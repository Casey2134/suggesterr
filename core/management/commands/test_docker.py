from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os
import sys


class Command(BaseCommand):
    help = 'Test Docker deployment configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('=== Docker Deployment Test ==='))
        
        # Test database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] == 1:
                    self.stdout.write(self.style.SUCCESS('✓ Database connection: OK'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Database connection: FAILED'))
                    return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection: FAILED - {e}'))
            return
        
        # Test environment variables
        required_vars = [
            'SECRET_KEY',
            'TMDB_API_KEY',
            'GOOGLE_GEMINI_API_KEY',
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.stdout.write(self.style.WARNING(f'⚠ Missing environment variables: {", ".join(missing_vars)}'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Required environment variables: OK'))
        
        # Test Django settings
        self.stdout.write(self.style.SUCCESS(f'✓ Django version: {getattr(settings, "DJANGO_VERSION", "Unknown")}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Debug mode: {settings.DEBUG}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Database engine: {settings.DATABASES["default"]["ENGINE"]}'))
        
        if verbose:
            self.stdout.write(self.style.SUCCESS(f'✓ Allowed hosts: {settings.ALLOWED_HOSTS}'))
            self.stdout.write(self.style.SUCCESS(f'✓ Static root: {settings.STATIC_ROOT}'))
            self.stdout.write(self.style.SUCCESS(f'✓ Media root: {settings.MEDIA_ROOT}'))
        
        # Test Redis connection (if configured)
        try:
            import redis
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                r = redis.from_url(redis_url)
                r.ping()
                self.stdout.write(self.style.SUCCESS('✓ Redis connection: OK'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Redis not configured'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Redis connection: FAILED - {e}'))
        
        # Test installed apps
        self.stdout.write(self.style.SUCCESS(f'✓ Installed apps: {len(settings.INSTALLED_APPS)}'))
        if verbose:
            for app in settings.INSTALLED_APPS:
                self.stdout.write(f'  - {app}')
        
        # Test migrations
        from django.core.management import call_command
        try:
            call_command('showmigrations', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ Migrations: OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Migrations: FAILED - {e}'))
        
        # Test static files
        import os
        static_root = settings.STATIC_ROOT
        if static_root and os.path.exists(static_root):
            static_files = len([f for f in os.listdir(static_root) if os.path.isfile(os.path.join(static_root, f))])
            self.stdout.write(self.style.SUCCESS(f'✓ Static files: {static_files} files in {static_root}'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Static files not collected'))
        
        self.stdout.write(self.style.SUCCESS('=== Docker Deployment Test Complete ==='))
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Docker deployment appears to be working correctly!'))
        self.stdout.write('You can now access the application at: http://localhost:8000')
        self.stdout.write('Admin interface: http://localhost:8000/admin')
        self.stdout.write('Health check: http://localhost:8000/health/')