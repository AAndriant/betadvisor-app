"""
Django management command to test result synchronization.

Usage:
    python manage.py sync_results
"""

from django.core.management.base import BaseCommand
from sports.services.result_service import ResultSyncService
from datetime import date


class Command(BaseCommand):
    help = 'Synchronize match results from external source (currently uses mock data)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to sync results for (format: YYYY-MM-DD). Defaults to today.',
        )

    def handle(self, *args, **options):
        # Parse date or use today
        sync_date = date.today()
        if options['date']:
            try:
                sync_date = date.fromisoformat(options['date'])
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f"Invalid date format: {options['date']}. Use YYYY-MM-DD")
                )
                return

        self.stdout.write(
            self.style.SUCCESS(f'Starting result synchronization for {sync_date}...')
        )
        
        # Run the sync service
        service = ResultSyncService()
        stats = service.sync_results_for_date(sync_date)
        
        # Display results
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Synchronization Summary:'))
        self.stdout.write(f"  Total results processed: {stats['total']}")
        self.stdout.write(self.style.SUCCESS(f"  ✓ Successfully updated: {stats['updated']}"))
        
        if stats['failed'] > 0:
            self.stdout.write(self.style.WARNING(f"  ✗ Failed to update: {stats['failed']}"))
            if stats['errors']:
                self.stdout.write('\nErrors:')
                for error in stats['errors']:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))
        
        self.stdout.write('='*60 + '\n')
        
        if stats['updated'] == stats['total']:
            self.stdout.write(
                self.style.SUCCESS('✓ All results synchronized successfully!')
            )
        elif stats['updated'] > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠ Partial success: {stats["updated"]}/{stats["total"]} results synchronized')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ No results were synchronized')
            )
