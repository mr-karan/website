// Theme toggle, code copy buttons, image lightbox. No dependencies.
(function () {
  'use strict';

  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    var l = document.getElementById('syn-light');
    var d = document.getElementById('syn-dark');
    if (l && d) {
      l.media = t === 'dark' ? 'not all' : 'all';
      d.media = t === 'dark' ? 'all' : 'not all';
    }
  }

  var toggle = document.querySelector('.theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var cur = document.documentElement.getAttribute('data-theme') ||
        (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      var next = cur === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', next);
      applyTheme(next);
    });
  }

  // Copy button on every code block
  document.querySelectorAll('pre').forEach(function (pre) {
    var code = pre.querySelector('code');
    if (!code) return;
    var btn = document.createElement('button');
    btn.className = 'copy-code';
    btn.type = 'button';
    btn.textContent = 'copy';
    btn.addEventListener('click', function () {
      navigator.clipboard.writeText(code.innerText).then(function () {
        btn.textContent = 'copied';
        setTimeout(function () { btn.textContent = 'copy'; }, 1500);
      });
    });
    pre.appendChild(btn);
  });

  // Lightbox for a.lightbox-thumbnail images
  var thumbs = document.querySelectorAll('a.lightbox-thumbnail');
  if (thumbs.length) {
    var modal = document.createElement('div');
    modal.className = 'lightbox-modal';
    modal.innerHTML = '<img src="" alt="">';
    document.body.appendChild(modal);
    var img = modal.querySelector('img');

    thumbs.forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        img.src = link.getAttribute('href');
        img.alt = (link.querySelector('img') || {}).alt || '';
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
      });
    });

    function close() {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
    modal.addEventListener('click', close);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && modal.classList.contains('active')) close();
    });
  }
})();
