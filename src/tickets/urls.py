"""
URL Configuration for Tickets API.

Endpoints:
- POST   /api/tickets/upload/         - Upload and process ticket image (async)
- GET    /api/tickets/<uuid>/status/  - Poll ticket OCR status
- GET    /api/tickets/list/           - List user's tickets (paginated)
"""
from django.urls import path
from .views import TicketUploadView, TicketStatusView, TicketListView


app_name = 'tickets'

urlpatterns = [
    path('upload/', TicketUploadView.as_view(), name='ticket-upload'),
    path('<uuid:pk>/status/', TicketStatusView.as_view(), name='ticket-status'),
    path('list/', TicketListView.as_view(), name='ticket-list'),
]
