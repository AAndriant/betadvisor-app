from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, TipsterProfile

class TipsterProfileInline(admin.StackedInline):
    model = TipsterProfile
    can_delete = False
    verbose_name_plural = 'Tipster Profile'

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('is_tipster',)
    inlines = (TipsterProfileInline,)

@admin.register(TipsterProfile)
class TipsterProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('user__username', 'user__email')
