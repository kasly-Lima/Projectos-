/* BusinessXP — utilitários globais: CSRF, toast seguro, notificações e Oráculo. */
(function () {
  'use strict';
  var meta = document.querySelector('meta[name="csrf-token"]');
  var CSRF = meta ? meta.content : '';

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /** fetch com CSRF + cookie de sessão. */
  function api(url, opts) {
    opts = opts || {};
    opts.credentials = 'same-origin';
    opts.headers = Object.assign({ 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': CSRF }, opts.headers || {});
    return fetch(url, opts);
  }

  /** Garante o token em todo <form method="post"> (rede de segurança). */
  function injectCsrf() {
    document.querySelectorAll('form').forEach(function (f) {
      if ((f.getAttribute('method') || '').toLowerCase() !== 'post' || f.querySelector('input[name="csrf_token"]')) return;
      var i = document.createElement('input');
      i.type = 'hidden'; i.name = 'csrf_token'; i.value = CSRF;
      f.appendChild(i);
    });
  }

  /** Toast montado com DOM (sem innerHTML): textos do servidor nunca viram HTML. */
  function showToast(n) {
    var box = document.getElementById('toast-container');
    if (!box) return;
    var t = document.createElement('div');
    t.className = 'toast'; t.setAttribute('role', 'status');
    var ic = document.createElement('span'); ic.className = 'toast-icon'; ic.textContent = n.icone || '🔔';
    var body = document.createElement('div');
    var ti = document.createElement('div'); ti.className = 'toast-title'; ti.textContent = n.titulo || '';
    body.appendChild(ti);
    if (n.mensagem) { var m = document.createElement('div'); m.className = 'toast-body'; m.textContent = n.mensagem; body.appendChild(m); }
    t.appendChild(ic); t.appendChild(body);
    var link = n.link && /^\/[^/\\]/.test(n.link) ? n.link : '';
    t.addEventListener('click', function () { if (link) location.href = link; else t.remove(); });
    box.appendChild(t);
    setTimeout(function () { t.remove(); }, 6500);
  }

  /* ── Notificações ── */
  var lastId = 0, primeira = true;
  function pollNotifs() {
    if (document.hidden) return;
    api('/api/notifications').then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
      if (!d) return;
      var b = document.getElementById('notif-badge');
      if (b) { b.textContent = d.total > 99 ? '99+' : d.total; b.style.display = d.total ? 'block' : 'none'; }
      var novas = d.notifications.filter(function (n) { return n.id > lastId; }).reverse();
      if (primeira) novas = novas.slice(-3);   // ao abrir o site, só as 3 mais recentes viram toast
      novas.forEach(function (n) { showToast(n); });
      d.notifications.forEach(function (n) { if (n.id > lastId) lastId = n.id; });
      primeira = false;
    }).catch(function () {});
  }

  /* ── Oráculo ── */
  var orHist = [];
  function orAdd(role, text) {
    var msgs = document.getElementById('or-msgs');
    var row = document.createElement('div'); row.className = 'or-msg ' + role;
    var av = document.createElement('span'); av.textContent = role === 'bot' ? '🔮' : '🧑';
    var b = document.createElement('div'); b.className = 'or-bubble';
    // texto puro; só **negrito** e quebras de linha são interpretados, depois de escapar
    b.innerHTML = esc(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
    row.appendChild(av); row.appendChild(b); msgs.appendChild(row);
    msgs.scrollTop = msgs.scrollHeight;
    return row;
  }
  function orSend() {
    var inp = document.getElementById('or-input'), btn = document.getElementById('or-send');
    var text = inp.value.trim();
    if (!text || btn.disabled) return;
    inp.value = ''; inp.style.height = 'auto'; btn.disabled = true;
    orAdd('user', text);
    var typing = document.createElement('div'); typing.className = 'or-msg bot or-typing';
    typing.innerHTML = '<span></span><span></span><span></span>';
    document.getElementById('or-msgs').appendChild(typing);
    api('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: orHist.slice(-10) }) })
      .then(function (r) { return r.json().catch(function () { return { reply: 'Resposta inválida do servidor.' }; }); })
      .then(function (d) { typing.remove(); orAdd('bot', d.reply || '...'); orHist.push({ role: 'user', text: text }, { role: 'model', text: d.reply || '' }); })
      .catch(function () { typing.remove(); orAdd('bot', 'Sem conexão com o servidor.'); })
      .then(function () { btn.disabled = false; inp.focus(); });
  }
  function initOraculo() {
    var btn = document.getElementById('oraculo-btn'), w = document.getElementById('oraculo-widget');
    if (!btn || !w) return;
    var open = false;
    function toggle(v) {
      open = v == null ? !open : v;
      w.classList.toggle('open', open); btn.setAttribute('aria-expanded', String(open));
      if (open) { if (!document.querySelector('#or-msgs .or-msg')) orAdd('bot', 'Olá! Sou o **Oráculo**. Pergunte sobre missões, XP, ponto, loja ou conquistas.'); document.getElementById('or-input').focus(); }
    }
    btn.addEventListener('click', function () { toggle(); });
    document.getElementById('or-close').addEventListener('click', function () { toggle(false); });
    document.getElementById('or-send').addEventListener('click', orSend);
    var inp = document.getElementById('or-input');
    inp.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); orSend(); } });
    inp.addEventListener('input', function () { inp.style.height = 'auto'; inp.style.height = Math.min(inp.scrollHeight, 90) + 'px'; });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && open) toggle(false); });
  }

  window.BXP = { csrf: CSRF, esc: esc, api: api };
  window.showToast = showToast;

  document.addEventListener('DOMContentLoaded', function () {
    injectCsrf();
    initOraculo();
    if (document.body.dataset.auth === '1') {
      pollNotifs();
      setInterval(pollNotifs, 8000);
      document.addEventListener('visibilitychange', function () { if (!document.hidden) pollNotifs(); });
    }
  });
})();
