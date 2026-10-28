#!/usr/bin/env python3
"""
BusinessXP — otimizador de modelos .glb

Reduz o peso dos personagens 3D sem mexer na geometria: redimensiona as
texturas (padrão 1024 px) e recodifica em JPEG (ou PNG, quando há
transparência ou é mapa de normais). Um .glb de 40 MB costuma cair para 2–4 MB.

Uso (a partir da pasta do projeto):
    python otimizar_modelos.py                       # static/models/iniciais e loja
    python otimizar_modelos.py caminho/arquivo.glb   # um arquivo ou pasta
    python otimizar_modelos.py --max-tex 2048        # mais qualidade, arquivo maior
    python otimizar_modelos.py --dry-run             # só mostra o que faria

Os originais vão para ./modelos_originais/ (fora de static/, não são servidos).
Rodar de novo é seguro: arquivos já otimizados são pulados.
Requer: pip install pillow
"""
import argparse, io, json, os, shutil, struct, sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta o Pillow. Instale com:  pip install pillow")

MARCA = "businessxp_otimizado"
PADRAO = ["static/models/iniciais", "static/models/loja"]


def ler_glb(caminho):
    with open(caminho, "rb") as f:
        dados = f.read()
    magic, versao, _ = struct.unpack("<4sII", dados[:12])
    if magic != b"glTF" or versao != 2:
        raise ValueError("não é um .glb glTF 2.0")
    off, js, binario = 12, None, b""
    while off < len(dados):
        n, tipo = struct.unpack("<I4s", dados[off:off + 8])
        corpo = dados[off + 8:off + 8 + n]
        if tipo == b"JSON":
            js = json.loads(corpo.decode("utf-8").rstrip("\x00 "))
        elif tipo == b"BIN\x00":
            binario = corpo
        off += 8 + n
    if js is None:
        raise ValueError("chunk JSON ausente")
    return js, binario


def escrever_glb(caminho, js, binario):
    jb = json.dumps(js, separators=(",", ":")).encode("utf-8")
    jb += b" " * ((4 - len(jb) % 4) % 4)
    binario += b"\x00" * ((4 - len(binario) % 4) % 4)
    total = 12 + 8 + len(jb) + 8 + len(binario)
    with open(caminho, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<I4s", len(jb), b"JSON") + jb)
        f.write(struct.pack("<I4s", len(binario), b"BIN\x00") + binario)


def papeis_das_imagens(js):
    """Descobre para que cada imagem serve (cor, normal, etc.)."""
    papeis = {}
    texturas = js.get("textures", [])

    def marca(info, papel):
        if not isinstance(info, dict) or "index" not in info:
            return
        t = texturas[info["index"]]
        if "source" in t:
            papeis.setdefault(t["source"], set()).add(papel)

    for m in js.get("materials", []):
        p = m.get("pbrMetallicRoughness", {})
        marca(p.get("baseColorTexture"), "cor")
        marca(p.get("metallicRoughnessTexture"), "mr")
        marca(m.get("normalTexture"), "normal")
        marca(m.get("occlusionTexture"), "ao")
        marca(m.get("emissiveTexture"), "emissivo")
        for ext in m.get("extensions", {}).values():
            if isinstance(ext, dict):
                for v in ext.values():
                    marca(v, "outro")
    return papeis


def tem_alpha(img):
    if img.mode in ("RGBA", "LA"):
        return img.getchannel("A").getextrema()[0] < 255
    return img.mode == "P" and "transparency" in img.info


def recodificar(dados, papeis, max_tex, qualidade, normal_jpeg):
    img = Image.open(io.BytesIO(dados))
    formato = (img.format or "").upper()
    if formato not in ("PNG", "JPEG"):
        return None  # WebP/KTX2/etc.: não mexe
    img.load()
    w, h = img.size
    if max(w, h) > max_tex:
        k = max_tex / max(w, h)
        img = img.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
    alpha = tem_alpha(img)
    usar_png = alpha or ("normal" in papeis and not normal_jpeg) or "outro" in papeis
    saida = io.BytesIO()
    if usar_png:
        img.save(saida, "PNG", optimize=True)
        mime = "image/png"
    else:
        img.convert("RGB").save(saida, "JPEG", quality=qualidade, optimize=True, progressive=True,
                                subsampling=0 if ("normal" in papeis or "mr" in papeis) else 2)
        mime = "image/jpeg"
    novo = saida.getvalue()
    if len(novo) >= len(dados) and (w, h) == img.size and mime.endswith(formato.lower().replace("jpeg", "jpeg")):
        return None  # já estava menor
    return novo, mime


def otimizar(origem, destino, max_tex, qualidade, normal_jpeg):
    js, binario = ler_glb(origem)
    if js.get("asset", {}).get("extras", {}).get(MARCA):
        return None, "já otimizado"
    buffers = js.get("buffers", [])
    if len(buffers) != 1 or "uri" in buffers[0]:
        return None, "buffers externos não suportados"
    views = js.get("bufferViews", [])
    papeis = papeis_das_imagens(js)
    substituir = {}
    usados = {}
    for i, im in enumerate(js.get("images", [])):
        bv = im.get("bufferView")
        if bv is None:
            continue
        usados.setdefault(bv, []).append(i)
    for bv, imgs in usados.items():
        if len(imgs) != 1:
            continue
        i = imgs[0]
        v = views[bv]
        ini = v.get("byteOffset", 0)
        bruto = binario[ini:ini + v["byteLength"]]
        try:
            r = recodificar(bruto, papeis.get(i, set()), max_tex, qualidade, normal_jpeg)
        except Exception as e:  # imagem estranha: mantém a original
            print(f"    aviso: imagem {i} mantida ({e})")
            r = None
        if r:
            substituir[bv] = r

    novo_bin = bytearray()
    for idx, v in enumerate(views):
        ini = v.get("byteOffset", 0)
        corpo = binario[ini:ini + v["byteLength"]]
        if idx in substituir:
            corpo, mime = substituir[idx]
            js["images"][usados[idx][0]]["mimeType"] = mime
        novo_bin += b"\x00" * ((4 - len(novo_bin) % 4) % 4)
        v["byteOffset"] = len(novo_bin)
        v["byteLength"] = len(corpo)
        novo_bin += corpo
    buffers[0]["byteLength"] = len(novo_bin)
    js.setdefault("asset", {}).setdefault("extras", {})[MARCA] = {"max_tex": max_tex}
    escrever_glb(destino, js, bytes(novo_bin))
    return len(substituir), "ok"


def coletar(alvos):
    for alvo in alvos:
        if os.path.isdir(alvo):
            for nome in sorted(os.listdir(alvo)):
                if nome.lower().endswith(".glb"):
                    yield os.path.join(alvo, nome), alvo
        elif os.path.isfile(alvo):
            yield alvo, os.path.dirname(alvo) or "."
        else:
            print(f"  (ignorado, não existe: {alvo})")


def mb(n):
    return f"{n / 1e6:.1f} MB"


def main():
    ap = argparse.ArgumentParser(description="Otimiza texturas de arquivos .glb")
    ap.add_argument("alvos", nargs="*", default=PADRAO, help="arquivos ou pastas (padrão: static/models/...)")
    ap.add_argument("--max-tex", type=int, default=1024, help="lado máximo das texturas em px (padrão 1024)")
    ap.add_argument("--quality", type=int, default=86, help="qualidade JPEG 1-95 (padrão 86)")
    ap.add_argument("--normal-jpeg", action="store_true", help="usa JPEG também no mapa de normais (menor)")
    ap.add_argument("--backup-dir", default="modelos_originais", help="onde guardar os originais")
    ap.add_argument("--no-backup", action="store_true", help="não guarda os originais")
    ap.add_argument("--dry-run", action="store_true", help="só lista, não altera")
    a = ap.parse_args()

    total_antes = total_depois = 0
    for caminho, pasta in coletar(a.alvos):
        antes = os.path.getsize(caminho)
        print(f"- {caminho}  ({mb(antes)})")
        if a.dry_run:
            continue
        tmp = caminho + ".tmp"
        try:
            n, msg = otimizar(caminho, tmp, a.max_tex, a.quality, a.normal_jpeg)
        except Exception as e:
            print(f"    erro: {e}")
            if os.path.exists(tmp):
                os.remove(tmp)
            continue
        if n is None:
            print(f"    pulado: {msg}")
            continue
        depois = os.path.getsize(tmp)
        if depois >= antes:
            os.remove(tmp)
            print("    sem ganho, mantido o original")
            continue
        if not a.no_backup:
            dest = os.path.join(a.backup_dir, os.path.basename(pasta.rstrip("/\\")))
            os.makedirs(dest, exist_ok=True)
            shutil.copy2(caminho, os.path.join(dest, os.path.basename(caminho)))
        os.replace(tmp, caminho)
        total_antes += antes
        total_depois += depois
        print(f"    {mb(antes)} -> {mb(depois)}  ({n} textura(s) recodificada(s))")
    if total_antes:
        print(f"\nTotal: {mb(total_antes)} -> {mb(total_depois)}")


if __name__ == "__main__":
    main()
