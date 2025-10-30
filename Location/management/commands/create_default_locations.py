"""
Management command to create default locations for testing
"""
from django.core.management.base import BaseCommand
from Location.models import Location

class Command(BaseCommand):
    help = 'Create default locations for testing'

    def handle(self, *args, **options):
        default_locations = [
            {'name': 'Main Campus', 'description': 'Primary campus building'},
            {'name': 'Library', 'description': 'Central library building'},
            {'name': 'Cafeteria', 'description': 'Main dining area'},
            {'name': 'Parking Lot A', 'description': 'Student parking area'},
            {'name': 'Gym', 'description': 'Sports and fitness center'},
            {'name': 'Lab Building', 'description': 'Science and computer labs'},
        ]

        for loc_data in default_locations:
            location, created = Location.objects.get_or_create(
                name=loc_data['name'],
                defaults={'description': loc_data['description']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created location: {location.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Location already exists: {location.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Default locations setup complete!')
        )