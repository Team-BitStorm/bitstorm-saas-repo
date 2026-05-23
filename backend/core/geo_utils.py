import math
from decimal import Decimal


def haversine_km(
    lat1: Decimal | float,
    lon1: Decimal | float,
    lat2: Decimal | float,
    lon2: Decimal | float,
) -> Decimal:
    """Great-circle distance in kilometres between two WGS84 points."""
    r = 6371.0
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    d_phi = math.radians(float(lat2) - float(lat1))
    d_lambda = math.radians(float(lon2) - float(lon1))
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return Decimal(str(round(r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)))


def estimate_travel_time_minutes(distance_km: Decimal) -> int:
    """Rough urban travel estimate at ~30 km/h average."""
    if distance_km <= 0:
        return 0
    return max(1, int(float(distance_km) / 30 * 60))


def location_has_coordinates(location) -> bool:
    return (
        location is not None
        and location.latitude is not None
        and location.longitude is not None
    )
