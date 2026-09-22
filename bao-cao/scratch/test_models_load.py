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

print("All models loaded successfully.")
