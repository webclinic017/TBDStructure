from django.contrib import admin

from core.models import (
    User,
    UserProfile,
    MonitorStock,
    PortHistory,
)

admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(MonitorStock)
admin.site.register(PortHistory)