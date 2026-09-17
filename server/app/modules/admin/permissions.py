"""Granular permissions for Admin Command Center operations."""

from app.core.dependencies import require_role

# Full admin-only permissions
require_admin_access = require_role("admin")
require_user_management_permission = require_role("admin")
require_verification_permission = require_role("admin")
require_moderation_permission = require_role("admin")

# Educational staff / admin shared read/audit permissions
require_staff_or_admin = require_role("admin", "edu_org")
