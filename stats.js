// filename: stats.js
// Usage exemples:
//   node stats.js data/*.json
//   node stats.js data --artist "Damso"
//   node stats.js data --year 2024 --sort plays
//   node stats.js data --style rap-fr --sort ms
//
// Sorties : console + CSVs (sans device_mix, comme demandé)

const fs = require('fs');
const path = require('path');

// --------- Helpers ---------
function isFile(p) { try { return fs.statSync(p).isFile(); } catch { return false; } }
function isDir(p) { try { return fs.statSync(p).isDirectory(); } catch { return false; } }
function listJsonFilesFromArg(arg) {
  if (isDir(arg)) {
    return fs.readdirSync(arg).filter(f => f.toLowerCase().endsWith('.json')).map(f => path.join(arg, f));
  }
  if (isFile(arg)) return [arg];
  return [];
}
function parseJsonArrayFromFile(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  let text = raw.trim();
  let start = text.indexOf('[');
  let end = text.lastIndexOf(']');
  if (start !== -1 && end !== -1 && end > start) text = text.slice(start, end + 1);
  try {
    const data = JSON.parse(text);
    if (Array.isArray(data)) return data;
  } catch (e) {
    console.error(`Erreur de parsing JSON dans ${filePath}:`, e.message);
  }
  return [];
}
function toDate(ts) { try { return new Date(ts); } catch { return null; } }
function minutes(ms) { return ms / 1000 / 60; }
function hours(ms) { return ms / 1000 / 3600; }
function normalizeString(s) { if (!s || typeof s !== 'string') return ''; return s.trim(); }
function keySafe(str) { return (str || '').toLowerCase(); }
function ensureDir(p) { if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true }); }

// --------- CLI options ---------
function parseArgs(argv) {
  const opts = { artist: null, year: null, style: null, sort: 'ms' };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--artist') opts.artist = argv[++i];
    else if (a === '--year') opts.year = Number(argv[++i]);
    else if (a === '--style') opts.style = argv[++i];
    else if (a === '--sort') opts.sort = argv[++i]; // 'ms' | 'plays'
  }
  return opts;
}

// Mapping simple pour “style” (modifie-le selon tes goûts)
const STYLE_MAP = [
  { key: 'rap-fr', include: [/gazo/i, /sdm/i, /plk/i, /damso/i, /werenoi/i, /ninho/i, /dinos/i, /booba/i, /laylow/i, /josman/i, /kerchak/i] },
  { key: 'lofi', include: [/lofi/i, /nightcore/i, /Closed on Sunday/i, /Sad Gatomon/i, /kisa/i, /Kioshi/i, /Linearwave/i, /Jordy Chandra/i] },
  { key: 'hardstyle', include: [/hardstyle/i, /SICK LEGEND/i, /BAKI\b/i, /PXSEIDON/i, /crypvolk/i, /Venko/i] },
  { key: 'kpop-jpop', include: [/k\/da/i, /yoasobi/i, /\bado\b/i, /\blisa\b/i, /rosé/i, /eve\b/i] },
  { key: 'pop-indie', include: [/Noah Kahan/i, /JVKE/i, /The Neighbourhood/i, /Lord Huron/i, /Mitski/i, /Suki Waterhouse/i] },
];

function matchStyle(rec, styleKey) {
  if (!styleKey) return true;
  const rule = STYLE_MAP.find(x => x.key === styleKey);
  if (!rule) return true;
  const hay = `${rec.artist} ${rec.track} ${rec.album}`;
  return rule.include.some(rx => rx.test(hay));
}

// --------- Aggregation ---------
function aggregate(records, opts = { artist: null, year: null, style: null, sort: 'ms' }) {
  const seen = new Set();
  const clean = [];

  for (const r of records) {
    const ts = r.ts || r.timestamp || r.endTime || r.startTime || '';
    const uri = r.spotify_track_uri || r.trackUri || '';
    const key = `${ts}|${uri}`;
    if (seen.has(key)) continue;
    seen.add(key);

    const ms_played = typeof r.ms_played === 'number' ? r.ms_played : 0;
    const platform = normalizeString(r.platform);
    const country = normalizeString(r.conn_country);
    const ip = normalizeString(r.ip_addr);
    const artist = normalizeString(r.master_metadata_album_artist_name);
    const track = normalizeString(r.master_metadata_track_name);
    const album = normalizeString(r.master_metadata_album_album_name);
    const reason_start = normalizeString(r.reason_start);
    const reason_end = normalizeString(r.reason_end);
    const skipped = !!r.skipped;
    const offline = !!r.offline;
    const incognito = !!r.incognito_mode;
    const shuffle = !!r.shuffle;

    clean.push({
      ts,
      dateObj: toDate(ts),
      ms_played,
      platform,
      country,
      ip,
      artist,
      track,
      album,
      uri,
      reason_start,
      reason_end,
      skipped,
      offline,
      incognito,
      shuffle,
    });
  }

  // Filtre selon opts
  const filtered = clean.filter(r => {
    if (opts.artist && keySafe(r.artist) !== keySafe(opts.artist)) return false;
    if (opts.year && r.dateObj && r.dateObj.getUTCFullYear() !== Number(opts.year)) return false;
    if (!matchStyle(r, opts.style)) return false;
    return true;
  });

  const base = filtered;

  // Stats
  const totals = {
    plays: base.length,
    ms: base.reduce((acc, r) => acc + (r.ms_played || 0), 0),
    skippedCount: base.reduce((acc, r) => acc + (r.skipped ? 1 : 0), 0),
    offlineCount: base.reduce((acc, r) => acc + (r.offline ? 1 : 0), 0),
    incognitoCount: base.reduce((acc, r) => acc + (r.incognito ? 1 : 0), 0),
    shuffleCount: base.reduce((acc, r) => acc + (r.shuffle ? 1 : 0), 0),
  };

  const byArtist = new Map();
  const byTrack = new Map();
  const byDay = new Map();
  const skipArtist = new Map();

  for (const r of base) {
    const artistKey = keySafe(r.artist);
    const trackKey = keySafe(`${r.artist} — ${r.track}`);
    const dayKey = r.dateObj ? r.dateObj.toISOString().slice(0, 10) : 'unknown';

    // Artist
    if (!byArtist.has(artistKey)) byArtist.set(artistKey, { artist: r.artist, plays: 0, ms: 0 });
    const a = byArtist.get(artistKey); a.plays += 1; a.ms += r.ms_played || 0;

    // Track
    if (!byTrack.has(trackKey)) byTrack.set(trackKey, { key: trackKey, artist: r.artist, track: r.track, plays: 0, ms: 0 });
    const t = byTrack.get(trackKey); t.plays += 1; t.ms += r.ms_played || 0;

    // Day
    if (!byDay.has(dayKey)) byDay.set(dayKey, { day: dayKey, plays: 0, ms: 0 });
    const d = byDay.get(dayKey); d.plays += 1; d.ms += r.ms_played || 0;

    // Skip by artist
    if (!skipArtist.has(artistKey)) skipArtist.set(artistKey, { artist: r.artist, plays: 0, skipped: 0 });
    const sa = skipArtist.get(artistKey); sa.plays += 1; if (r.skipped) sa.skipped += 1;
  }

  const sortByKey = (arr, key = 'ms') => {
    if (key === 'plays') return arr.sort((x, y) => y.plays - x.plays);
    return arr.sort((x, y) => y.ms - x.ms);
  };
  const sortByDayAsc = (arr) => arr.sort((x, y) => (x.day > y.day ? 1 : -1));

  const topArtists = sortByKey(Array.from(byArtist.values()), opts.sort).slice(0, 20);
  const topTracks = sortByKey(Array.from(byTrack.values()), opts.sort).slice(0, 20);
  const days = sortByDayAsc(Array.from(byDay.values()));
  const skipRates = Array.from(skipArtist.values())
    .map(x => ({ artist: x.artist, plays: x.plays, skipped: x.skipped, skip_rate: x.plays ? (x.skipped / x.plays) : 0 }))
    .sort((a, b) => b.skip_rate - a.skip_rate);

  return { base, totals, topArtists, topTracks, days, skipRates, opts };
}

// --------- CSV Export ---------
function toCSV(rows, headers) {
  const escape = (v) => {
    if (v === null || v === undefined) return '';
    const s = String(v);
    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };
  const lines = [];
  lines.push(headers.join(','));
  for (const r of rows) lines.push(headers.map(h => escape(r[h])).join(','));
  return lines.join('\n');
}

function exportCSVs(stats) {
  ensureDir('exports');

  // Artists
  const artistsRows = stats.topArtists.map(a => ({
    artist: a.artist,
    plays: a.plays,
    ms: a.ms,
    minutes: Math.round(minutes(a.ms) * 100) / 100,
    hours: Math.round(hours(a.ms) * 100) / 100,
  }));
  fs.writeFileSync(
    path.join('exports', 'plays_by_artist.csv'),
    toCSV(artistsRows, ['artist', 'plays', 'ms', 'minutes', 'hours']),
    'utf8'
  );

  // Tracks
  const tracksRows = stats.topTracks.map(t => ({
    artist: t.artist,
    track: t.track,
    plays: t.plays,
    ms: t.ms,
    minutes: Math.round(minutes(t.ms) * 100) / 100,
    hours: Math.round(hours(t.ms) * 100) / 100,
  }));
  fs.writeFileSync(
    path.join('exports', 'plays_by_track.csv'),
    toCSV(tracksRows, ['artist', 'track', 'plays', 'ms', 'minutes', 'hours']),
    'utf8'
  );

  // Days
  const dayRows = stats.days.map(d => ({
    day: d.day,
    plays: d.plays,
    ms: d.ms,
    minutes: Math.round(minutes(d.ms) * 100) / 100,
    hours: Math.round(hours(d.ms) * 100) / 100,
  }));
  fs.writeFileSync(
    path.join('exports', 'plays_by_day.csv'),
    toCSV(dayRows, ['day', 'plays', 'ms', 'minutes', 'hours']),
    'utf8'
  );

  // Skip rates
  const skipRows = stats.skipRates.map(s => ({
    artist: s.artist,
    plays: s.plays,
    skipped: s.skipped,
    skip_rate: Math.round(s.skip_rate * 10000) / 10000,
  }));
  fs.writeFileSync(
    path.join('exports', 'skip_rates.csv'),
    toCSV(skipRows, ['artist', 'plays', 'skipped', 'skip_rate']),
    'utf8'
  );
}

// --------- Report ---------
function printReport(stats) {
  const totalHours = hours(stats.totals.ms);
  const totalMinutes = minutes(stats.totals.ms);

  console.log('================ Spotify Stats ================');
  console.log(`Filtres: artist=${stats.opts.artist || 'ALL'}, year=${stats.opts.year || 'ALL'}, style=${stats.opts.style || 'ALL'}, sort=${stats.opts.sort}`);
  console.log(`Total plays:        ${stats.totals.plays}`);
  console.log(`Total time:         ${totalHours.toFixed(2)} h (${Math.round(totalMinutes)} min)`);
  console.log(`Skipped plays:      ${stats.totals.skippedCount} (${(stats.totals.plays ? (stats.totals.skippedCount / stats.totals.plays) * 100 : 0).toFixed(1)}%)`);
  console.log(`Offline plays:      ${stats.totals.offlineCount}`);
  console.log(`Incognito plays:    ${stats.totals.incognitoCount}`);
  console.log(`Shuffle plays:      ${stats.totals.shuffleCount}`);
  console.log('');

  console.log(`Top artists (by ${stats.opts.sort}):`);
  for (const a of stats.topArtists.slice(0, 10)) {
    const val = stats.opts.sort === 'plays' ? `${a.plays} plays` : `${hours(a.ms).toFixed(2)} h`;
    console.log(`  - ${a.artist}: ${val}`);
  }
  console.log('');

  console.log(`Top tracks (by ${stats.opts.sort}):`);
  for (const t of stats.topTracks.slice(0, 10)) {
    const val = stats.opts.sort === 'plays' ? `${t.plays} plays` : `${hours(t.ms).toFixed(2)} h`;
    console.log(`  - ${t.artist} — ${t.track}: ${val}`);
  }
  console.log('');

  console.log('Skip rates (worst first):');
  for (const s of stats.skipRates.slice(0, 10)) {
    console.log(`  - ${s.artist}: ${(s.skip_rate * 100).toFixed(1)}% (${s.skipped}/${s.plays})`);
  }
  console.log('===============================================');
}

// Ajoute en haut :
const HTML_DIR = 'exports';

// À la fin, avant main():
function exportHTML(stats) {
  ensureDir(HTML_DIR);
  const html = `<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Spotify Stats Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://unpkg.com/sakura.css/css/sakura.css" rel="stylesheet">
  <style>
    body { max-width: 1100px; margin: 0 auto; }
    .grid { display: grid; grid-template-columns: 1fr; gap: 24px; }
    @media (min-width: 900px) { .grid { grid-template-columns: 1fr 1fr; } }
    canvas { background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 8px; }
    .meta { font-size: 14px; color: #666; margin-bottom: 16px; }
    .card { padding: 8px; border: 1px solid #eee; border-radius: 8px; background: #fff; }
    code { font-size: 12px; }
  </style>
</head>
<body>
  <h1>Spotify Stats</h1>
  <p class="meta">
    Filtres: artist=<strong>${stats.opts.artist || 'ALL'}</strong>,
    year=<strong>${stats.opts.year || 'ALL'}</strong>,
    style=<strong>${stats.opts.style || 'ALL'}</strong>,
    sort=<strong>${stats.opts.sort}</strong><br>
    Total plays: <strong>${stats.totals.plays}</strong> —
    Temps total: <strong>${(stats.totals.ms/1000/3600).toFixed(2)} h</strong> —
    Skips: <strong>${stats.totals.skippedCount}</strong> (${(stats.totals.plays? (stats.totals.skippedCount/stats.totals.plays)*100 : 0).toFixed(1)}%)
  </p>

  <div class="grid">
    <div class="card">
      <h3>Top artistes (${stats.opts.sort})</h3>
      <canvas id="chartArtists" height="300"></canvas>
    </div>
    <div class="card">
      <h3>Top morceaux (${stats.opts.sort})</h3>
      <canvas id="chartTracks" height="300"></canvas>
    </div>
    <div class="card">
      <h3>Écoute par jour</h3>
      <canvas id="chartDays" height="300"></canvas>
    </div>
    <div class="card">
      <h3>Taux de skip par artiste</h3>
      <canvas id="chartSkips" height="300"></canvas>
    </div>
  </div>

  <p class="meta">Exports CSV: plays_by_artist.csv, plays_by_track.csv, plays_by_day.csv, skip_rates.csv</p>

  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <script>
    const sortMode = ${JSON.stringify(stats.opts.sort)};
    const topArtists = ${JSON.stringify(stats.topArtists)};
    const topTracks  = ${JSON.stringify(stats.topTracks)};
    const days       = ${JSON.stringify(stats.days)};
    const skipRates  = ${JSON.stringify(stats.skipRates)};

    function valueFor(item) {
      return sortMode === 'plays' ? item.plays : (item.ms/1000/3600);
    }

    function makeBar(ctx, labels, data, label, color='#2b8a3e') {
      return new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label, data, backgroundColor: color }] },
        options: {
          responsive: true,
          plugins: { legend: { display: false }, tooltip: { callbacks: {
            label: (tt) => label + ': ' + (sortMode==='plays' ? tt.raw.toFixed(0)+' plays' : tt.raw.toFixed(2)+' h')
          }}},
          scales: { x: { ticks: { autoSkip: false, maxRotation: 45, minRotation: 0 } }, y: { beginAtZero: true } }
        }
      });
    }

    function makeLine(ctx, labels, data, label, color='#1c7ed6') {
      return new Chart(ctx, {
        type: 'line',
        data: { labels, datasets: [{ label, data, borderColor: color, fill: true, tension: 0.2 }] },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true } }
        }
      });
    }

    // Top Artists
    const aLabels = topArtists.map(a => a.artist);
    const aData   = topArtists.map(a => valueFor(a));
    makeBar(document.getElementById('chartArtists'), aLabels, aData, sortMode === 'plays' ? 'Plays' : 'Heures', '#495057');

    // Top Tracks
    const tLabels = topTracks.map(t => (t.artist + ' — ' + t.track));
    const tData   = topTracks.map(t => valueFor(t));
    makeBar(document.getElementById('chartTracks'), tLabels, tData, sortMode === 'plays' ? 'Plays' : 'Heures', '#0b7285');

    // Days (heures)
    const dLabels = days.map(d => d.day);
    const dData   = days.map(d => (d.ms/1000/3600));
    makeLine(document.getElementById('chartDays'), dLabels, dData, 'Heures / jour', '#1c7ed6');

    // Skip rates
    const sLabels = skipRates.slice(0, 20).map(s => s.artist);
    const sData   = skipRates.slice(0, 20).map(s => +(s.skip_rate * 100).toFixed(2));
    makeBar(document.getElementById('chartSkips'), sLabels, sData, 'Skip %', '#c92a2a');
  </script>
</body>
</html>`;
  fs.writeFileSync(path.join(HTML_DIR, 'report.html'), html, 'utf8');
}


// --------- Main ---------
function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 0) {
    console.error('Usage: node stats.js <files|directory> [--artist "Nom"] [--year 2024] [--style rap-fr] [--sort ms|plays]');
    process.exit(1);
  }

  const opts = parseArgs(argv);
  const inputArgs = argv.filter(a => !a.startsWith('--'));

  let files = [];
  for (const arg of inputArgs) files = files.concat(listJsonFilesFromArg(arg));
  files = Array.from(new Set(files));
  if (files.length === 0) {
    console.error('Aucun fichier JSON trouvé. Passe un dossier ou des fichiers *.json');
    process.exit(1);
  }

  let all = [];
  for (const f of files) {
    const arr = parseJsonArrayFromFile(f);
    if (arr.length === 0) {
      console.warn(`(vide) Ignoré: ${f}`);
      continue;
    }
    all = all.concat(arr);
  }
  if (all.length === 0) {
    console.error('Aucun enregistrement après parsing.');
    process.exit(1);
  }

  const stats = aggregate(all, opts);
  printReport(stats);
exportCSVs(stats);
exportHTML(stats);
console.log(`\nHTML: ${path.resolve(path.join('exports','report.html'))}`);


  console.log('');
  console.log(`Exports écrits dans: ${path.resolve('exports')}`);
}

main();
