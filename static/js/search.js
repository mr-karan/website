// Minimal search over Zola's fuse_json index (title + description only).
// Index is fetched once, on first focus of the input.
(function () {
  'use strict';

  var input = document.getElementById('search-input');
  var results = document.getElementById('search-results');
  var status = document.getElementById('search-status');
  if (!input || !results) return;

  var index = null;

  function load() {
    if (index) return Promise.resolve(index);
    status.textContent = 'loading index…';
    return fetch('/search_index.en.json')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        index = data;
        status.textContent = '';
        return index;
      })
      .catch(function () { status.textContent = 'could not load search index'; });
  }

  function score(entry, terms) {
    var title = (entry.title || '').toLowerCase();
    var desc = (entry.description || '').toLowerCase();
    var s = 0;
    for (var i = 0; i < terms.length; i++) {
      var t = terms[i];
      if (!t) continue;
      if (title.indexOf(t) !== -1) s += 3;
      else if (desc.indexOf(t) !== -1) s += 1;
      else return 0; // every term must match somewhere
    }
    return s;
  }

  function render(q) {
    results.innerHTML = '';
    if (!q || !index) { status.textContent = ''; return; }
    var terms = q.toLowerCase().split(/\s+/);
    var hits = [];
    for (var i = 0; i < index.length; i++) {
      var s = score(index[i], terms);
      if (s > 0) hits.push({ s: s, e: index[i] });
    }
    hits.sort(function (a, b) { return b.s - a.s; });
    hits = hits.slice(0, 20);
    status.textContent = hits.length ? hits.length + ' result' + (hits.length === 1 ? '' : 's') : 'no results';
    hits.forEach(function (h) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = h.e.url;
      a.textContent = h.e.title;
      li.appendChild(a);
      if (h.e.description) {
        var d = document.createElement('span');
        d.className = 'desc';
        d.textContent = h.e.description;
        li.appendChild(d);
      }
      results.appendChild(li);
    });
  }

  var timer;
  input.addEventListener('focus', load, { once: true });
  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () {
      load().then(function () { render(input.value.trim()); });
    }, 120);
  });

  // Support ?q= links
  var q = new URLSearchParams(location.search).get('q');
  if (q) {
    input.value = q;
    load().then(function () { render(q); });
  }
})();
