from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.CitizenNotificationsView.as_view(), name='citizen_notifications'),
]
