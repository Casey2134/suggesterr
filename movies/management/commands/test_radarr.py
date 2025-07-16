from django.core.management.base import BaseCommand
from integrations.services import RadarrService


class Command(BaseCommand):
    help = 'Test Radarr API connection'

    def handle(self, *args, **options):
        radarr = RadarrService()
        
        self.stdout.write(f"Testing Radarr connection...")
        self.stdout.write(f"URL: {radarr.base_url}")
        self.stdout.write(f"API Key: {'*' * (len(radarr.api_key) - 4) + radarr.api_key[-4:] if radarr.api_key else 'None'}")
        
        success, message = radarr.test_connection()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'SUCCESS: {message}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'FAILED: {message}')
            )