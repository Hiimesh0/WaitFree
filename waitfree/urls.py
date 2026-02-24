"""
Root URL configuration for WaitFree.
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render


def landing_page(request):
    return render(request, 'pages/landing.html')


def about_page(request):
    return render(request, 'pages/about.html')


urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Global pages
    path('', landing_page, name='landing'),
    path('about/', about_page, name='about'),

    # App URLs
    path('accounts/', include('accounts.urls')),
    path('organizations/', include('organizations.urls')),
    path('facilities/', include('facilities.urls')),
    path('counters/', include('counters.urls')),
    path('queues/', include('queues.urls')),
    path('notifications/', include('notifications.urls')),
    path('dashboard/', include('dashboard.urls')),
]
