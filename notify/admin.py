from django.contrib import admin

from . import models

admin.site.register(models.History)
admin.site.register(models.UserPreferences)
admin.site.register(models.Location)
