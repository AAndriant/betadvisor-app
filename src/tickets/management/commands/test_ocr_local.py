import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.contrib.auth import get_user_model
from tickets.models import Ticket
from tickets.logic import process_ticket_image

class Command(BaseCommand):
    help = 'Test OCR pipeline with a local image file'

    def add_arguments(self, parser):
        parser.add_argument('image_path', type=str, help='Path to the image file')

    def handle(self, *args, **options):
        image_path = options['image_path']
        
        if not os.path.exists(image_path):
            self.stdout.write(self.style.ERROR(f"Image not found: {image_path}"))
            return

        User = get_user_model()
        # Ensure we have a user
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found. Please run init_project.sh first."))
            return

        self.stdout.write(f"Creating test ticket with image: {image_path}")
        
        # Create a ticket
        with open(image_path, 'rb') as f:
            ticket = Ticket.objects.create(
                user=user,
                status=Ticket.Status.PENDING_OCR
            )
            # Save the image to the field
            ticket.image.save(os.path.basename(image_path), File(f))
            ticket.save()

        self.stdout.write(f"Ticket created: {ticket.id}")
        self.stdout.write("Starting OCR processing...")

        process_ticket_image(ticket.id)

        # Refresh from DB
        ticket.refresh_from_db()
        
        self.stdout.write("-" * 30)
        self.stdout.write(f"Final Status: {ticket.status}")
        self.stdout.write(f"Raw Data: {ticket.ocr_raw_data}")
        self.stdout.write("Bet Selections:")
        for selection in ticket.selections.all():
            self.stdout.write(f" - {selection}")
        self.stdout.write("-" * 30)
