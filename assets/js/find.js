async function loadCleaners() {
  const res = await fetch('data/cleaners.json');
  return res.json();
}

function getQueryParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    q: (params.get('q') || '').trim(),
    service: (params.get('service') || '').trim()
  };
}

function uniqueValues(items, key) {
  return [...new Set(items.flatMap(item => item[key]))].sort();
}

function cleanerCard(cleaner) {
  return `
    <article class="card listing-card">
      <span class="eyebrow">Approved cleaner</span>
      <h3>${cleaner.business_name}</h3>
      <div class="meta">${cleaner.town} · ${cleaner.county}</div>
      <p>${cleaner.description}</p>
      <p><strong>Services:</strong> ${cleaner.services.join(', ')}</p>
      <div class="badge-grid left">
        ${cleaner.badges.map(b => `<span class="badge-pill">${b}</span>`).join('')}
      </div>
      <div class="actions">
        <a class="btn btn-primary" href="profile.html">View Profile</a>
        <a class="btn btn-outline" href="mailto:${cleaner.email}">Contact</a>
      </div>
    </article>
  `;
}

function applyFilters(cleaners) {
  const q = document.getElementById('searchInput').value.trim().toLowerCase();
  const service = document.getElementById('serviceFilter').value;
  const badge = document.getElementById('badgeFilter').value;

  return cleaners.filter(cleaner => {
    const haystack = [cleaner.business_name, cleaner.town, cleaner.county, cleaner.postcode, cleaner.description].join(' ').toLowerCase();
    const matchesText = !q || haystack.includes(q);
    const matchesService = !service || cleaner.services.includes(service);
    const matchesBadge = !badge || cleaner.badges.includes(badge);
    return matchesText && matchesService && matchesBadge;
  });
}

function render(cleaners) {
  const grid = document.getElementById('listingGrid');
  const count = document.getElementById('resultsCount');
  const filtered = applyFilters(cleaners);
  count.textContent = `${filtered.length} cleaner${filtered.length === 1 ? '' : 's'} found`;
  grid.innerHTML = filtered.map(cleanerCard).join('') || '<div class="card"><p>No cleaners match those filters yet.</p></div>';
}

loadCleaners().then(cleaners => {
  const serviceFilter = document.getElementById('serviceFilter');
  const badgeFilter = document.getElementById('badgeFilter');
  const searchInput = document.getElementById('searchInput');
  const params = getQueryParams();

  uniqueValues(cleaners, 'services').forEach(service => {
    const option = document.createElement('option');
    option.value = service;
    option.textContent = service;
    serviceFilter.appendChild(option);
  });
  uniqueValues(cleaners, 'badges').forEach(badge => {
    const option = document.createElement('option');
    option.value = badge;
    option.textContent = badge;
    badgeFilter.appendChild(option);
  });

  searchInput.value = params.q;
  if (params.service) serviceFilter.value = params.service;

  [searchInput, serviceFilter, badgeFilter].forEach(el => el.addEventListener('input', () => render(cleaners)));
  render(cleaners);
});
