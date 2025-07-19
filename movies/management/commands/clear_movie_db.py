from django.core.management.base import BaseCommand
from django.db import transaction
from movies.models import Movie


class Command(BaseCommand):
    help = 'Clear all movies from the database to use TMDB-only approach'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the deletion of all movies',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL movies from the database.\n'
                    'Movies will be fetched directly from TMDB instead.\n'
                    'To confirm, run: python manage.py clear_movie_db --confirm'
                )
            )
            return

        movie_count = Movie.objects.count()
        
        if movie_count == 0:
            self.stdout.write(self.style.SUCCESS('No movies found in database - already cleared'))
            return

        self.stdout.write(f'Found {movie_count} movies in database')
        
        try:
            with transaction.atomic():
                Movie.objects.all().delete()
                
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {movie_count} movies from database.\n'
                    'Movies will now be fetched directly from TMDB API.\n'
                    'This should fix any infinite scroll looping issues.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error clearing movies: {e}')
            )