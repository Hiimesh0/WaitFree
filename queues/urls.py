from django.urls import path
from . import views

app_name = 'queues'

urlpatterns = [
    path('join/', views.JoinQueueView.as_view(), name='join_queue'),
    path('ticket/<int:ticket_id>/', views.QueueTicketView.as_view(), name='ticket'),
    path('overview/<int:service_id>/', views.QueueOverviewView.as_view(), name='overview'),
    path('my-tickets/', views.MyTicketsView.as_view(), name='my_tickets'),
    path('serve-next/', views.ServeNextView.as_view(), name='serve_next'),
    path('no-show/', views.MarkNoShowView.as_view(), name='mark_no_show'),
]
