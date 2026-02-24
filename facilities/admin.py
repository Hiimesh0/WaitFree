from django.contrib import admin
from .models import Branch, Service


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'city', 'is_active', 'created_at')
    list_filter = ('is_active', 'organization')
    search_fields = ('name', 'city')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'avg_service_time', 'is_active')
    list_filter = ('is_active', 'branch__organization')
    search_fields = ('name',)
