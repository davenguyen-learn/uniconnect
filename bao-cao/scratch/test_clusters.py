import sys
sys.path.insert(0, r'server')
from app.core.models import Base
import app.modules.users.models
import app.modules.activities.models
import app.modules.groups.models
import app.modules.participation.models
import app.modules.interactions.models
import app.modules.forms.models
import app.modules.calendar.models
import app.modules.trophies.models
import app.modules.notifications.models
import app.modules.reports.models
import app.modules.admin.models

tables = Base.metadata.tables

# Group tables into 7 domain clusters
clusters = [
    {
        "name": "Nhóm Người dùng và Đồ thị xã hội (Users & Social Graph)",
        "tables": ["users", "user_follows"]
    },
    {
        "name": "Nhóm Hoạt động và Sự kiện (Activities Module)",
        "tables": ["activities"]
    },
    {
        "name": "Nhóm Nhóm sinh viên và Đồng tổ chức (Groups & Co-hosting)",
        "tables": ["groups", "group_members", "group_join_requests", "activity_cohosts", "activity_cohost_invitations", "organization_verification_requests"]
    },
    {
        "name": "Nhóm Đăng ký tham gia và Biểu mẫu tùy biến (Participation & Forms)",
        "tables": ["join_requests", "custom_forms", "form_fields"]
    },
    {
        "name": "Nhóm Tương tác cộng đồng (Interactions Module)",
        "tables": ["comments", "content_likes"]
    },
    {
        "name": "Nhóm Lịch cá nhân thông minh (Smart Calendar)",
        "tables": ["user_busy_slots", "busy_slot_exceptions", "user_vacation_periods"]
    },
    {
        "name": "Nhóm Trò chơi hóa và Thành tích (Gamification & Trophies)",
        "tables": ["trophies", "user_trophies"]
    },
    {
        "name": "Nhóm Quản trị, Thông báo và Giám sát (Administration & Notifications)",
        "tables": ["notifications", "reports", "admin_audit_logs"]
    }
]

total = sum(len(c["tables"]) for c in clusters)
print(f"Total tables categorized: {total}")
for c in clusters:
    print(c["name"])
    for t in c["tables"]:
        tbl = tables[t]
        print(f"  - {t}: {len(tbl.columns)} columns")
