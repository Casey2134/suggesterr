# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Suggesterr is a Django-based AI-powered movie and TV show recommendation system with:
- Google Gemini 2.0 Flash integration for intelligent recommendations
- TMDB API for movie/TV show data
- Media server integration (Plex/Jellyfin)
- Download automation (Radarr/Sonarr)
- Field-level encryption for sensitive data
- Production-ready Docker deployment

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with required API keys
```

### Django Commands
```bash
# Database operations
python manage.py migrate
python manage.py makemigrations
python manage.py createsuperuser

# Development server
python manage.py runserver
python manage.py runserver 8080  # Specific port

# Static files (production)
python manage.py collectstatic

# Django shell
python manage.py shell
```

### Custom Management Commands
```bash
# Clear all movie data from database
python manage.py clear_movie_db

# Sync movie data from TMDB
python manage.py sync_movies --popular-pages=5
python manage.py sync_movies --genres-only

# Update availability status from media servers
python manage.py sync_availability

# Test Jellyfin connection
python manage.py test_jellyfin

# Test Docker environment
python manage.py test_docker
```

### Testing
```bash
# Run all tests with pytest
pytest

# Run Django tests
python manage.py test

# Run specific app tests
python manage.py test movies
python manage.py test accounts

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Docker Commands
```bash
# Build and run with docker-compose
docker-compose up -d

# Run commands in container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web

# Build multiplatform image with buildx
docker buildx build --platform linux/amd64,linux/arm64 -f Dockerfile.allinone -t casey073/suggesterr:test --push .
```

## Architecture Overview

### Django Apps Structure

**Core Apps:**
- `core/` - Base functionality, health checks, error handling, middleware
  - Models: Genre
  - Views: Health checks, dashboard, search
  
- `accounts/` - User authentication and encrypted API key storage
  - Models: UserSettings (stores encrypted API keys)
  - Features: Field-level encryption using cryptography.fernet
  
- `movies/` - Movie management with TMDB and AI integration
  - Models: Movie, MovieWatchlist, MovieRecommendation, UserNegativeFeedback
  - Services: TMDBService, GeminiService
  - Custom fields: available_on_jellyfin, available_on_plex
  
- `tv_shows/` - TV show functionality
  - Models: TVShow with season/episode tracking
  - Integration with Sonarr for downloads
  
- `recommendations/` - AI-powered recommendation engine
  - Models: ChatConversation, ChatMessage, PersonalityQuiz, UserProfile
  - Services: ChatService for natural language interactions
  - Maintains conversation context for personalized recommendations
  
- `integrations/` - External service connections
  - Services: JellyfinService, PlexService, RadarrService, SonarrService
  - Handles all media server and download client communications
  
- `smart_recommendations/` - Advanced recommendation features
  - Enhanced recommendation algorithms
  - User preference learning

### Key Services and Integration Points

**External APIs:**
- TMDB API: Primary movie/TV metadata source
- Google Gemini API: AI recommendation engine
- Jellyfin/Plex APIs: Media library availability checking
- Radarr/Sonarr APIs: Download automation

**Security Features:**
- Field-level encryption for API keys in UserSettings model
- CSP headers configured in settings
- Rate limiting on authentication endpoints
- CSRF protection enabled
- Input validation and sanitization

### Database Design
- PostgreSQL in production (with connection pooling)
- SQLite for development
- Redis for caching and session storage
- Encrypted storage for all external service API keys

### Deployment Architecture

**All-in-One Container (`Dockerfile.allinone`):**
- Includes PostgreSQL, Redis, Nginx, and Django
- Supervisor manages all processes
- Self-contained deployment suitable for home servers

**Standard Container (`Dockerfile`):**
- Python 3.11-slim base
- Gunicorn WSGI server
- Requires external PostgreSQL and Redis

## Environment Variables

Required:
```env
SECRET_KEY=django-secret-key
TMDB_API_KEY=your-tmdb-api-key
GOOGLE_GEMINI_API_KEY=your-gemini-api-key
```

Optional integrations:
```env
JELLYFIN_URL=http://jellyfin:8096
JELLYFIN_API_KEY=your-key
PLEX_URL=http://plex:32400
PLEX_TOKEN=your-token
RADARR_URL=http://radarr:7878
RADARR_API_KEY=your-key
SONARR_URL=http://sonarr:8989
SONARR_API_KEY=your-key
```

## API Endpoints

Authentication:
- POST `/accounts/login/`
- POST `/accounts/register/`
- POST `/accounts/logout/`

Movies:
- GET `/api/movies/` - List movies with search
- GET `/api/movies/{id}/` - Movie details
- GET `/api/movies/ai_recommendations/` - AI recommendations
- POST `/api/movies/{id}/request_movie/` - Request via Radarr

TV Shows:
- GET `/api/tv-shows/` - List TV shows
- GET `/api/tv-shows/ai_recommendations/` - AI recommendations
- POST `/api/tv-shows/{id}/request_tv_show/` - Request via Sonarr

Chat:
- POST `/api/chat/message/` - Send chat message
- GET `/api/chat/history/` - Get conversation history

## Testing Configuration

Tests use pytest (configured in `pytest.ini`):
- Test paths: `movies/`, `integrations/`
- Django settings module: `suggesterr.settings`
- Run with verbose output and short traceback

## Background Tasks

Celery is configured for background task processing:
- Broker: Redis
- Task autodiscovery enabled
- Used for long-running operations like media server syncs

## Key Implementation Details

1. **AI Recommendations**: The GeminiService considers user's existing media library when making recommendations, avoiding suggesting content already available.

2. **Encryption**: API keys are encrypted at rest using Fernet symmetric encryption. The encryption key is generated from Django's SECRET_KEY.

3. **Media Server Integration**: Availability checking happens in real-time for each request, not cached, to ensure accuracy.

4. **TMDB Sync**: The sync_movies command can operate in "genres-only" mode or sync popular movies. Direct API calls are preferred over database storage for infinite scroll functionality.

5. **Health Checks**: Available at `/health/` endpoint, used by Docker and monitoring systems.

6. **Static Files**: Collected to `/config/static` in production, served by Nginx in the all-in-one container.