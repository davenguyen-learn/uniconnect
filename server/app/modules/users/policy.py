"""User achievement and recognition domain policy."""

# Default CTXH graduation target for UniConnect
CTXH_TARGET_DAYS: float = 15.0

# Immutable rank thresholds ordered from highest to lowest
_RANK_THRESHOLDS = (
    (500, "Thành viên Tiêu biểu"),
    (200, "Thành viên Năng nổ"),
    (50, "Thành viên Tích cực"),
    (0, "Thành viên Mới"),
)


def resolve_rank_title(trophy_points: int) -> str:
    """Resolve user recognition rank title from verified trophy points."""
    for threshold, title in _RANK_THRESHOLDS:
        if trophy_points >= threshold:
            return title
    return "Thành viên Mới"
