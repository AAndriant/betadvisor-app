from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from tickets.models import Ticket
from tickets.serializers import TicketSerializer
from tickets.logic import process_ticket_image

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user).order_by('-created')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Trigger OCR synchronously for MVP
        ticket_instance = serializer.instance
        try:
            process_ticket_image(ticket_instance.id)
            # Refresh to get updated status and bets
            ticket_instance.refresh_from_db()
            
            # Re-serialize with new data
            headers = self.get_success_headers(serializer.data)
            new_serializer = self.get_serializer(ticket_instance)
            return Response(new_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            # If OCR fails, we still return the ticket but maybe with error indication
            # The process_ticket_image handles status update to REJECTED on error
            ticket_instance.refresh_from_db()
            new_serializer = self.get_serializer(ticket_instance)
            return Response(new_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
