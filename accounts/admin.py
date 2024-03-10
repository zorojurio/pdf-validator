from django.contrib import admin
from .models import CustomUser, SignerUser, ValidatorUser


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "user_type"]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(SignerUser)
admin.site.register(ValidatorUser)
