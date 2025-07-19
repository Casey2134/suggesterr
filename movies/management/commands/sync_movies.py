from django.core.management.base import BaseCommand
from movies.services import MovieService


class Command(BaseCommand):
    help = 'Sync movies and genres from TMDB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--genres-only',
            action='store_true',
            help='Only sync genres',
        )
        parser.add_argument(
            '--popular-pages',
            type=int,
            default=5,
            help='Number of pages of popular movies to sync',
        )

    def handle(self, *args, **options):
        movie_service = MovieService()
        
        self.stdout.write('Starting movie sync...')
        
        # Sync genres first
        self.stdout.write('Syncing genres from TMDB...')
        if movie_service.sync_genres_from_tmdb():
            self.stdout.write(self.style.SUCCESS('Genres synced successfully'))
        else:
            self.stdout.write(self.style.ERROR('Failed to sync genres'))
        
        if not options['genres_only']:
            # Skip movie syncing - movies are now fetched directly from TMDB
            self.stdout.write(self.style.WARNING('Movie syncing disabled - using direct TMDB API calls instead'))
            self.stdout.write('This ensures infinite scroll works correctly without database limitations')
        
        self.stdout.write(self.style.SUCCESS('Movie sync completed'))