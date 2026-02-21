import math

def haversine_distance(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return c * 6371  # km

def ambulances_sorted_by_distance(ambulances, target_lat, target_lng):
    """Return list of (distance, ambulance) sorted by distance ascending."""
    out = []
    for amb in ambulances:
        loc = amb.get('current_location')
        if not loc:
            continue
        d = haversine_distance(target_lat, target_lng, loc['lat'], loc['lng'])
        out.append((d, amb))
    out.sort(key=lambda x: x[0])
    return out

def find_nearest_ambulance(ambulances, target_lat, target_lng, prefer_active=True):
    """
    Prefer nearest ACTIVE ambulance; if none active, return nearest any.
    ambulances: list of docs with current_location and status.
    """
    sorted_list = ambulances_sorted_by_distance(ambulances, target_lat, target_lng)
    if not sorted_list:
        return None
    if prefer_active:
        for _d, amb in sorted_list:
            if amb.get('status') == 'active':
                return amb
    return sorted_list[0][1]
