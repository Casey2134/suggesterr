from django.core.management.base import BaseCommand
from movies.models import Movie
from integrations.services import JellyfinService, PlexService


class Command(BaseCommand):
    help = 'Sync movie availability from Jellyfin and Plex'

    def handle(self, *args, **options):
        jellyfin_service = JellyfinService()
        plex_service = PlexService()
        
        self.stdout.write('Starting availability sync...')
        
        movies = Movie.objects.all()
        total = movies.count()
        
        for i, movie in enumerate(movies, 1):
            self.stdout.write(f'Checking {i}/{total}: {movie.title}')
            
            # Check Jellyfin availability
            movie.available_on_jellyfin = jellyfin_service.is_movie_available(movie)
            
            # Check Plex availability
            movie.available_on_plex = plex_service.is_movie_available(movie)
            
            movie.save()
        
        self.stdout.write(self.style.SUCCESS('Availability sync completed'))