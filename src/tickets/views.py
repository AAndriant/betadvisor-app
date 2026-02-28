"""
Production-ready API Views for Ticket Upload & Listing.
Includes asynchronous OCR processing with threading and status polling.
"""
import threading
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
import logging

from .models import Ticket
from .serializers import TicketUploadSerializer, TicketStatusSerializer, TicketListSerializer
from .logic import process_ticket_image


logger = logging.getLogger(__name__)


class TicketPagination(PageNumberPagination):
    """
    Custom pagination for ticket list.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class TicketUploadView(generics.CreateAPIView):
    """
    API endpoint for uploading betting ticket images (Async).
    
    Workflow:
    1. Validate image (format, size)
    2. Create ticket in database with PENDING_OCR status
    3. Launch OCR in background thread (non-blocking)
    4. Return 202 Accepted with status_url for polling
    
    Security:
    - Requires JWT authentication
    - User isolation (tickets linked to request.user)
    - File validation (format, size limits)
    
    Response:
    - 202 Accepted (ticket created, OCR processing in background)
    - Returns status_url for mobile to poll completion
    """
    queryset = Ticket.objects.all()
    serializer_class = TicketUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request, *args, **kwargs):
        """
        Handle async ticket upload.
        
        OCR processing happens in background thread, 
        allowing immediate response to mobile client.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 1. Save ticket immediately with PENDING_OCR status
        ticket = serializer.save(
            user=request.user,
            status=Ticket.Status.PENDING_OCR
        )
        
        logger.info(f"Ticket {ticket.id} created for user {request.user.id}")
        
        # 2. Launch OCR in background thread (daemon=True for cleanup)
        # Pass ticket ID, not object, to avoid shared memory issues
        thread = threading.Thread(
            target=process_ticket_image,
            args=(ticket.id,),
            daemon=True
        )
        thread.start()
        
        logger.info(f"OCR thread started for ticket {ticket.id}")
        
        # 3. Return 202 Accepted immediately
        # Mobile will poll status_url to check completion
        response_serializer = self.get_serializer(ticket)
        return Response(
            response_serializer.data,
            status=status.HTTP_202_ACCEPTED
        )


class TicketStatusView(generics.RetrieveAPIView):
    """
    API endpoint for polling ticket OCR status.
    
    Mobile calls this endpoint to check if OCR processing is complete.
    
    Features:
    - User isolation (only returns tickets owned by authenticated user)
    - Optimized queries (select_related, prefetch_related)
    - Returns bet_selections when OCR is complete
    
    Response:
    - 200 OK with current ticket status and bet selections
    - 404 if ticket doesn't exist or doesn't belong to user
    """
    serializer_class = TicketStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Returns tickets for authenticated user only.
        Optimized with related data prefetching.
        """
        return Ticket.objects.filter(
            user=self.request.user
        ).select_related(
            'user'
        ).prefetch_related(
            'selections',
            'selections__match'
        )


class TicketListView(generics.ListAPIView):
    """
    API endpoint for listing user's tickets.
    
    Features:
    - User isolation (only shows authenticated user's tickets)
    - Pagination (10 items per page, configurable)
    - Sorted by creation date (newest first)
    - Lightweight response (thumbnail + ROI, no full data)
    
    Security:
    - Requires authentication
    - Strict user filtering
    """
    serializer_class = TicketListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TicketPagination
    
    def get_queryset(self):
        """
        Returns tickets for authenticated user only.
        Ordered by creation date (newest first).
        """
        return Ticket.objects.filter(
            user=self.request.user
        ).select_related(
            # Optimize query - avoid N+1
        ).prefetch_related(
            'selections',  # For ROI calculation
            'selections__match'
        ).order_by('-created')