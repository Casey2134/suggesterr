from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis
import os


def health_check(request):
    """
    Health check endpoint for Docker and monitoring systems
    """
    from django.utils import timezone
    
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'protocol': 'https' if request.is_secure() else 'http',
        'host': request.get_host(),
        'services': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['services']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['services']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
    
    # Check Redis connection
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        health_status['services']['redis'] = {
            'status': 'healthy',
            'message': 'Redis connection successful'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['services']['redis'] = {
            'status': 'unhealthy',
            'message': f'Redis connection failed: {str(e)}'
        }
    
    # Check cache
    try:
        cache.set('health_check', 'ok', 30)
        cache_result = cache.get('health_check')
        if cache_result == 'ok':
            health_status['services']['cache'] = {
                'status': 'healthy',
                'message': 'Cache working properly'
            }
        else:
            health_status['status'] = 'unhealthy'
            health_status['services']['cache'] = {
                'status': 'unhealthy',
                'message': 'Cache not working properly'
            }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['services']['cache'] = {
            'status': 'unhealthy',
            'message': f'Cache check failed: {str(e)}'
        }
    
    # Check required environment variables
    required_vars = ['TMDB_API_KEY', 'GOOGLE_GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        health_status['status'] = 'unhealthy'
        health_status['services']['environment'] = {
            'status': 'unhealthy',
            'message': f'Missing required environment variables: {", ".join(missing_vars)}'
        }
    else:
        health_status['services']['environment'] = {
            'status': 'healthy',
            'message': 'All required environment variables present'
        }
    
    # Set HTTP status code based on health
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


def ready_check(request):
    """
    Readiness check for Kubernetes and Docker health checks
    """
    try:
        # Quick database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'ready',
            'message': 'Application is ready to serve requests'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'message': f'Application is not ready: {str(e)}'
        }, status=503)


def liveness_check(request):
    """
    Liveness check for Kubernetes and Docker health checks
    """
    return JsonResponse({
        'status': 'alive',
        'message': 'Application is alive'
    })