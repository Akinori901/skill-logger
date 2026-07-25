from django.contrib import admin

from apps.generation.infrastructure.models import AiConfig, AiGenerationLog, DomainStatement

admin.site.register(AiConfig)
admin.site.register(DomainStatement)
admin.site.register(AiGenerationLog)
