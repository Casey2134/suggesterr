from django.core.management.base import BaseCommand
from integrations.services import RadarrService


class Command(BaseCommand):
    help = 'Test movie request to Radarr'

    def add_arguments(self, parser):
        parser.add_argument('tmdb_id', type=int, help='TMDB ID to request')
        parser.add_argument('title', type=str, help='Movie title')

    def handle(self, *args, **options):
        radarr = RadarrService()
        
        movie_data = {
            'id': options['tmdb_id'],
            'title': options['title']
        }
        
        self.stdout.write(f"Testing movie request for: {movie_data['title']} (TMDB: {movie_data['id']})")
        
        try:
            result = radarr.request_movie(movie_data)
            
            if result:
                self.stdout.write(
                    self.style.SUCCESS('Movie request successful!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Movie request failed!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'ERROR: {e}')
            )