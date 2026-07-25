from django.contrib import admin

from apps.careers.infrastructure.models import (
    Achievement,
    Engagement,
    EngagementDomain,
    EngagementUrl,
    SupportDomain,
)

admin.site.register(SupportDomain)
admin.site.register(Engagement)
admin.site.register(Achievement)
admin.site.register(EngagementUrl)
admin.site.register(EngagementDomain)
