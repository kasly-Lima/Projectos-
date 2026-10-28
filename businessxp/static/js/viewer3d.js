/**
 * BusinessXP — visualizador 3D (Three.js r128 + GLTFLoader + OrbitControls).
 * Uso:  const v = new BusinessXpViewer(canvasOuId, { autoRotate: true });
 *       v.loadModel(url, { rotacaoY: 90 });
 * O canvas deve estar dentro de um .viewer-stage com .v-loading, .v-error e .v-progress.
 * O loop só roda quando o canvas está visível e a aba está ativa.
 */
class BusinessXpViewer {
  constructor(canvasOrId, opts = {}) {
    this.canvas = typeof canvasOrId === 'string' ? document.getElementById(canvasOrId) : canvasOrId;
    this.stage = this.canvas.closest('.viewer-stage') || this.canvas.parentElement;
    this.opts = Object.assign({ autoRotate: true, rotateSpeed: 1.4, fov: 38, cameraY: 0.9, cameraZ: 4.3, targetY: -0.05, floorY: -1, altura: 2.0 }, opts);
    this._model = null; this._mixer = null; this._loadId = 0;
    this._visible = true; this._destroyed = false; this._raf = 0; this._clock = null;
    this._wire = false;
    if (!window.THREE) { this._showError('Three.js não carregou. Verifique sua conexão.'); return; }
    try { this._setup(); } catch (e) { console.error(e); this._showError('Este navegador não conseguiu iniciar o 3D (WebGL).'); return; }
    this._observe();
    this._maybeRun();
  }

  /* ── cena ── */
  _setup() {
    const T = THREE, o = this.opts;
    this.renderer = new T.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.outputEncoding = T.sRGBEncoding;
    this.renderer.toneMapping = T.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.scene = new T.Scene();
    this.camera = new T.PerspectiveCamera(o.fov, 1, 0.05, 60);
    this.camera.position.set(0, o.cameraY, o.cameraZ);
    this._buildEnvironment();

    this.scene.add(new T.HemisphereLight(0x9fd8ff, 0x1a0828, 0.45));
    const key = new T.DirectionalLight(0xfff2e0, 1.0); key.position.set(3, 5, 4); this.scene.add(key);
    const rim = new T.DirectionalLight(0xff2e97, 1.1); rim.position.set(-4, 3, -3); this.scene.add(rim);
    const cyan = new T.DirectionalLight(0x19f0ff, 0.7); cyan.position.set(4, 1, -3); this.scene.add(cyan);
    this._glow = new T.PointLight(0x19f0ff, 0.8, 7); this._glow.position.set(0, o.floorY + 0.3, 1.4); this.scene.add(this._glow);

    // plataforma: disco escuro + anéis neon + grade
    const fy = o.floorY;
    const disc = new T.Mesh(new T.CircleGeometry(1.45, 72), new T.MeshBasicMaterial({ color: 0x070b18, transparent: true, opacity: 0.85 }));
    disc.rotation.x = -Math.PI / 2; disc.position.y = fy - 0.005; this.scene.add(disc);
    const ring = (r0, r1, color, op) => {
      const m = new T.Mesh(new T.RingGeometry(r0, r1, 96), new T.MeshBasicMaterial({ color, transparent: true, opacity: op, side: T.DoubleSide }));
      m.rotation.x = -Math.PI / 2; m.position.y = fy; this.scene.add(m); return m;
    };
    this._ringA = ring(1.30, 1.34, 0x19f0ff, 0.9);
    ring(1.46, 1.48, 0xff2e97, 0.7);
    ring(0.60, 0.61, 0x19f0ff, 0.35);
    const grid = new T.GridHelper(4.2, 14, 0x19f0ff, 0x19f0ff);
    grid.position.y = fy - 0.004; grid.material.transparent = true; grid.material.opacity = 0.10; this.scene.add(grid);

    // anel de varredura que sobe e desce pelo personagem
    this._scan = new T.Mesh(new T.TorusGeometry(1.12, 0.012, 8, 128),
      new T.MeshBasicMaterial({ color: 0x19f0ff, transparent: true, opacity: 0.0, blending: T.AdditiveBlending, depthWrite: false }));
    this._scan.rotation.x = Math.PI / 2; this.scene.add(this._scan);

    // partículas
    const N = 90, pos = new Float32Array(N * 3), col = new Float32Array(N * 3), c1 = new T.Color(0x19f0ff), c2 = new T.Color(0xff2e97);
    for (let i = 0; i < N; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 5; pos[i * 3 + 1] = fy + Math.random() * 3.4; pos[i * 3 + 2] = (Math.random() - 0.5) * 5;
      const c = Math.random() < 0.7 ? c1 : c2; col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    }
    const pg = new T.BufferGeometry();
    pg.setAttribute('position', new T.BufferAttribute(pos, 3)); pg.setAttribute('color', new T.BufferAttribute(col, 3));
    this._particles = new T.Points(pg, new T.PointsMaterial({ size: 0.035, vertexColors: true, transparent: true, opacity: 0.55, depthWrite: false }));
    this.scene.add(this._particles);

    if (T.OrbitControls) {
      const c = this.controls = new T.OrbitControls(this.camera, this.canvas);
      c.target.set(0, o.targetY, 0);
      c.enableDamping = true; c.dampingFactor = 0.08; c.enablePan = false;
      c.autoRotate = o.autoRotate; c.autoRotateSpeed = o.rotateSpeed;
      c.minDistance = 1.8; c.maxDistance = 8; c.minPolarAngle = Math.PI * 0.18; c.maxPolarAngle = Math.PI * 0.52;
      c.update(); c.saveState();
    } else { this.camera.lookAt(0, o.targetY, 0); }
    this._clock = new T.Clock();
    this._resize();
  }

  /** Ambiente procedural (painéis de luz neon) para os metais refletirem algo. */
  _buildEnvironment() {
    try {
      const T = THREE, env = new T.Scene();
      env.add(new T.Mesh(new T.SphereGeometry(12, 32, 16), new T.ShaderMaterial({
        side: T.BackSide,
        vertexShader: 'varying vec3 vP;void main(){vP=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
        fragmentShader: 'varying vec3 vP;void main(){float h=normalize(vP).y*.5+.5;gl_FragColor=vec4(mix(vec3(.015,.02,.05),vec3(.09,.14,.28),h),1.);}'
      })));
      const panel = (hex, k, w, h, p) => {
        const m = new T.Mesh(new T.PlaneGeometry(w, h), new T.MeshBasicMaterial({ color: new T.Color(hex).multiplyScalar(k), side: T.DoubleSide }));
        m.position.set(p[0], p[1], p[2]); m.lookAt(0, 0, 0); env.add(m);
      };
      panel(0x19f0ff, 3.2, 7, 2.2, [-7, 3, 4]); panel(0xff2e97, 3.2, 7, 2.2, [7, 2, -4]);
      panel(0xffffff, 2.6, 6, 3, [0, 8, 2]); panel(0xf5e642, 1.1, 4, 3, [0, -2, 7]);
      const pm = new T.PMREMGenerator(this.renderer);
      this.scene.environment = pm.fromScene(env, 0.03).texture;
      pm.dispose();
      env.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); });
    } catch (e) { console.warn('Ambiente 3D indisponível:', e); }
  }

  /* ── carregamento ── */
  loadModel(url, o = {}) {
    if (!this.renderer) return;
    const id = ++this._loadId;
    this._showLoading(true); this._clearModel();
    if (!url) { this._showError('Nenhum personagem equipado.'); return; }
    if (!THREE.GLTFLoader) { this._showError('GLTFLoader não carregou. Verifique sua conexão.'); return; }
    const loader = this._loader || (this._loader = new THREE.GLTFLoader());
    if (THREE.DRACOLoader && !this._draco) {
      this._draco = new THREE.DRACOLoader();
      this._draco.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/libs/draco/gltf/');
      loader.setDRACOLoader(this._draco);
    }
    loader.load(url, (gltf) => {
      if (id !== this._loadId || this._destroyed) return;   // pedido antigo, ignora
      try { this._place(gltf, o); } catch (e) { console.error(e); this._showError('Modelo carregado, mas inválido.'); return; }
      this._showLoading(false);
      let tris = 0;
      this._model.traverse(m => { if (m.isMesh && m.geometry) tris += (m.geometry.index ? m.geometry.index.count : m.geometry.attributes.position.count) / 3; });
      this.canvas.dispatchEvent(new CustomEvent('viewer:loaded', { detail: { arquivo: url.split('?')[0].split('/').pop(), triangulos: Math.round(tris) } }));
    }, (xhr) => {
      if (id !== this._loadId) return;
      const el = this.stage.querySelector('.v-progress');
      if (el && xhr.total) el.textContent = 'Carregando… ' + Math.round(xhr.loaded / xhr.total * 100) + '%';
    }, (err) => {
      if (id !== this._loadId) return;
      const nome = url.split('?')[0].split('/').pop();
      const nf = /404|not found/i.test(String(err && err.message));
      this._showError(nf ? ['Arquivo não encontrado', nome, 'Coloque o .glb na pasta static/models correta.']
                         : ['Falha ao ler o modelo', nome, String((err && err.message) || '').slice(0, 120)]);
      this.canvas.dispatchEvent(new CustomEvent('viewer:error', { detail: { url } }));
    });
  }

  _place(gltf, o) {
    const T = THREE, model = gltf.scene;
    model.updateMatrixWorld(true);
    const box = new T.Box3().setFromObject(model), size = box.getSize(new T.Vector3()), center = box.getCenter(new T.Vector3());
    const maior = Math.max(size.x, size.y, size.z);
    if (!isFinite(maior) || maior <= 0) throw new Error('bounding box inválido');
    const aniso = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
    model.traverse(m => {
      if (!m.isMesh) return;
      m.frustumCulled = false;
      (Array.isArray(m.material) ? m.material : [m.material]).forEach(mt => {
        if (!mt) return;
        mt.envMapIntensity = 1.15; mt.wireframe = this._wire;
        ['map', 'normalMap', 'metalnessMap', 'roughnessMap', 'emissiveMap', 'aoMap'].forEach(k => { if (mt[k]) mt[k].anisotropy = aniso; });
      });
    });
    model.position.set(-center.x, -box.min.y, -center.z);        // pés na origem, centrado
    const holder = new T.Group(); holder.add(model);
    holder.scale.setScalar(this.opts.altura / maior);
    holder.position.y = this.opts.floorY;
    holder.rotation.y = T.MathUtils.degToRad(Number(o.rotacaoY) || 0);
    this.scene.add(holder);
    this._model = holder;
    if (gltf.animations && gltf.animations.length) {
      this._mixer = new T.AnimationMixer(model);
      const idle = gltf.animations.find(a => /idle|stand|parad/i.test(a.name)) || gltf.animations[0];
      this._mixer.clipAction(idle).play();
    }
    this._scanTop = this.opts.floorY + (size.y * this.opts.altura / maior);
  }

  _clearModel() {
    if (this._mixer) { this._mixer.stopAllAction(); this._mixer = null; }
    if (!this._model) return;
    this.scene.remove(this._model);
    this._model.traverse(m => {
      if (m.geometry) m.geometry.dispose();
      (Array.isArray(m.material) ? m.material : [m.material]).forEach(mt => {
        if (!mt) return;
        Object.keys(mt).forEach(k => { if (mt[k] && mt[k].isTexture) mt[k].dispose(); });
        mt.dispose();
      });
    });
    this._model = null; this._scanTop = null;
  }

  /* ── controles públicos ── */
  setAutoRotate(on) { if (this.controls) this.controls.autoRotate = !!on; }
  setWireframe(on) {
    this._wire = !!on;
    if (!this._model) return;
    this._model.traverse(m => { if (m.isMesh && m.material) (Array.isArray(m.material) ? m.material : [m.material]).forEach(x => { x.wireframe = this._wire; }); });
  }
  resetCamera() {
    if (!this.camera) return;
    if (this.controls) this.controls.reset();
    else { this.camera.position.set(0, this.opts.cameraY, this.opts.cameraZ); this.camera.lookAt(0, this.opts.targetY, 0); }
  }
  pause() { this._paused = true; this._maybeRun(); }
  resume() { this._paused = false; this._resize(); this._maybeRun(); }

  /* ── loop e visibilidade ── */
  _observe() {
    if ('IntersectionObserver' in window) {
      this._io = new IntersectionObserver(es => { this._visible = es[0].isIntersecting; this._maybeRun(); });
      this._io.observe(this.canvas);
    }
    if ('ResizeObserver' in window) { this._ro = new ResizeObserver(() => this._resize()); this._ro.observe(this.canvas); }
    else window.addEventListener('resize', this._onResize = () => this._resize());
    this._onVis = () => this._maybeRun();
    document.addEventListener('visibilitychange', this._onVis);
  }
  _maybeRun() {
    const deve = !this._destroyed && !this._paused && this._visible && !document.hidden && this.renderer;
    if (deve && !this._raf) { this._clock.getDelta(); this._tick(); }
    else if (!deve && this._raf) { cancelAnimationFrame(this._raf); this._raf = 0; }
  }
  _tick() {
    this._raf = requestAnimationFrame(() => this._tick());
    const dt = this._clock.getDelta(), t = this._clock.elapsedTime;
    if (this._mixer) this._mixer.update(dt);
    if (this.controls) this.controls.update();
    this._glow.intensity = 0.7 + Math.sin(t * 2.2) * 0.25;
    this._ringA.material.opacity = 0.65 + Math.sin(t * 2.2) * 0.3;
    this._particles.rotation.y = t * 0.05;
    const p = this._particles.geometry.attributes.position;
    for (let i = 0; i < p.count; i++) { let y = p.getY(i) + dt * 0.12; if (y > this.opts.floorY + 3.4) y = this.opts.floorY; p.setY(i, y); }
    p.needsUpdate = true;
    if (this._scanTop != null) {
      const k = (t % 4.5) / 4.5, h = this._scanTop - this.opts.floorY;
      this._scan.position.y = this.opts.floorY + h * k;
      this._scan.material.opacity = Math.sin(k * Math.PI) * 0.55;
    } else this._scan.material.opacity = 0;
    this.renderer.render(this.scene, this.camera);
  }
  _resize() {
    if (!this.renderer) return;
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h; this.camera.updateProjectionMatrix();
  }

  /* ── overlays ── */
  _showLoading(on) {
    const l = this.stage.querySelector('.v-loading'), e = this.stage.querySelector('.v-error'), p = this.stage.querySelector('.v-progress');
    if (l) l.style.display = on ? 'flex' : 'none';
    if (e) e.style.display = 'none';
    if (p && on) p.textContent = 'Invocando…';
  }
  _showError(msg) {
    const l = this.stage.querySelector('.v-loading'), e = this.stage.querySelector('.v-error');
    if (l) l.style.display = 'none';
    if (!e) return;
    e.textContent = '';
    (Array.isArray(msg) ? msg : [msg]).forEach((linha, i) => {
      const el = document.createElement(i === 0 ? 'strong' : 'div'); el.textContent = linha; e.appendChild(el);
    });
    e.style.display = 'flex';
  }

  destroy() {
    this._destroyed = true; this._maybeRun();
    if (this._io) this._io.disconnect(); if (this._ro) this._ro.disconnect();
    if (this._onResize) window.removeEventListener('resize', this._onResize);
    if (this._onVis) document.removeEventListener('visibilitychange', this._onVis);
    this._clearModel(); if (this.controls) this.controls.dispose();
    if (this.renderer) this.renderer.dispose();
  }
}
window.BusinessXpViewer = BusinessXpViewer;
