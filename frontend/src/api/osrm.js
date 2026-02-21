/**
 * OSRM - Free routing API (no API key)
 * https://router.project-osrm.org/
 */
const OSRM_BASE = 'https://router.project-osrm.org/route/v1/driving';

export async function fetchRoute(origin, destination) {
  if (!origin?.lat || !destination?.lat) return null;
  const coords = `${origin.lng},${origin.lat};${destination.lng},${destination.lat}`;
  const url = `${OSRM_BASE}/${coords}?overview=full&geometries=geojson`;
  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.code === 'Ok' && data.routes?.[0]?.geometry?.coordinates?.length) {
      return data.routes[0].geometry.coordinates.map(([lng, lat]) => ({ lat, lng }));
    }
  } catch (e) {
    console.warn('OSRM route fetch failed:', e);
  }
  return null;
}
