from django.core.management.base import BaseCommand
from integrations.services import RadarrService
import requests


class Command(BaseCommand):
    help = 'Test Radarr movie lookup endpoint'

    def add_arguments(self, parser):
        parser.add_argument('tmdb_id', type=int, help='TMDB ID to test')

    def handle(self, *args, **options):
        radarr = RadarrService()
        tmdb_id = options['tmdb_id']
        
        self.stdout.write(f"Testing Radarr movie lookup for TMDB ID: {tmdb_id}")
        
        # Test the lookup endpoint directly
        search_url = f"{radarr.base_url}/api/v3/movie/lookup"
        params = {'term': f"tmdb:{tmdb_id}"}
        
        self.stdout.write(f"URL: {search_url}")
        self.stdout.write(f"Params: {params}")
        self.stdout.write(f"Headers: {radarr.headers}")
        
        try:
            response = requests.get(search_url, headers=radarr.headers, params=params, timeout=10)
            
            self.stdout.write(f"Status Code: {response.status_code}")
            self.stdout.write(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                self.stdout.write(
                    self.style.SUCCESS(f'SUCCESS: Found {len(data)} results')
                )
                if data:
                    self.stdout.write(f"First result: {data[0].get('title', 'Unknown')}")
            else:
                self.stdout.write(
                    self.style.ERROR(f'FAILED: HTTP {response.status_code}')
                )
                self.stdout.write(f"Response: {response.text}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'ERROR: {e}')
            )