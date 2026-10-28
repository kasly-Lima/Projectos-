/* Modal de pré-visualização 3D compartilhado (loja e cadastro).
   Qualquer elemento com data-preview="URL" data-title="Nome" [data-rot="90"] abre o modal. */
(function () {
  'use strict';
  var modal = document.getElementById('model-modal');
  if (!modal) return;
  var canvas = document.getElementById('modal-canvas'), titulo = document.getElementById('modal-title'),
      info = document.getElementById('modal-info'), fechar = document.getElementById('modal-close');
  var viewer = null, anterior = null;

  function abrir(url, nome, rot, gatilho) {
    anterior = gatilho || null;
    titulo.textContent = nome || 'Pré-visualização';
    info.textContent = 'Arraste para girar · role para aproximar';
    modal.hidden = false; document.body.classList.add('modal-open');
    if (!viewer) viewer = new BusinessXpViewer(canvas, { autoRotate: true });
    else viewer.resume();
    viewer.loadModel(url, { rotacaoY: rot });
    fechar.focus();
  }
  function fecharModal() {
    modal.hidden = true; document.body.classList.remove('modal-open');
    if (viewer) viewer.pause();
    if (anterior && anterior.focus) anterior.focus();
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-preview]');
    if (b) { e.preventDefault(); e.stopPropagation(); abrir(b.dataset.preview, b.dataset.title, parseFloat(b.dataset.rot || '0'), b); }
  }, true);
  fechar.addEventListener('click', fecharModal);
  modal.addEventListener('mousedown', function (e) { if (e.target === modal) fecharModal(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modal.hidden) fecharModal(); });
  canvas.addEventListener('viewer:loaded', function (e) {
    info.textContent = e.detail.triangulos.toLocaleString('pt-BR') + ' triângulos · arraste para girar';
  });
})();
