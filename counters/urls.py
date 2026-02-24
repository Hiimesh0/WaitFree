from django.urls import path
from . import views

app_name = 'counters'

urlpatterns = [
    path('operator/dashboard/', views.OperatorDashboardView.as_view(), name='operator_dashboard'),
    path('operator/control/', views.CounterControlView.as_view(), name='toggle_counter'),
]
