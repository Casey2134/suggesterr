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
            # Sync popular movies
            self.stdout.write(f'Syncing {options["popular_pages"]} pages of popular movies...')
            if movie_service.sync_popular_movies(pages=options['popular_pages']):
                self.stdout.write(self.style.SUCCESS('Popular movies synced successfully'))
            else:
                self.stdout.write(self.style.ERROR('Failed to sync popular movies'))
        
        self.stdout.write(self.style.SUCCESS('Movie sync completed'))