from django.core.management.base import BaseCommand
from integrations.services import JellyfinService
from accounts.models import UserSettings
from django.contrib.auth.models import User
import logging

class Command(BaseCommand):
    help = 'Test Jellyfin connection and library loading'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to test (uses their Jellyfin settings)',
        )
        parser.add_argument(
            '--url',
            type=str,
            help='Jellyfin URL to test',
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='Jellyfin API key to test',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Limit number of movies to fetch for testing',
        )

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        
        # Configure logging to show more details
        logging.basicConfig(level=logging.INFO)
        
        jellyfin = JellyfinService()
        
        # Determine configuration source
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                user_settings = UserSettings.objects.get(user=user)
                
                if user_settings.server_type != 'jellyfin':
                    self.stdout.write(
                        self.style.ERROR(f'User {user.username} does not have Jellyfin configured')
                    )
                    return
                
                jellyfin.configure(user_settings.server_url, user_settings.server_api_key)
                self.stdout.write(f'Testing Jellyfin for user: {user.username}')
                self.stdout.write(f'URL: {user_settings.server_url}')
                
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {options["user_id"]} not found'))
                return
            except UserSettings.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User settings not found for user ID {options["user_id"]}'))
                return
                
        elif options['url'] and options['api_key']:
            jellyfin.configure(options['url'], options['api_key'])
            self.stdout.write(f'Testing Jellyfin with provided credentials')
            self.stdout.write(f'URL: {options["url"]}')
            
        else:
            self.stdout.write(self.style.ERROR('Must provide either --user-id or both --url and --api-key'))
            return

        # Test connection
        self.stdout.write('\n=== Testing Connection ===')
        success, message = jellyfin.test_connection()
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'✓ Connection successful: {message}'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ Connection failed: {message}'))
            return

        # Test library stats
        self.stdout.write('\n=== Testing Library Stats ===')
        try:
            stats = jellyfin.get_library_stats()
            if stats:
                self.stdout.write(self.style.SUCCESS(f'✓ Library stats retrieved:'))
                for key, value in stats.items():
                    self.stdout.write(f'  {key}: {value}')
            else:
                self.stdout.write(self.style.WARNING('⚠ No library stats returned'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Library stats failed: {e}'))

        # Test library movies
        self.stdout.write(f'\n=== Testing Library Movies (limit: {options["limit"]}) ===')
        try:
            movies = jellyfin.get_library_movies(limit=options['limit'])
            if movies:
                self.stdout.write(self.style.SUCCESS(f'✓ Retrieved {len(movies)} movies:'))
                for i, movie in enumerate(movies[:5]):  # Show first 5
                    self.stdout.write(f'  {i+1}. {movie.get("title", "Unknown")} ({movie.get("year", "Unknown")})')
                if len(movies) > 5:
                    self.stdout.write(f'  ... and {len(movies) - 5} more')
            else:
                self.stdout.write(self.style.WARNING('⚠ No movies returned from library'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Library movies failed: {e}'))

        self.stdout.write('\n=== Test Complete ===')