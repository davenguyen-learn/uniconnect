"""Activity constants and enums."""

import enum

# Temporal lock: activities cannot be modified within this many minutes of start_time
TEMPORAL_LOCK_MINUTES = 30

# Default search radius in meters
DEFAULT_SEARCH_RADIUS = 5000

# Maximum search radius in meters
MAX_SEARCH_RADIUS = 50_000

# Coordinate obfuscation radius in meters (for non-participants)
OBFUSCATION_RADIUS = 200


class ActivityCategory(str, enum.Enum):
    STUDY = "study"
    SPORTS = "sports"
    SOCIAL = "social"
    MUSIC = "music"
    FOOD = "food"
    GAMING = "gaming"
    VOLUNTEERING = "volunteering"
    OTHER = "other"


class ActivityPrivacy(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
