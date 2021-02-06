from django.contrib import admin

from core.models import (
    User,
    UserProfile,
    MonitorStock,
    Strategy,
    PortHistory,
    OHLCV,
)

admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(MonitorStock)
admin.site.register(Strategy)
admin.site.register(PortHistory)
admin.site.register(OHLCV)