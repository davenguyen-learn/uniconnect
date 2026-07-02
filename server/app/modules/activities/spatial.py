"""Spatial utilities for coordinate obfuscation and validation."""

import math
import random


def obfuscate_coordinates(lat: float, lng: float, radius_meters: float = 200.0) -> tuple[float, float]:
    """Add a random offset within the given radius to obscure exact location.

    Uses uniform random distribution in a circle to avoid clustering at center.
    """
    # Random angle and distance (sqrt for uniform distribution in circle)
    angle = random.uniform(0, 2 * math.pi)
    distance = radius_meters * math.sqrt(random.random())

    # Convert distance to degrees (approximate)
    # 1 degree latitude ≈ 111,320 meters
    # 1 degree longitude ≈ 111,320 * cos(latitude) meters
    lat_offset = (distance * math.cos(angle)) / 111_320
    lng_offset = (distance * math.sin(angle)) / (111_320 * math.cos(math.radians(lat)))

    return (lat + lat_offset, lng + lng_offset)


def validate_coordinates(lat: float, lng: float) -> bool:
    """Check if coordinates are within valid geographic bounds."""
    return -90 <= lat <= 90 and -180 <= lng <= 180
