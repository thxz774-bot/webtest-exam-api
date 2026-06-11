(function () {
  'use strict';

  /* ── refs ─────────────────────────────────────── */
  const sidebar     = document.getElementById('sidebar');
  const mobOverlay  = document.getElementById('mobOverlay');
  const mobToggle   = document.getElementById('mobToggle');
  const toastStack  = document.getElementById('toastStack');
  const crumb       = document.getElementById('crumbCurrent');

  const dropzone    = document.getElementById('dropzone');
  const dzDefault   = document.getElementById('dzDefault');
  const dzSuccess   = document.getElementById('dzSuccess');
  const dzFileName  = document.getElementById('dzFileName');
  const fileInput   = document.getElementById('fileInput');
  const btnGerar    = document.getElementById('btnGerar');
  const btnLimpar   = document.getElementById('btnLimpar');
  const previewArea = document.getElementById('previewArea');
  const previewData = document.getElementById('previewData');

  const checks = {
    1: document.getElementById('check1'),
    2: document.getElementById('check2'),
    3: document.getElementById('check3'),
    4: document.getElementById('check4'),
  };

  const PAGE_NAMES = { inicio: 'Início', modelo: 'Modelo', organizar: 'Organizar' };
  let uploaded = false;

  /* ── navigation ───────────────────────────────── */
  function navigate(id) {
    document.querySelectorAll('.page').forEach(function (p) { p.classList.remove('active'); });
    document.querySelectorAll('.sb-link').forEach(function (l) { l.classList.remove('active'); });

    var page = document.getElementById('page-' + id);
    var link = document.querySelector('.sb-link[data-page="' + id + '"]');
    if (page) page.classList.add('active');
    if (link) link.classList.add('active');
    if (crumb) crumb.textContent = PAGE_NAMES[id] || id;
    closeSidebar();
  }

  document.querySelectorAll('.sb-link').forEach(function (l) {
    l.addEventListener('click', function (e) {
      e.preventDefault();
      navigate(l.dataset.page);
    });
  });

  document.querySelectorAll('[data-goto]').forEach(function (el) {
    el.addEventListener('click', function () { navigate(el.dataset.goto); });
  });

  /* ── mobile sidebar ───────────────────────────── */
  function openSidebar()  { sidebar.classList.add('open'); mobOverlay.classList.add('show'); }
  function closeSidebar() { sidebar.classList.remove('open'); mobOverlay.classList.remove('show'); }
  if (mobToggle)   mobToggle.addEventListener('click', openSidebar);
  if (mobOverlay)  mobOverlay.addEventListener('click', closeSidebar);

  /* ── toasts ───────────────────────────────────── */
  function toast(msg, type) {
    type = type || 's';
    var icons = { s: 'fa-circle-check', i: 'fa-circle-info' };
    var el = document.createElement('div');
    el.className = 'toast toast-' + type;
    el.innerHTML = '<i class="fa-solid ' + (icons[type] || icons.i) + ' ti"></i><span>' + msg + '</span>';
    toastStack.appendChild(el);
    setTimeout(function () {
      el.classList.add('out');
      el.addEventListener('animationend', function () { el.remove(); }, { once: true });
    }, 3400);
  }

  /* ── toggle buttons (organizar page) ─────────── */
  function makePairToggle(idA, idB) {
    var a = document.getElementById(idA);
    var b = document.getElementById(idB);
    if (!a || !b) return;
    a.addEventListener('click', function () { a.classList.add('active'); b.classList.remove('active'); });
    b.addEventListener('click', function () { b.classList.add('active'); a.classList.remove('active'); });
  }
  makePairToggle('toggleSepSim', 'toggleSepNao');
  makePairToggle('toggleFiscalSim', 'toggleFiscalNao');

  /* ── upload ───────────────────────────────────── */
  function applyUpload(name) {
    name = name || 'arquivo_alunos.xlsx';
    dzDefault.style.display  = 'none';
    dzSuccess.style.display  = 'flex';
    dzFileName.textContent   = name;
    dropzone.classList.remove('dz-drag');
    uploaded = true;
    btnGerar.disabled  = false;
    btnLimpar.disabled = false;
    animateChecks();
    setTimeout(function () {
      if (previewArea) previewArea.style.display = 'none';
      if (previewData) previewData.style.display = 'flex';
    }, 600);
  }

  function clearUpload() {
    dzDefault.style.display = 'flex';
    dzSuccess.style.display = 'none';
    dzFileName.textContent  = '';
    uploaded = false;
    btnGerar.disabled  = true;
    btnLimpar.disabled = true;
    resetChecks();
    if (previewArea) previewArea.style.display = 'flex';
    if (previewData) previewData.style.display = 'none';
    fileInput.value = '';
    toast('Upload removido', 'i');
  }

  function animateChecks() {
    [1, 2, 3, 4].forEach(function (k, i) {
      setTimeout(function () {
        if (checks[k]) checks[k].classList.add('done');
      }, 110 * i);
    });
  }

  function resetChecks() {
    [1, 2, 3, 4].forEach(function (k) {
      if (checks[k]) checks[k].classList.remove('done');
    });
  }

  if (dropzone) {
    dropzone.addEventListener('click', function () { if (!uploaded) fileInput.click(); });
    dropzone.addEventListener('dragenter', function (e) { e.preventDefault(); dropzone.classList.add('dz-drag'); });
    dropzone.addEventListener('dragover',  function (e) { e.preventDefault(); dropzone.classList.add('dz-drag'); });
    dropzone.addEventListener('dragleave', function (e) {
      if (!dropzone.contains(e.relatedTarget)) dropzone.classList.remove('dz-drag');
    });
    dropzone.addEventListener('drop', function (e) {
      e.preventDefault();
      dropzone.classList.remove('dz-drag');
      var f = e.dataTransfer.files;
      if (f && f.length) applyUpload(f[0].name);
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', function () {
      if (fileInput.files && fileInput.files.length) applyUpload(fileInput.files[0].name);
    });
  }

  if (btnLimpar) btnLimpar.addEventListener('click', clearUpload);

  if (btnGerar) {
    btnGerar.addEventListener('click', function () {
      if (!uploaded) return;
      var orig = btnGerar.innerHTML;
      btnGerar.disabled = true;
      btnGerar.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Gerando...';
      setTimeout(function () {
        btnGerar.innerHTML = orig;
        btnGerar.disabled  = false;
        toast('Arquivo gerado com sucesso (demonstração)', 's');
      }, 2000);
    });
  }

  /* ── download buttons ─────────────────────────── */
  ['btnDownloadInicio', 'btnDownloadModelo', 'btnDownloadModelo2', 'btnStepDownload'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('click', function () {
      toast('Download simulado — modelo disponível', 'i');
    });
  });

  /* ── hover lift (touch-safe) ──────────────────── */
  document.querySelectorAll('.feat-card, .step-item, .hero-stat').forEach(function (el) {
    el.addEventListener('mouseenter', function () { el.style.willChange = 'transform'; });
    el.addEventListener('mouseleave', function () { el.style.willChange = ''; });
  });

  /* ── init ─────────────────────────────────────── */
  navigate('inicio');

}());