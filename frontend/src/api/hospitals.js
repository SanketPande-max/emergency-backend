/** Overpass API - fetch hospitals near a point (free, no key) */
const OVERPASS = 'https://overpass-api.de/api/interpreter';

export async function fetchNearbyHospitals(lat, lng, radiusM = 5000) {
  const query = `[out:json];(
    node["amenity"="hospital"](around:${radiusM},${lat},${lng});
    way["amenity"="hospital"](around:${radiusM},${lat},${lng});
    node["healthcare"="hospital"](around:${radiusM},${lat},${lng});
  );out center ${radiusM};`;
  try {
    const res = await fetch(OVERPASS, {
      method: 'POST',
      body: query,
      headers: { 'Content-Type': 'text/plain' },
    });
    const data = await res.json();
    const out = [];
    const seen = new Set();
    (data.elements || []).forEach((el) => {
      const center = el.center || el;
      const plat = center.lat;
      const plng = center.lon || center.lng;
      const name = el.tags?.name || 'Hospital';
      const key = `${plat},${plng}`;
      if (plat && plng && !seen.has(key)) {
        seen.add(key);
        out.push({ name, lat: plat, lng: plng });
      }
    });
    return out.sort((a, b) => {
      const d1 = Math.hypot(a.lat - lat, a.lng - lng);
      const d2 = Math.hypot(b.lat - lat, b.lng - lng);
      return d1 - d2;
    }).slice(0, 10);
  } catch (e) {
    console.warn('Overpass fetch failed:', e);
    return [];
  }
}
