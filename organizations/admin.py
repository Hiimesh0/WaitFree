from django.contrib import admin
from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'contact_email', 'phone', 'is_active', 'branch_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'contact_email')
    prepopulated_fields = {'slug': ('name',)}
