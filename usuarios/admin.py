from django.contrib import admin
from .models import CustomUser, Funcionario
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('email', 'is_staff', 'is_active')
    list_filter = ('is_active', 'is_staff', 'groups')
    ordering = ('email',)
    search_fields = ('email',)

    readonly_fields = ('date_joined', 'last_login')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.username:
            obj.username = obj.email
        obj.save()

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'apellido', 'numero_identificacion',
        'correo_electronico', 'estamento', 'facultad_dependencia', 'sede'
    )
    search_fields = ('nombre', 'apellido', 'numero_identificacion', 'user__email')
    list_filter = ('estamento', 'facultad_dependencia', 'sede')
