from django.contrib import admin
from .models import UserAccount
from django.contrib.auth.admin import UserAdmin

class UserAccountAdmin(UserAdmin):
    list_display = ("email", "username", "first_name", "last_name",
                    "is_active", "is_staff", "is_superuser", 'role', 'verified',)
    list_filter = ("is_active", "is_staff", "is_superuser", "created_at",)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password', 'verified', 'role',)}),
        ('Personal info', {'fields': ('first_name', 'last_name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',)}),
        ('Important Dates', {'fields': ('last_login', 'created_at', 'updated_at',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ("email", "username", "first_name", "last_name", 'role', 'verified', "password1", "password2", "is_active", "is_staff", "is_superuser"),
        }),
    )
    search_fields = ("email", "username", "first_name", "last_name",)
    ordering = ("email",)
    readonly_fields = ('created_at', 'updated_at',)
    list_editable = ('role', 'verified',)

admin.site.register(UserAccount, UserAccountAdmin)


