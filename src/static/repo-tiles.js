/* ── Repo Tiles — donut rings flanking the graph panel ──── */

(function () {
  const LEFT = document.getElementById('repo-rail-left');
  const RIGHT = document.getElementById('repo-rail-right');
  const BOTTOM = document.getElementById('repo-rail-bottom');
  if (!LEFT || !RIGHT || !BOTTOM) return;

  const SIZE = 64;
  const OUTER = SIZE / 2 - 2;
  const INNER = OUTER - 10;

  const pie = d3.pie().sort(null).value(d => d.value);
  const arc = d3.arc().innerRadius(INNER).outerRadius(OUTER);

  function renderTile(repo) {
    const tile = document.createElement('div');
    tile.className = 'repo-tile';

    if (repo.domains.length) {
      const svgNS = 'http://www.w3.org/2000/svg';
      const svg = document.createElementNS(svgNS, 'svg');
      svg.setAttribute('viewBox', `0 0 ${SIZE} ${SIZE}`);
      svg.setAttribute('class', 'repo-tile__ring');

      const g = document.createElementNS(svgNS, 'g');
      g.setAttribute('transform', `translate(${SIZE / 2},${SIZE / 2})`);

      const data = repo.domains.map(d => ({ name: d.domain, value: d.snippets || d.skill_count || 1 }));
      for (const slice of pie(data)) {
        const path = document.createElementNS(svgNS, 'path');
        path.setAttribute('d', arc(slice));
        path.setAttribute('fill', window.domainColor ? window.domainColor(slice.data.name) : '#5a7a4f');
        path.setAttribute('opacity', '0.85');
        g.appendChild(path);
      }
      svg.appendChild(g);
      tile.appendChild(svg);
    }

    const name = document.createElement('div');
    name.className = 'repo-tile__name';
    name.textContent = repo.name;
    tile.appendChild(name);

    return tile;
  }

  fetch('/api/repositories')
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(repos => {
      repos.forEach((repo, i) => {
        const tile = renderTile(repo);
        if (i < 3) LEFT.appendChild(tile);
        else if (i < 6) RIGHT.appendChild(tile);
        else BOTTOM.appendChild(tile);
      });
    })
    .catch(() => {});

  // Fade out when chat starts
  const rails = [LEFT, RIGHT, BOTTOM];
  new MutationObserver(() => {
    if (document.body.classList.contains('hero-faded')) {
      rails.forEach(r => r.classList.add('repo-rail--hidden'));
    }
  }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
})();
