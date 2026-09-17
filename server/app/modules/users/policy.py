"""User achievement and recognition domain policy."""

# Default CTXH graduation target for UniConnect
CTXH_TARGET_DAYS: float = 15.0

# Immutable rank thresholds ordered from highest to lowest
_RANK_THRESHOLDS = (
    (500, "Đại sứ Hoạt động (Ambassador)"),
    (200, "Thủ lĩnh Năng động (Leader)"),
    (50, "Tình nguyện viên Tiên phong (Pioneer)"),
    (0, "Tân sinh viên Tích cực (Active Member)"),
)


def resolve_rank_title(trophy_points: int) -> str:
    """Resolve user recognition rank title from verified trophy points."""
    for threshold, title in _RANK_THRESHOLDS:
        if trophy_points >= threshold:
            return title
    return "Tân sinh viên Tích cực (Active Member)"
