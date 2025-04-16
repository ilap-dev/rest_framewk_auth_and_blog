from django.contrib import admin
from .models import UserAccount
from django.contrib.auth.admin import UserAdmin

class UserAccountAdmin(UserAdmin):
    #Campos a mostrar en la lista de usuarios
    list_display = ("email","username","first_name","last_name",
                    "is_active","is_staff","is_superuser",)
    list_filter=("is_active","is_staff","is_superuser","created_at")
    #Campos a mostrar en el formulario de edicion
    fieldsets = (
        (None, {'fields':('email','username','password')}),
        ('Personal info', {'fields':('first_name','last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'groups','user_permissions')}),
        ('Important Dates', {'fields':('last_login','created_at', 'update_at')}),
    )
    #Campos a mostrar al crear un nuevo usuario
    add_fieldsets = (
        (None, {
            'classes':('wide',),
            'fields': ("email","username","first_name","last_name","password1",
                       "password2","is_active","is_staff","is_superuser",)
        })
    )

    #Campos a buscar de un usuario
    search_fields = ("email","username","first_name","last_name")
    ordering = ("email",)
    readonly_fields = ('created_at', 'update_at')

admin.site.register(UserAccount, UserAccountAdmin)

