import html
import json
import logging
import mimetypes
import os
import re
import secrets
import smtplib
import sqlite3
import ssl
import time
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

from flask import (Flask, flash, g, jsonify, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
os.makedirs(app.instance_path, exist_ok=True)
mimetypes.add_type('model/gltf-binary', '.glb')
mimetypes.add_type('model/gltf+json', '.gltf')
logging.basicConfig(level=logging.INFO)


def _secret_key():
    """SECRET_KEY do ambiente ou uma chave persistida em instance/ (não muda a cada reinício)."""
    k = os.environ.get('SECRET_KEY')
    if k:
        return k
    caminho = os.path.join(app.instance_path, 'secret_key')
    if os.path.exists(caminho):
        with open(caminho) as f:
            return f.read().strip()
    k = secrets.token_hex(32)
    with open(caminho, 'w') as f:
        f.write(k)
    try:
        os.chmod(caminho, 0o600)
    except OSError:
        pass
    return k


app.secret_key = _secret_key()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == '1',
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    MAX_CONTENT_LENGTH=1024 * 1024,
)
app.jinja_env.globals['enumerate'] = enumerate

DATABASE = os.path.join(app.instance_path, 'Businessxp.db')
TZ = timezone(timedelta(hours=float(os.environ.get('TZ_OFFSET_HOURS', '-3'))))


def agora():
    return datetime.now(TZ)


# ── Filtros / globals de template ──────────────────────────────────────────────
@app.template_filter('from_json')
def from_json_filter(s):
    try:
        v = json.loads(s or '[]')
        return v if isinstance(v, list) else []
    except Exception:
        return []


@app.template_filter('localdt')
def localdt_filter(s, fmt='%d/%m/%Y %H:%M'):
    """Converte 'YYYY-MM-DD HH:MM:SS' (UTC, padrão do SQLite) para o fuso configurado."""
    try:
        dt = datetime.fromisoformat(str(s).replace('T', ' ')[:19]).replace(tzinfo=timezone.utc)
        return dt.astimezone(TZ).strftime(fmt)
    except Exception:
        return s or ''


def csrf_token():
    if '_csrf' not in session:
        session['_csrf'] = secrets.token_urlsafe(32)
    return session['_csrf']


app.jinja_env.globals['csrf_token'] = csrf_token

# ── Dados estáticos ────────────────────────────────────────────────────────────
RACAS = [
    ('humano',    '🧑', 'Humano',    'Versátil e adaptável'),
    ('elfo',      '🧝', 'Elfo',      'Ágil e inteligente'),
    ('anao',      '🧔', 'Anão',      'Resistente e forte'),
    ('orc',       '💪', 'Orc',       'Força bruta máxima'),
    ('gnomo',     '🧪', 'Gnomo',     'Inventivo e técnico'),
    ('draconato', '🐉', 'Draconato', 'Poder arcano e físico'),
]
CLASSES = [
    ('Analista de Redes', '🌐'),
    ('Suporte N1',        '🖥️'),
    ('Suporte N2',        '⚡'),
    ('Administrador',     '👑'),
    ('Dev Técnico',       '💻'),
    ('Arcano',            '🔮'),
]
RARIDADES = ('comum', 'raro', 'epico', 'lendario')
PRECO_PADRAO = {'comum': 300, 'raro': 600, 'epico': 900, 'lendario': 1500}

# Modelos 3D: o que estiver nestas pastas aparece sozinho no sistema.
MODELS_DIR = os.path.join(BASE_DIR, 'static', 'models')
PASTAS_MODELOS = {'inicial': 'iniciais', 'loja': 'loja'}
EXT_MODELOS = ('.glb', '.gltf')

PERIODOS_PONTO = ['entrada', 'saida_almoco', 'retorno', 'saida']
PERIODOS_LABEL = {'entrada': 'Entrada', 'saida_almoco': 'Saída Almoço',
                  'retorno': 'Retorno Almoço', 'saida': 'Saída'}
MOEDAS_POR_PONTO = 5
MAX_VALOR = 100000


# ── Banco ──────────────────────────────────────────────────────────────────────
def connect():
    db = sqlite3.connect(DATABASE, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=15000')
    try:
        db.execute('PRAGMA journal_mode=WAL')
    except sqlite3.DatabaseError:
        pass
    return db


def get_db():
    if 'db' not in g:
        g.db = connect()
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def add_column(db, tabela, coluna, ddl):
    cols = {r['name'] for r in db.execute(f'PRAGMA table_info({tabela})').fetchall()}
    if coluna not in cols:
        db.execute(f'ALTER TABLE {tabela} ADD COLUMN {coluna} {ddl}')


SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL, role TEXT DEFAULT 'user', raca TEXT DEFAULT 'humano',
    classe TEXT DEFAULT 'Suporte N1', nivel INTEGER DEFAULT 1, xp INTEGER DEFAULT 0,
    moedas INTEGER DEFAULT 100, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, arquivo TEXT UNIQUE NOT NULL,
    categoria TEXT DEFAULT 'inicial', preco INTEGER DEFAULT 0, descricao TEXT DEFAULT '',
    raridade TEXT DEFAULT 'comum', icone TEXT DEFAULT '⚔️', ativo INTEGER DEFAULT 1,
    rotacao_y REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS user_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, model_id INTEGER NOT NULL,
    equipado INTEGER DEFAULT 0, adquirido_em TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, model_id),
    FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(model_id) REFERENCES models(id));
CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, descricao TEXT DEFAULT '',
    categoria TEXT DEFAULT 'task', xp_reward INTEGER DEFAULT 50, moedas_reward INTEGER DEFAULT 10,
    assigned_to INTEGER, created_by INTEGER, status TEXT DEFAULT 'pendente',
    xp_dado INTEGER DEFAULT 0, moedas_dadas INTEGER DEFAULT 0, feedback_gestor TEXT DEFAULT '',
    deadline TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')), completed_at TEXT DEFAULT '',
    FOREIGN KEY(assigned_to) REFERENCES users(id), FOREIGN KEY(created_by) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS registros_ponto (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
    data TEXT DEFAULT (date('now')), timestamp TEXT DEFAULT (datetime('now')),
    tipo TEXT DEFAULT 'entrada', validado INTEGER DEFAULT 0, validado_por INTEGER,
    xp_bonus INTEGER DEFAULT 0, moedas_bonus INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(validado_por) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS pontos_diarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
    timestamp TEXT DEFAULT (datetime('now','localtime')), data TEXT DEFAULT (date('now','localtime')),
    periodo TEXT NOT NULL, UNIQUE(user_id, data, periodo),
    FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, tipo TEXT NOT NULL,
    titulo TEXT NOT NULL, mensagem TEXT DEFAULT '', lida INTEGER DEFAULT 0, icone TEXT DEFAULT '🔔',
    link TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE NOT NULL, titulo TEXT NOT NULL,
    descricao TEXT DEFAULT '', icone TEXT DEFAULT '🏆', categoria TEXT DEFAULT 'especial',
    threshold INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, achievement_id INTEGER NOT NULL,
    earned_at TEXT DEFAULT (datetime('now')), UNIQUE(user_id, achievement_id),
    FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(achievement_id) REFERENCES achievements(id));
CREATE TABLE IF NOT EXISTS invites (
    id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT UNIQUE NOT NULL, email TEXT NOT NULL,
    role TEXT DEFAULT 'user', used INTEGER DEFAULT 0, created_by INTEGER,
    created_at TEXT DEFAULT (datetime('now')), FOREIGN KEY(created_by) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, question TEXT NOT NULL,
    category TEXT DEFAULT 'Geral', xp_reward INTEGER DEFAULT 100, gold_reward INTEGER DEFAULT 20,
    alternativas TEXT DEFAULT '[]', resposta_correta TEXT DEFAULT '0', created_by INTEGER,
    created_at TEXT DEFAULT (datetime('now')), FOREIGN KEY(created_by) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS challenge_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT, challenge_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
    answer TEXT NOT NULL, score INTEGER DEFAULT 0, reviewed INTEGER DEFAULT 1,
    submitted_at TEXT DEFAULT (datetime('now')), UNIQUE(challenge_id, user_id),
    FOREIGN KEY(challenge_id) REFERENCES challenges(id), FOREIGN KEY(user_id) REFERENCES users(id));
'''

CONQUISTAS = [
    ('missoes_5',   'Iniciante',        'Completou 5 missões',                '📜', 'missoes',  5),
    ('missoes_25',  'Veterano',         'Completou 25 missões',               '⚔️', 'missoes', 25),
    ('missoes_50',  'Lenda do Suporte', 'Completou 50 missões',               '🎯', 'missoes', 50),
    ('moedas_500',  'Tesoureiro',       'Acumulou 500 moedas',                '💰', 'moedas',  500),
    ('moedas_2000', 'Magnata',          'Acumulou 2000 moedas',               '🏦', 'moedas', 2000),
    ('nivel_5',     'Experiente',       'Atingiu nível 5',                    '⭐', 'nivel',    5),
    ('nivel_10',    'Mestre',           'Atingiu nível 10',                   '🌟', 'nivel',   10),
    ('ponto_7',     'Pontual Semanal',  '7 registros de ponto validados',     '⏰', 'ponto',    7),
    ('skin_3',      'Colecionador',     'Possui 3 personagens no inventário', '🎭', 'colecao',  3),
]


def nome_bonito(arquivo):
    base = os.path.splitext(arquivo)[0]
    return re.sub(r'[_\-]+', ' ', base).strip().title() or arquivo


def carregar_meta_modelos():
    """static/models/models.json: {"arquivo.glb": {"name","icone","descricao","preco","raridade","rotacao_y"}}"""
    caminho = os.path.join(MODELS_DIR, 'models.json')
    if not os.path.exists(caminho):
        return {}
    try:
        with open(caminho, encoding='utf-8') as f:
            dados = json.load(f)
        return {k: v for k, v in dados.items() if isinstance(v, dict) and not k.startswith('_')}
    except Exception as e:
        app.logger.error('models.json inválido: %s', e)
        return {}


def sync_models(db):
    """Registra no banco todo .glb/.gltf encontrado nas pastas e desativa os que sumiram."""
    meta = carregar_meta_modelos()
    presentes = []
    for categoria, pasta in PASTAS_MODELOS.items():
        d = os.path.join(MODELS_DIR, pasta)
        os.makedirs(d, exist_ok=True)
        for arq in sorted(os.listdir(d)):
            if not arq.lower().endswith(EXT_MODELOS):
                continue
            tamanho = os.path.getsize(os.path.join(d, arq))
            if tamanho > 15 * 1024 * 1024:
                app.logger.warning('%s tem %.0f MB — rode "python otimizar_modelos.py" para reduzir.',
                                   arq, tamanho / 1e6)
            m = meta.get(arq, {})
            raridade = m.get('raridade') if m.get('raridade') in RARIDADES else None
            row = db.execute('SELECT * FROM models WHERE arquivo=?', (arq,)).fetchone()
            if row is None:
                raridade = raridade or 'comum'
                preco = 0 if categoria == 'inicial' else to_int(m.get('preco'), PRECO_PADRAO[raridade], 0, MAX_VALOR)
                db.execute('INSERT INTO models (name,arquivo,categoria,preco,descricao,raridade,icone,ativo,rotacao_y) '
                           'VALUES (?,?,?,?,?,?,?,1,?)',
                           (m.get('name') or nome_bonito(arq), arq, categoria, preco, m.get('descricao', ''),
                            raridade, m.get('icone') or '⚔️', float(m.get('rotacao_y', 0) or 0)))
            else:
                if row['categoria'] != categoria:
                    pasta_antiga = os.path.join(MODELS_DIR, PASTAS_MODELOS.get(row['categoria'], ''), arq)
                    if os.path.exists(pasta_antiga):
                        app.logger.warning('%s existe em iniciais e loja; mantido em %s.', arq, row['categoria'])
                        continue
                    db.execute('UPDATE models SET categoria=? WHERE id=?', (categoria, row['id']))
                campos = {}
                for k_json, col in (('name', 'name'), ('icone', 'icone'), ('descricao', 'descricao')):
                    if m.get(k_json) is not None:
                        campos[col] = m[k_json]
                if raridade:
                    campos['raridade'] = raridade
                if 'preco' in m and categoria == 'loja':
                    campos['preco'] = to_int(m['preco'], row['preco'], 0, MAX_VALOR)
                if 'rotacao_y' in m:
                    campos['rotacao_y'] = float(m['rotacao_y'] or 0)
                if categoria == 'inicial':
                    campos['preco'] = 0
                campos['ativo'] = 1
                sets = ','.join(f'{c}=?' for c in campos)
                db.execute(f'UPDATE models SET {sets} WHERE id=?', (*campos.values(), row['id']))
            presentes.append(arq)
    if presentes:
        marcas = ','.join('?' * len(presentes))
        db.execute(f'UPDATE models SET ativo=CASE WHEN arquivo IN ({marcas}) THEN 1 ELSE 0 END', presentes)
    else:
        db.execute('UPDATE models SET ativo=0')
    # o admin recebe todos os modelos ativos (ótimo para testar)
    adm = db.execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()
    if adm:
        for m in db.execute('SELECT id FROM models WHERE ativo=1').fetchall():
            db.execute('INSERT OR IGNORE INTO user_models (user_id,model_id,equipado) VALUES (?,?,0)', (adm['id'], m['id']))
        if not db.execute('SELECT 1 FROM user_models um JOIN models m ON m.id=um.model_id '
                          'WHERE um.user_id=? AND um.equipado=1 AND m.ativo=1', (adm['id'],)).fetchone():
            prim = db.execute("SELECT um.id FROM user_models um JOIN models m ON m.id=um.model_id "
                              "WHERE um.user_id=? AND m.ativo=1 ORDER BY (m.categoria='inicial') DESC, um.id LIMIT 1",
                              (adm['id'],)).fetchone()
            if prim:
                db.execute('UPDATE user_models SET equipado=0 WHERE user_id=?', (adm['id'],))
                db.execute('UPDATE user_models SET equipado=1 WHERE id=?', (prim['id'],))
    db.commit()


def init_db():
    db = connect()
    db.executescript(SCHEMA)
    # migrações de bancos antigos
    add_column(db, 'models', 'ativo', 'INTEGER DEFAULT 1')
    add_column(db, 'models', 'rotacao_y', 'REAL DEFAULT 0')
    add_column(db, 'challenges', 'alternativas', "TEXT DEFAULT '[]'")
    add_column(db, 'challenges', 'resposta_correta', "TEXT DEFAULT '0'")
    add_column(db, 'challenges', 'assigned_to', 'INTEGER')
    add_column(db, 'missions', 'confirmado_usuario', 'INTEGER DEFAULT 0')
    add_column(db, 'missions', 'feedback_usuario', "TEXT DEFAULT ''")
    for a in CONQUISTAS:
        db.execute('INSERT OR IGNORE INTO achievements (key,titulo,descricao,icone,categoria,threshold) VALUES (?,?,?,?,?,?)', a)
    if not db.execute("SELECT id FROM users WHERE role='admin'").fetchone():
        email = os.environ.get('ADMIN_EMAIL', 'admin@businessxp.com').strip().lower()
        senha = os.environ.get('ADMIN_PASSWORD') or secrets.token_urlsafe(9)
        db.execute('INSERT INTO users (username,email,password,role,moedas,nivel,xp) VALUES (?,?,?,?,?,?,?)',
                   ('Admin', email, generate_password_hash(senha), 'admin', 99999, 99, 0))
        db.commit()
        print('\n' + '=' * 60)
        print(' ADMIN CRIADO  ->  e-mail: %s   senha: %s' % (email, senha))
        print(' (defina ADMIN_EMAIL / ADMIN_PASSWORD no .env para escolher)')
        print('=' * 60 + '\n')
    db.commit()
    sync_models(db)
    db.close()


# ── Utilidades ─────────────────────────────────────────────────────────────────
def to_int(valor, padrao=0, minimo=None, maximo=None):
    try:
        n = int(str(valor).strip())
    except (TypeError, ValueError):
        n = padrao
    if minimo is not None:
        n = max(minimo, n)
    if maximo is not None:
        n = min(maximo, n)
    return n


_hits = {}


def hit_count(chave, janela):
    agora_t = time.time()
    fila = [t for t in _hits.get(chave, []) if agora_t - t < janela]
    _hits[chave] = fila
    return len(fila)


def add_hit(chave):
    _hits.setdefault(chave, []).append(time.time())


def model_dict(row):
    d = dict(row)
    pasta = PASTAS_MODELOS.get(d.get('categoria'), 'loja')
    caminho = os.path.join(MODELS_DIR, pasta, d['arquivo'])
    try:
        v, tam = int(os.path.getmtime(caminho)), os.path.getsize(caminho)
    except OSError:
        v, tam = 0, 0
    d['caminho'] = url_for('static', filename=f'models/{pasta}/{d["arquivo"]}') + f'?v={v}'
    d['tamanho_mb'] = round(tam / 1e6, 1)
    d['rotacao_y'] = d.get('rotacao_y') or 0
    return d


def get_user(uid):
    return get_db().execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()


def get_equipped_model(uid):
    db = get_db()
    r = db.execute('SELECT m.* FROM user_models um JOIN models m ON um.model_id=m.id '
                   'WHERE um.user_id=? AND um.equipado=1 AND m.ativo=1 LIMIT 1', (uid,)).fetchone()
    if r is None:  # nada equipado (ou arquivo sumiu): equipa o primeiro disponível
        r = db.execute('SELECT m.*, um.id AS um_id FROM user_models um JOIN models m ON um.model_id=m.id '
                       'WHERE um.user_id=? AND m.ativo=1 ORDER BY um.adquirido_em LIMIT 1', (uid,)).fetchone()
        if r is not None:
            db.execute('UPDATE user_models SET equipado=0 WHERE user_id=?', (uid,))
            db.execute('UPDATE user_models SET equipado=1 WHERE id=?', (r['um_id'],))
            db.commit()
        else:  # não possui nenhum modelo ativo (ex.: arquivos trocados): ganha um inicial grátis
            r = db.execute("SELECT * FROM models WHERE categoria='inicial' AND ativo=1 ORDER BY id LIMIT 1").fetchone()
            if r is not None:
                db.execute('UPDATE user_models SET equipado=0 WHERE user_id=?', (uid,))
                db.execute('INSERT OR IGNORE INTO user_models (user_id,model_id,equipado) VALUES (?,?,1)', (uid, r['id']))
                db.commit()
    return r


def get_inventory(uid):
    rows = get_db().execute(
        'SELECT m.*,um.equipado,um.adquirido_em FROM user_models um JOIN models m ON um.model_id=m.id '
        'WHERE um.user_id=? AND m.ativo=1 ORDER BY um.adquirido_em DESC', (uid,)).fetchall()
    return [model_dict(r) for r in rows]


def xp_para_nivel(n):
    return n * 1000


def check_level_up(uid):
    db = get_db()
    u = db.execute('SELECT nivel,xp FROM users WHERE id=?', (uid,)).fetchone()
    if u:
        n, xp = u['nivel'], u['xp']
        while xp >= xp_para_nivel(n):
            xp -= xp_para_nivel(n)
            n += 1
        db.execute('UPDATE users SET nivel=?,xp=? WHERE id=?', (n, xp, uid))
        db.commit()
    check_achievements(uid)


def check_achievements(uid):
    db = get_db()
    u = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    if not u:
        return
    m_done = db.execute("SELECT COUNT(*) c FROM missions WHERE assigned_to=? AND status='encerrada'", (uid,)).fetchone()['c']
    p_val = db.execute('SELECT COUNT(*) c FROM registros_ponto WHERE user_id=? AND validado=1', (uid,)).fetchone()['c']
    skins = db.execute('SELECT COUNT(*) c FROM user_models WHERE user_id=?', (uid,)).fetchone()['c']
    regras = [('missoes_5', m_done >= 5), ('missoes_25', m_done >= 25), ('missoes_50', m_done >= 50),
              ('moedas_500', u['moedas'] >= 500), ('moedas_2000', u['moedas'] >= 2000),
              ('nivel_5', u['nivel'] >= 5), ('nivel_10', u['nivel'] >= 10),
              ('ponto_7', p_val >= 7), ('skin_3', skins >= 3)]
    for key, ok in regras:
        if not ok:
            continue
        ach = db.execute('SELECT id,titulo,icone FROM achievements WHERE key=?', (key,)).fetchone()
        if ach:
            r = db.execute('INSERT OR IGNORE INTO user_achievements (user_id,achievement_id) VALUES (?,?)', (uid, ach['id']))
            if r.rowcount:
                db.execute('INSERT INTO notifications (user_id,tipo,titulo,mensagem,icone,link) VALUES (?,?,?,?,?,?)',
                           (uid, 'conquista', f'Conquista: {ach["titulo"]}', 'Nova proeza desbloqueada!', ach['icone'], '/conquistas'))
    db.commit()


def notif(uid, tipo, titulo, msg='', icone='🔔', link=''):
    db = get_db()
    db.execute('INSERT INTO notifications (user_id,tipo,titulo,mensagem,icone,link) VALUES (?,?,?,?,?,?)',
               (uid, tipo, titulo, msg, icone, link))
    db.commit()


def notificar_gestores(tipo, titulo, msg, icone, link):
    db = get_db()
    for gst in db.execute("SELECT id FROM users WHERE role IN ('admin','gestor')").fetchall():
        db.execute('INSERT INTO notifications (user_id,tipo,titulo,mensagem,icone,link) VALUES (?,?,?,?,?,?)',
                   (gst['id'], tipo, titulo, msg, icone, link))


# ── Decorators / hooks ─────────────────────────────────────────────────────────
def wants_json():
    return (request.path.startswith('/api/') or request.is_json
            or request.headers.get('X-Requested-With') == 'XMLHttpRequest')


@app.before_request
def carregar_usuario_e_csrf():
    g.user = None
    if request.endpoint == 'static':
        return
    uid = session.get('user_id')
    if uid:
        u = get_db().execute('SELECT id,username,role FROM users WHERE id=?', (uid,)).fetchone()
        if u:
            g.user = u
            session['role'], session['username'] = u['role'], u['username']  # cargo sempre atual
        else:
            session.clear()
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        enviado = request.form.get('csrf_token') or request.headers.get('X-CSRFToken') or ''
        esperado = session.get('_csrf', '')
        if not esperado or not secrets.compare_digest(enviado, esperado):
            if wants_json():
                return jsonify({'status': 'erro', 'mensagem': 'Sessão expirada. Recarregue a página.'}), 400
            flash('Sessão expirada. Tente novamente.', 'error')
            return redirect(url_for('perfil') if g.user else url_for('login'))


@app.after_request
def cabecalhos(resp):
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resp.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    resp.headers.setdefault('Referrer-Policy', 'same-origin')
    return resp


def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if not g.get('user'):
            if wants_json():
                return jsonify({'status': 'erro', 'mensagem': 'Faça login.'}), 401
            return redirect(url_for('login'))
        return f(*a, **kw)
    return dec


def manager_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if g.user['role'] not in ('admin', 'gestor'):
            flash('Acesso negado.', 'error')
            return redirect(url_for('perfil'))
        return f(*a, **kw)
    return dec


def admin_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if g.user['role'] != 'admin':
            flash('Apenas Admin.', 'error')
            return redirect(url_for('perfil'))
        return f(*a, **kw)
    return dec


# ── E-mail de convite ──────────────────────────────────────────────────────────
def link_convite(token):
    base = os.environ.get('BASE_URL', '').rstrip('/')
    if base:
        return base + url_for('register', token=token)
    return url_for('register', token=token, _external=True)


def enviar_email_convite(email_destino, token, role):
    remetente = os.environ.get('EMAIL_REMETENTE', '')
    senha = os.environ.get('EMAIL_SENHA', '')
    host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    porta = to_int(os.environ.get('EMAIL_PORT'), 465)
    if not remetente or not senha:
        return False
    link = html.escape(link_convite(token), quote=True)
    cargo = 'Gestor' if role == 'gestor' else 'Guerreiro'
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '⚔️ Seu convite para BusinessXP'
    msg['From'], msg['To'] = remetente, email_destino
    corpo = f'''<html><body style="font-family:Arial,sans-serif;background:#06070f;color:#dbe6ff;padding:30px;">
<div style="max-width:500px;margin:0 auto;background:#0b0f1f;border:1px solid #19f0ff;padding:32px;">
<h1 style="color:#19f0ff;text-align:center;">BUSINESS XP</h1>
<p>Você foi convidado como <strong style="color:#f5e642;">{cargo}</strong>.</p>
<div style="text-align:center;margin:28px 0;"><a href="{link}" style="background:#19f0ff;color:#000;font-weight:700;
text-decoration:none;padding:14px 32px;display:inline-block;">ENTRAR NO REINO</a></div>
<p style="font-size:12px;color:#93a1c4;text-align:center;">Convite para: {html.escape(email_destino)}</p></div></body></html>'''
    msg.attach(MIMEText(f'Acesse: {link_convite(token)}', 'plain', 'utf-8'))
    msg.attach(MIMEText(corpo, 'html', 'utf-8'))
    try:
        with smtplib.SMTP_SSL(host, porta, context=ssl.create_default_context(), timeout=15) as s:
            s.login(remetente, senha)
            s.sendmail(remetente, email_destino, msg.as_string())
        return True
    except Exception as e:
        app.logger.error('Erro e-mail: %s', e)
        return False


# ── AUTH ───────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('perfil') if g.user else url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('perfil'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        chave = f'login:{request.remote_addr}:{email}'
        if hit_count(chave, 300) >= 8:
            flash('Muitas tentativas. Aguarde alguns minutos e tente de novo.', 'error')
            return render_template('login.html')
        u = get_db().execute('SELECT * FROM users WHERE lower(email)=?', (email,)).fetchone()
        if u and check_password_hash(u['password'], request.form.get('password', '')):
            _hits.pop(chave, None)
            session.clear()
            session.permanent = True
            session.update(user_id=u['id'], username=u['username'], role=u['role'])
            return redirect(url_for('perfil'))
        add_hit(chave)
        flash('E-mail ou senha inválidos.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/register/<token>', methods=['GET', 'POST'])
def register(token):
    db = get_db()
    inv = db.execute('SELECT * FROM invites WHERE token=? AND used=0', (token,)).fetchone()
    if not inv:
        flash('Convite inválido ou já utilizado.', 'error')
        return redirect(url_for('login'))
    modelos = [model_dict(r) for r in db.execute(
        "SELECT * FROM models WHERE categoria='inicial' AND ativo=1 ORDER BY id").fetchall()]

    def pagina(erro=None):
        return render_template('register.html', token=token, invite=inv, modelos=modelos,
                               racas=RACAS, classes=CLASSES, error=erro)

    if request.method == 'POST':
        f = request.form
        username = f.get('username', '').strip()
        password = f.get('password', '')
        raca = f.get('raca') if f.get('raca') in {r[0] for r in RACAS} else 'humano'
        classe = f.get('classe') if f.get('classe') in {c[0] for c in CLASSES} else 'Suporte N1'
        if not 3 <= len(username) <= 30:
            return pagina('O nome de usuário deve ter entre 3 e 30 caracteres.')
        if len(password) < 8:
            return pagina('A senha deve ter ao menos 8 caracteres.')
        mid = to_int(f.get('model_id'), 0)
        escolhido = next((m for m in modelos if m['id'] == mid), modelos[0] if modelos else None)
        try:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('UPDATE invites SET used=1 WHERE token=? AND used=0', (token,)).rowcount != 1:
                db.rollback()
                flash('Convite inválido ou já utilizado.', 'error')
                return redirect(url_for('login'))
            cur = db.execute('INSERT INTO users (username,email,password,role,raca,classe) VALUES (?,?,?,?,?,?)',
                             (username, inv['email'].lower(), generate_password_hash(password), inv['role'], raca, classe))
            uid = cur.lastrowid
            if escolhido:
                db.execute('INSERT INTO user_models (user_id,model_id,equipado) VALUES (?,?,1)', (uid, escolhido['id']))
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            return pagina('Esse nome de usuário ou e-mail já está em uso.')
        except Exception:
            db.rollback()
            app.logger.exception('Falha no cadastro')
            return pagina('Não foi possível criar a conta. Tente novamente.')
        session.clear()
        session.permanent = True
        session.update(user_id=uid, username=username, role=inv['role'])
        flash('Bem-vindo ao reino!', 'success')
        return redirect(url_for('perfil'))
    return pagina()


# ── PERFIL ─────────────────────────────────────────────────────────────────────
@app.route('/perfil')
@login_required
def perfil():
    uid = g.user['id']
    u = get_user(uid)
    inv = get_inventory(uid)
    db = get_db()
    m_pend = db.execute("SELECT m.*,u.username criador FROM missions m LEFT JOIN users u ON m.created_by=u.id "
                        "WHERE m.assigned_to=? AND m.status='pendente' ORDER BY m.created_at DESC", (uid,)).fetchall()
    m_env = db.execute("SELECT * FROM missions WHERE assigned_to=? AND status='aguardando_validacao' "
                       "ORDER BY created_at DESC", (uid,)).fetchall()
    m_enc = db.execute("SELECT * FROM missions WHERE assigned_to=? AND status='encerrada' "
                       "ORDER BY completed_at DESC LIMIT 10", (uid,)).fetchall()
    achs = db.execute('SELECT a.*,CASE WHEN ua.id IS NOT NULL THEN 1 ELSE 0 END earned FROM achievements a '
                      'LEFT JOIN user_achievements ua ON a.id=ua.achievement_id AND ua.user_id=? '
                      'ORDER BY earned DESC,a.id', (uid,)).fetchall()
    needed = xp_para_nivel(u['nivel'])
    return render_template('perfil.html', u=u, inv=inv, m_pend=m_pend, m_env=m_env, m_enc=m_enc, achs=achs,
                           earned_achs=sum(1 for a in achs if a['earned']), total_achs=len(achs),
                           needed_xp=needed, xp_pct=min(int(u['xp'] / needed * 100), 100),
                           racas={r[0]: r for r in RACAS})


@app.route('/api/perfil')
@login_required
def api_perfil():
    uid = g.user['id']
    eq = get_equipped_model(uid)
    if not eq:
        return jsonify({'equipado': None})
    d = model_dict(eq)
    u = get_user(uid)
    return jsonify({'equipado': {'nome': d['name'], 'arquivo': d['arquivo'], 'caminho': d['caminho'],
                                 'icone': d['icone'], 'rotacao_y': d['rotacao_y'], 'tamanho_mb': d['tamanho_mb']},
                    'usuario': {'nivel': u['nivel'], 'xp': u['xp'], 'moedas': u['moedas']}})


@app.route('/inventario/equipar/<int:model_id>', methods=['POST'])
@login_required
def equipar(model_id):
    uid = g.user['id']
    db = get_db()
    if db.execute('SELECT um.id FROM user_models um JOIN models m ON m.id=um.model_id '
                  'WHERE um.user_id=? AND um.model_id=? AND m.ativo=1', (uid, model_id)).fetchone():
        db.execute('UPDATE user_models SET equipado=0 WHERE user_id=?', (uid,))
        db.execute('UPDATE user_models SET equipado=1 WHERE user_id=? AND model_id=?', (uid, model_id))
        db.commit()
        flash('Personagem equipado!', 'success')
    return redirect(url_for('perfil'))


# ── MISSÕES ────────────────────────────────────────────────────────────────────
@app.route('/missoes/confirmar/<int:mid>', methods=['POST'])
@login_required
def confirmar_missao(mid):
    """Etapa 1 — o usuário confirma que executou a missão."""
    uid = g.user['id']
    feedback = request.form.get('feedback_usuario', '').strip()[:1000]
    db = get_db()
    m = db.execute("SELECT * FROM missions WHERE id=? AND assigned_to=? AND status='pendente'", (mid, uid)).fetchone()
    if m:
        db.execute("UPDATE missions SET status='aguardando_validacao',confirmado_usuario=1,feedback_usuario=? WHERE id=?",
                   (feedback, mid))
        notificar_gestores('missao', f'{g.user["username"]} concluiu: {m["titulo"]}',
                           feedback or 'Missão marcada como executada pelo guerreiro.', '📜', '/gestor')
        db.commit()
        flash('Missão marcada como concluída! Aguardando validação do gestor.', 'success')
    return redirect(url_for('perfil'))


@app.route('/missoes/enviar/<int:mid>', methods=['POST'])
@login_required
def enviar_missao(mid):
    return confirmar_missao(mid)


# ── PONTO ──────────────────────────────────────────────────────────────────────
def _ponto_de_hoje(db, uid):
    data = agora().strftime('%Y-%m-%d')
    rows = db.execute('SELECT periodo,timestamp FROM pontos_diarios WHERE user_id=? AND data=?', (uid, data)).fetchall()
    return data, {r['periodo']: r['timestamp'][11:16] for r in rows}


@app.route('/api/ponto/status')
@login_required
def ponto_status():
    _, feitos = _ponto_de_hoje(get_db(), g.user['id'])
    slots = [{'periodo': p, 'label': PERIODOS_LABEL[p], 'feito': p in feitos, 'hora': feitos.get(p, '--:--')}
             for p in PERIODOS_PONTO]
    proximo = next((p for p in PERIODOS_PONTO if p not in feitos), None)
    return jsonify({'slots': slots, 'total': len(feitos), 'proximo': proximo, 'completo': proximo is None})


@app.route('/ponto/bater', methods=['POST'])
@login_required
def bater_ponto():
    uid = g.user['id']
    pedido = request.form.get('periodo', '').strip()
    ajax = wants_json()

    def resp(status, msg, code=200):
        if ajax:
            return jsonify({'status': status, 'mensagem': msg}), code
        flash(msg, 'success' if status == 'ok' else 'error')
        return redirect(url_for('perfil'))

    db = get_db()
    data, feitos = _ponto_de_hoje(db, uid)
    proximo = next((p for p in PERIODOS_PONTO if p not in feitos), None)
    if proximo is None:
        return resp('duplicado', 'Sua jornada de hoje já está completa.', 409)
    if pedido and pedido != proximo:  # o servidor decide a ordem
        return resp('erro', f'Sequência inválida. O próximo registro é: {PERIODOS_LABEL[proximo]}.', 409)
    ts = agora().strftime('%Y-%m-%d %H:%M:%S')
    try:
        db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO pontos_diarios (user_id,timestamp,data,periodo) VALUES (?,?,?,?)', (uid, ts, data, proximo))
        db.execute('INSERT INTO registros_ponto (user_id,data,timestamp,tipo) VALUES (?,?,?,?)', (uid, data, ts, proximo))
        db.execute('UPDATE users SET moedas=moedas+? WHERE id=?', (MOEDAS_POR_PONTO, uid))
        notificar_gestores('ponto', f'{g.user["username"]} — {PERIODOS_LABEL[proximo]}', 'Clique para validar', '⏰', '/gestor/ponto')
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return resp('duplicado', 'Ponto já registrado para este período hoje.', 409)
    except Exception:
        db.rollback()
        app.logger.exception('Falha ao registrar ponto')
        return resp('erro', 'Não foi possível registrar o ponto. Tente novamente.', 500)
    return resp('ok', f'{PERIODOS_LABEL[proximo]} registrada! +{MOEDAS_POR_PONTO} moedas')


# ── NOTIFICAÇÕES ───────────────────────────────────────────────────────────────
@app.route('/api/notifications')
@login_required
def api_notifications():
    uid = g.user['id']
    db = get_db()
    ns = db.execute('SELECT * FROM notifications WHERE user_id=? AND lida=0 ORDER BY id DESC LIMIT 20', (uid,)).fetchall()
    total = db.execute('SELECT COUNT(*) c FROM notifications WHERE user_id=? AND lida=0', (uid,)).fetchone()['c']
    return jsonify({'total': total, 'notifications': [dict(n) for n in ns]})


@app.route('/api/notifications/mark_read', methods=['POST'])
@login_required
def mark_read():
    uid = g.user['id']
    nid = (request.get_json(silent=True) or {}).get('id')
    db = get_db()
    if nid:
        db.execute('UPDATE notifications SET lida=1 WHERE id=? AND user_id=?', (to_int(nid), uid))
    else:
        db.execute('UPDATE notifications SET lida=1 WHERE user_id=?', (uid,))
    db.commit()
    return jsonify({'ok': True})


@app.route('/notificacoes')
@login_required
def notificacoes():
    uid = g.user['id']
    db = get_db()
    ns = db.execute('SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 60', (uid,)).fetchall()
    db.execute('UPDATE notifications SET lida=1 WHERE user_id=?', (uid,))
    db.commit()
    return render_template('notificacoes.html', notificacoes=ns)


# ── LOJA ───────────────────────────────────────────────────────────────────────
@app.route('/loja')
@login_required
def loja():
    uid = g.user['id']
    db = get_db()
    itens = [model_dict(r) for r in db.execute(
        "SELECT * FROM models WHERE categoria='loja' AND ativo=1 ORDER BY preco, name").fetchall()]
    owned = {r['model_id'] for r in db.execute('SELECT model_id FROM user_models WHERE user_id=?', (uid,)).fetchall()}
    return render_template('loja.html', itens=itens, owned_ids=owned, moedas=get_user(uid)['moedas'])


@app.route('/loja/comprar/<int:model_id>', methods=['POST'])
@login_required
def comprar(model_id):
    uid = g.user['id']
    db = get_db()
    item = db.execute("SELECT * FROM models WHERE id=? AND categoria='loja' AND ativo=1", (model_id,)).fetchone()
    if not item:
        flash('Item não encontrado.', 'error')
        return redirect(url_for('loja'))
    try:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM user_models WHERE user_id=? AND model_id=?', (uid, model_id)).fetchone():
            db.rollback()
            flash('Você já possui este personagem.', 'error')
            return redirect(url_for('loja'))
        if db.execute('UPDATE users SET moedas=moedas-? WHERE id=? AND moedas>=?', (item['preco'], uid, item['preco'])).rowcount != 1:
            db.rollback()
            flash('Moedas insuficientes!', 'error')
            return redirect(url_for('loja'))
        db.execute('INSERT INTO user_models (user_id,model_id,equipado) VALUES (?,?,0)', (uid, model_id))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        flash('Você já possui este personagem.', 'error')
        return redirect(url_for('loja'))
    flash(f'{item["name"]} adquirido! Equipe no perfil.', 'success')
    notif(uid, 'compra', f'Novo personagem: {item["name"]}', 'Acesse o inventário!', item['icone'], '/perfil')
    check_achievements(uid)
    return redirect(url_for('loja'))


# ── CONQUISTAS / RANKING ───────────────────────────────────────────────────────
@app.route('/conquistas')
@login_required
def conquistas():
    uid = g.user['id']
    check_achievements(uid)
    achs = get_db().execute('SELECT a.*,CASE WHEN ua.id IS NOT NULL THEN 1 ELSE 0 END earned,ua.earned_at FROM achievements a '
                            'LEFT JOIN user_achievements ua ON a.id=ua.achievement_id AND ua.user_id=? '
                            'ORDER BY earned DESC,a.id', (uid,)).fetchall()
    return render_template('conquistas.html', achs=achs)


@app.route('/ranking')
@login_required
def ranking():
    players = get_db().execute('''
        SELECT u.id,u.username,u.raca,u.classe,u.nivel,u.xp,u.moedas,
               (SELECT COUNT(*) FROM missions WHERE assigned_to=u.id AND status='encerrada') missoes,
               (SELECT COUNT(*) FROM user_achievements WHERE user_id=u.id) conquistas,
               (SELECT m.icone FROM user_models um JOIN models m ON um.model_id=m.id
                 WHERE um.user_id=u.id AND um.equipado=1 AND m.ativo=1 LIMIT 1) skin_icone
        FROM users u WHERE u.role IN ('user','gestor') ORDER BY u.nivel DESC,u.xp DESC''').fetchall()
    return render_template('ranking.html', players=players, racas={r[0]: r for r in RACAS})


# ── GESTOR ─────────────────────────────────────────────────────────────────────
@app.route('/gestor')
@login_required
@manager_required
def gestor():
    db = get_db()
    usuarios = db.execute("SELECT id,username,nivel,xp,moedas,raca,classe FROM users "
                          "WHERE role IN ('user','gestor') ORDER BY username").fetchall()
    m_env = db.execute("SELECT m.*,u.username guerreiro FROM missions m JOIN users u ON m.assigned_to=u.id "
                       "WHERE m.status IN ('enviada','aguardando_validacao') ORDER BY m.created_at DESC").fetchall()
    m_enc = db.execute("SELECT m.*,u.username guerreiro FROM missions m JOIN users u ON m.assigned_to=u.id "
                       "WHERE m.status='encerrada' ORDER BY m.completed_at DESC LIMIT 20").fetchall()
    return render_template('gestor.html', usuarios=usuarios, m_env=m_env, m_enc=m_enc)


def _guerreiro_valido(db, uid):
    return db.execute("SELECT id,username FROM users WHERE id=? AND role IN ('user','gestor')", (uid,)).fetchone()


@app.route('/gestor/missao/criar', methods=['POST'])
@login_required
@manager_required
def criar_missao():
    f = request.form
    db = get_db()
    alvo = _guerreiro_valido(db, to_int(f.get('assigned_to')))
    titulo = f.get('titulo', '').strip()
    if not alvo or not titulo:
        flash('Informe o título e o guerreiro.', 'error')
        return redirect(url_for('gestor'))
    categoria = f.get('categoria') if f.get('categoria') in ('task', 'inventory', 'physical', 'guild') else 'task'
    xp, mc = to_int(f.get('xp_reward'), 50, 0, MAX_VALOR), to_int(f.get('moedas_reward'), 10, 0, MAX_VALOR)
    db.execute('INSERT INTO missions (titulo,descricao,categoria,xp_reward,moedas_reward,assigned_to,created_by,deadline) '
               'VALUES (?,?,?,?,?,?,?,?)',
               (titulo[:120], f.get('descricao', '').strip()[:1000], categoria, xp, mc, alvo['id'], g.user['id'],
                f.get('deadline', '')[:10]))
    db.commit()
    notif(alvo['id'], 'nova_missao', f'Nova missão: {titulo[:120]}', f'+{xp} XP ao completar', '⚔️', '/perfil')
    flash('Missão criada!', 'success')
    return redirect(url_for('gestor'))


@app.route('/gestor/missao/avaliar/<int:mid>', methods=['POST'])
@login_required
@manager_required
def avaliar_missao(mid):
    """Etapa 2 — o gestor valida (aprova ou devolve) a missão concluída."""
    xp = to_int(request.form.get('xp_dado'), 0, 0, MAX_VALOR)
    mc = to_int(request.form.get('moedas_dadas'), 0, 0, MAX_VALOR)
    fb = request.form.get('feedback', '').strip()[:500]
    acao = request.form.get('acao', 'aprovar')
    db = get_db()
    m = db.execute("SELECT * FROM missions WHERE id=? AND status IN ('enviada','aguardando_validacao')", (mid,)).fetchone()
    if not m:
        return redirect(url_for('gestor'))
    if m['assigned_to'] == g.user['id'] and g.user['role'] != 'admin':
        flash('Você não pode validar uma missão atribuída a você mesmo.', 'error')
        return redirect(url_for('gestor'))
    if acao == 'rejeitar':
        db.execute("UPDATE missions SET status='pendente',feedback_gestor=?,confirmado_usuario=0 WHERE id=?",
                   (f'[REJEITADA] {fb}', mid))
        db.commit()
        notif(m['assigned_to'], 'missao_rejeitada', f'Missão devolvida: {m["titulo"]}',
              fb or 'O gestor solicitou que a missão seja refeita.', '↩️', '/perfil')
        flash('Missão devolvida ao guerreiro para correção.', 'success')
    else:
        if db.execute("UPDATE missions SET status='encerrada',xp_dado=?,moedas_dadas=?,feedback_gestor=?,"
                      "completed_at=datetime('now') WHERE id=? AND status IN ('enviada','aguardando_validacao')",
                      (xp, mc, fb, mid)).rowcount == 1:
            db.execute('UPDATE users SET xp=xp+?,moedas=moedas+? WHERE id=?', (xp, mc, m['assigned_to']))
            db.commit()
            check_level_up(m['assigned_to'])
            notif(m['assigned_to'], 'missao_validada', f'Missão validada: {m["titulo"]}',
                  f'+{xp} XP e +{mc} moedas — {fb}' if fb else f'+{xp} XP e +{mc} moedas', '✅', '/perfil')
            flash(f'Missão validada! +{xp} XP e +{mc} moedas concedidos.', 'success')
    return redirect(url_for('gestor'))


@app.route('/gestor/award/<int:uid>', methods=['POST'])
@login_required
@manager_required
def award(uid):
    xp = to_int(request.form.get('xp'), 0, 0, MAX_VALOR)
    mc = to_int(request.form.get('moedas'), 0, 0, MAX_VALOR)
    db = get_db()
    if not _guerreiro_valido(db, uid):
        flash('Guerreiro não encontrado.', 'error')
    elif uid == g.user['id'] and g.user['role'] != 'admin':
        flash('Você não pode dar recompensas a si mesmo.', 'error')
    elif xp or mc:
        db.execute('UPDATE users SET xp=xp+?,moedas=moedas+? WHERE id=?', (xp, mc, uid))
        db.commit()
        check_level_up(uid)
        notif(uid, 'bonus', 'Recompensa recebida!', f'+{xp} XP e +{mc} moedas', '🎁', '/perfil')
        flash(f'+{xp} XP e +{mc} moedas concedidos!', 'success')
    return redirect(url_for('gestor'))


@app.route('/gestor/ponto')
@login_required
@manager_required
def gestor_ponto():
    regs = get_db().execute('SELECT rp.*,u.username FROM registros_ponto rp JOIN users u ON rp.user_id=u.id '
                            'ORDER BY rp.timestamp DESC LIMIT 100').fetchall()
    return render_template('gestor_ponto.html', registros=regs, labels=PERIODOS_LABEL)


@app.route('/gestor/ponto/validar/<int:pid>', methods=['POST'])
@login_required
@manager_required
def validar_ponto(pid):
    xp_b = to_int(request.form.get('xp_bonus'), 25, 0, MAX_VALOR)
    mc_b = to_int(request.form.get('moedas_bonus'), 5, 0, MAX_VALOR)
    db = get_db()
    rp = db.execute('SELECT * FROM registros_ponto WHERE id=? AND validado=0', (pid,)).fetchone()
    if rp:
        if rp['user_id'] == g.user['id'] and g.user['role'] != 'admin':
            flash('Você não pode validar o seu próprio ponto.', 'error')
            return redirect(url_for('gestor_ponto'))
        db.execute('UPDATE registros_ponto SET validado=1,validado_por=?,xp_bonus=?,moedas_bonus=? WHERE id=?',
                   (g.user['id'], xp_b, mc_b, pid))
        db.execute('UPDATE users SET xp=xp+?,moedas=moedas+? WHERE id=?', (xp_b, mc_b, rp['user_id']))
        db.commit()
        check_level_up(rp['user_id'])
        notif(rp['user_id'], 'ponto', 'Ponto validado!', f'+{xp_b} XP e +{mc_b} moedas de bônus!', '⏰', '/perfil')
        flash('Ponto validado!', 'success')
    return redirect(url_for('gestor_ponto'))


# ── ADMIN ──────────────────────────────────────────────────────────────────────
@app.route('/admin')
@login_required
@admin_required
def admin():
    db = get_db()
    usuarios = db.execute("SELECT u.*,(SELECT COUNT(*) FROM user_models WHERE user_id=u.id) skins FROM users u "
                          "WHERE u.role!='admin' ORDER BY u.role,u.username").fetchall()
    invites = db.execute('SELECT i.*,u.username criador FROM invites i LEFT JOIN users u ON i.created_by=u.id '
                         'ORDER BY i.created_at DESC LIMIT 20').fetchall()
    return render_template('admin.html', usuarios=usuarios,
                           invites=[dict(i, link=link_convite(i['token'])) for i in invites])


@app.route('/admin/invite', methods=['POST'])
@login_required
@admin_required
def criar_invite():
    email = request.form.get('email', '').strip().lower()
    role = request.form.get('role', 'user')
    if role not in ('user', 'gestor'):
        role = 'user'
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        flash('Informe um e-mail válido.', 'error')
        return redirect(url_for('admin'))
    db = get_db()
    if db.execute('SELECT 1 FROM users WHERE lower(email)=?', (email,)).fetchone():
        flash('Já existe um usuário com esse e-mail.', 'error')
        return redirect(url_for('admin'))
    token = secrets.token_urlsafe(24)
    db.execute('INSERT INTO invites (token,email,role,created_by) VALUES (?,?,?,?)', (token, email, role, g.user['id']))
    db.commit()
    if enviar_email_convite(email, token, role):
        flash(f'Convite enviado por e-mail para {email} ({role}).', 'success')
    else:
        flash(f'Convite criado. O envio automático não está configurado; copie o link na lista abaixo.', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/delete/<int:uid>', methods=['POST'])
@login_required
@admin_required
def deletar(uid):
    db = get_db()
    alvo = db.execute('SELECT id,role FROM users WHERE id=?', (uid,)).fetchone()
    if not alvo or alvo['role'] == 'admin':
        flash('Usuário não pode ser removido.', 'error')
        return redirect(url_for('admin'))
    try:
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM challenge_answers WHERE user_id=? OR challenge_id IN '
                   '(SELECT id FROM challenges WHERE assigned_to=?)', (uid, uid))
        db.execute('DELETE FROM challenges WHERE assigned_to=?', (uid,))
        for tabela in ('user_models', 'user_achievements', 'notifications', 'registros_ponto', 'pontos_diarios'):
            db.execute(f'DELETE FROM {tabela} WHERE user_id=?', (uid,))
        db.execute('DELETE FROM missions WHERE assigned_to=?', (uid,))
        for tabela, col in (('missions', 'created_by'), ('challenges', 'created_by'),
                            ('invites', 'created_by'), ('registros_ponto', 'validado_por')):
            db.execute(f'UPDATE {tabela} SET {col}=NULL WHERE {col}=?', (uid,))
        db.execute('DELETE FROM users WHERE id=?', (uid,))
        db.commit()
        flash('Usuário removido.', 'success')
    except Exception:
        db.rollback()
        app.logger.exception('Falha ao remover usuário')
        flash('Não foi possível remover o usuário.', 'error')
    return redirect(url_for('admin'))


@app.route('/admin/role/<int:uid>', methods=['POST'])
@login_required
@admin_required
def mudar_role(uid):
    role = request.form.get('role', 'user')
    if role not in ('user', 'gestor'):
        role = 'user'
    db = get_db()
    db.execute("UPDATE users SET role=? WHERE id=? AND role!='admin'", (role, uid))
    db.commit()
    flash('Cargo atualizado!', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/modelos/sincronizar', methods=['POST'])
@login_required
@admin_required
def sincronizar_modelos():
    sync_models(get_db())
    flash('Modelos 3D sincronizados com as pastas.', 'success')
    return redirect(url_for('admin'))


# ── Exercícios ─────────────────────────────────────────────────────────────────
@app.route('/exercicios')
@login_required
def exercicios():
    uid = g.user['id']
    db = get_db()
    chs = db.execute('SELECT * FROM challenges WHERE assigned_to=? ORDER BY created_at DESC', (uid,)).fetchall()
    respostas = {r['challenge_id']: dict(r) for r in
                 db.execute('SELECT * FROM challenge_answers WHERE user_id=?', (uid,)).fetchall()}
    return render_template('exercicios.html', challenges=chs, respondidos=set(respostas), respostas=respostas)


@app.route('/exercicios/responder/<int:cid>', methods=['POST'])
@login_required
def responder_challenge(cid):
    uid = g.user['id']
    db = get_db()
    ch = db.execute('SELECT * FROM challenges WHERE id=? AND assigned_to=?', (cid, uid)).fetchone()
    if not ch:
        flash('Exercício não encontrado.', 'error')
        return redirect(url_for('exercicios'))
    alts = from_json_filter(ch['alternativas'])
    resp = to_int(request.form.get('resposta'), -1)
    if not 0 <= resp < len(alts):
        flash('Selecione uma alternativa válida.', 'error')
        return redirect(url_for('exercicios'))
    acertou = str(resp) == str(ch['resposta_correta'])
    xp, ouro = (ch['xp_reward'], ch['gold_reward']) if acertou else (0, 0)
    try:
        db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO challenge_answers (challenge_id,user_id,answer,score,reviewed) VALUES (?,?,?,?,1)',
                   (cid, uid, str(resp), 10 if acertou else 0))
        if xp or ouro:
            db.execute('UPDATE users SET xp=xp+?,moedas=moedas+? WHERE id=?', (xp, ouro, uid))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        flash('Você já respondeu este exercício.', 'error')
        return redirect(url_for('exercicios'))
    check_level_up(uid)
    flash(f'Correto! +{xp} XP +{ouro} moedas' if acertou else 'Resposta incorreta. Continue!',
          'success' if acertou else 'error')
    return redirect(url_for('exercicios'))


@app.route('/gestor/challenge', methods=['POST'])
@login_required
@manager_required
def criar_challenge():
    f = request.form
    titulo, pergunta = f.get('titulo', '').strip(), f.get('question', '').strip()
    db = get_db()
    alvo = _guerreiro_valido(db, to_int(f.get('assigned_to')))
    # alternativas: aceita qualquer sequência de índices (o JS pode remover linhas) e remapeia a correta
    pares = sorted((int(m.group(1)), v.strip()) for k, v in f.items()
                   if (m := re.fullmatch(r'alternativa_(\d+)', k)) and v.strip())
    pares = pares[:6]
    alternativas = [v[:300] for _, v in pares]
    correta_orig = to_int(f.get('resposta_correta'), -1)
    correta = next((pos for pos, (idx, _) in enumerate(pares) if idx == correta_orig), None)
    if not titulo or not pergunta:
        flash('Informe o título e a pergunta.', 'error')
    elif not alvo:
        flash('Selecione o guerreiro para este exercício.', 'error')
    elif len(alternativas) < 2:
        flash('Adicione ao menos 2 alternativas.', 'error')
    elif correta is None:
        flash('Marque qual alternativa é a correta.', 'error')
    else:
        categoria = f.get('category') if f.get('category') in ('Redes', 'Active Directory', 'Workspace', 'Office 365', 'Geral') else 'Geral'
        xp, ouro = to_int(f.get('xp_reward'), 100, 0, MAX_VALOR), to_int(f.get('gold_reward'), 20, 0, MAX_VALOR)
        db.execute('INSERT INTO challenges (title,question,category,xp_reward,gold_reward,assigned_to,created_by,'
                   'alternativas,resposta_correta) VALUES (?,?,?,?,?,?,?,?,?)',
                   (titulo[:120], pergunta[:2000], categoria, xp, ouro, alvo['id'], g.user['id'],
                    json.dumps(alternativas, ensure_ascii=False), str(correta)))
        db.commit()
        notif(alvo['id'], 'exercicio', f'Novo exercício: {titulo[:120]}', f'+{xp} XP se correto!', '💡', '/exercicios')
        flash('Exercício criado e atribuído!', 'success')
    return redirect(url_for('gestor'))


# ── Oráculo (Gemini) ───────────────────────────────────────────────────────────
GEMINI_SYSTEM = ("Você é o Oráculo de BusinessXP, assistente do sistema BusinessXP. Responda em português. "
                 "Ajude com dúvidas sobre o sistema: missões, XP, níveis, ponto, loja, conquistas e personagens. "
                 "Se a pergunta não for sobre o sistema, redirecione gentilmente. Respostas curtas e diretas.")


@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    uid = g.user['id']
    data = request.get_json(silent=True) or {}
    message = str(data.get('message') or '').strip()[:1500]
    if not message:
        return jsonify({'reply': 'Mensagem vazia.'}), 400
    chave = f'chat:{uid}'
    if hit_count(chave, 60) >= 12:
        return jsonify({'reply': 'O Oráculo precisa respirar. Tente de novo em instantes.'}), 429
    add_hit(chave)
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return jsonify({'reply': 'Configure GEMINI_API_KEY no arquivo .env para ativar o Oráculo.'})
    historico = []
    for m in (data.get('history') or [])[-10:]:
        if isinstance(m, dict) and isinstance(m.get('text'), str):
            historico.append({'role': 'user' if m.get('role') == 'user' else 'model', 'parts': [m['text'][:1500]]})
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash'), system_instruction=GEMINI_SYSTEM)
        chat = model.start_chat(history=historico)
        return jsonify({'reply': chat.send_message(message).text})
    except ImportError:
        return jsonify({'reply': 'Instale o pacote: pip install google-generativeai'})
    except Exception:
        app.logger.exception('Erro no Oráculo')
        return jsonify({'reply': 'O Oráculo está indisponível no momento.'}), 502


init_db()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1',
            host=os.environ.get('HOST', '0.0.0.0'), port=to_int(os.environ.get('PORT'), 5000))
