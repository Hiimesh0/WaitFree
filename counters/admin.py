from django.contrib import admin
from .models import Counter, OperatorAssignment


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ('number', 'branch', 'service', 'is_open', 'current_operator', 'created_at')
    list_filter = ('is_open', 'branch', 'service')


@admin.register(OperatorAssignment)
class OperatorAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'counter', 'assigned_at')
