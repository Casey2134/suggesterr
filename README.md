# Suggesterr - Movie Recommendation System

A comprehensive Django web application for movie recommendations with AI-powered suggestions and integration with popular media management tools like Jellyfin, Plex, Radarr, and Sonarr.

## Features

- **Movie Database**: Comprehensive movie database synced with The Movie Database (TMDB)
- **AI-Powered Recommendations**: Intelligent movie suggestions using collaborative filtering and OpenAI GPT
- **Genre Browsing**: Browse movies by genres with filters and search functionality
- **Popular Movies**: Display trending and top-rated movies
- **Media Server Integration**: Check movie availability on Jellyfin and Plex
- **Download Management**: Request movies through Radarr and Sonarr
- **User Ratings**: Rate movies and get personalized recommendations
- **Responsive Web Interface**: Modern, mobile-friendly user interface
- **REST API**: Full REST API for all functionality
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (handled by Docker)
- Redis (handled by Docker)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd suggesterr
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and service URLs
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Sync movie data**
   ```bash
   docker-compose exec web python manage.py sync_movies
   ```

7. **Access the application**
   - Web Interface: http://localhost:8000
   - Admin Interface: http://localhost:8000/admin
   - API Documentation: http://localhost:8000/api/

## Local Development

### Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up local database**
   ```bash
   # Start PostgreSQL and Redis with Docker
   docker-compose up db redis
   
   # In another terminal
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Run development server**
   ```bash
   python manage.py runserver
   ```

### Management Commands

- **Sync movies from TMDB**
  ```bash
  python manage.py sync_movies [--genres-only] [--popular-pages=5]
  ```

- **Sync availability from media servers**
  ```bash
  python manage.py sync_availability
  ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=suggesterr
DB_USER=suggesterr
DB_PASSWORD=suggesterr
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
TMDB_API_KEY=your-tmdb-api-key
OPENAI_API_KEY=your-openai-api-key

# External Services
JELLYFIN_URL=http://localhost:8096
JELLYFIN_API_KEY=your-jellyfin-api-key
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your-plex-token
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your-radarr-api-key
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your-sonarr-api-key
```

### API Keys Setup

1. **TMDB API Key**: Sign up at https://www.themoviedb.org/settings/api
2. **OpenAI API Key**: Get from https://platform.openai.com/api-keys
3. **Jellyfin API Key**: Generate in Jellyfin Dashboard > API Keys
4. **Plex Token**: Follow https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
5. **Radarr/Sonarr API Keys**: Found in Settings > General > Security

## API Documentation

### Authentication

The API uses session-based authentication. Most endpoints require authentication.

### Endpoints

- **Movies**
  - `GET /api/movies/` - List movies with filtering
  - `GET /api/movies/{id}/` - Get movie details
  - `GET /api/movies/popular/` - Get popular movies
  - `GET /api/movies/top_rated/` - Get top-rated movies
  - `GET /api/movies/by_genre/?genre=Action` - Get movies by genre
  - `POST /api/movies/{id}/request_movie/` - Request movie on Radarr

- **Genres**
  - `GET /api/genres/` - List all genres

- **User Ratings**
  - `GET /api/ratings/` - Get user's ratings
  - `POST /api/ratings/` - Rate a movie

- **Watchlist**
  - `GET /api/watchlist/` - Get user's watchlist
  - `POST /api/watchlist/` - Add movie to watchlist

- **Recommendations**
  - `GET /api/recommendations/` - Get user's recommendations
  - `POST /api/recommendations/generate/` - Generate new recommendations

### Query Parameters

- `search` - Search movies by title or overview
- `genre` - Filter by genre name
- `available_only` - Show only available movies (true/false)

## Testing

### Run Tests

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Test Structure

- **Model Tests**: Test database models and relationships
- **API Tests**: Test REST API endpoints
- **Service Tests**: Test business logic services
- **Integration Tests**: Test full application flow

## Deployment

### Docker Production

1. **Build production image**
   ```bash
   docker build -t suggesterr:latest .
   ```

2. **Use production docker-compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Manual Deployment

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure settings**
   ```bash
   export DJANGO_SETTINGS_MODULE=suggesterr.settings
   export DEBUG=False
   ```

3. **Run migrations and collect static files**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

4. **Start with Gunicorn**
   ```bash
   gunicorn suggesterr.wsgi:application --bind 0.0.0.0:8000
   ```

## Architecture

### Backend

- **Django**: Web framework
- **Django REST Framework**: API framework
- **PostgreSQL**: Primary database
- **Redis**: Caching and Celery broker
- **Celery**: Background task processing

### Frontend

- **Bootstrap 5**: CSS framework
- **Vanilla JavaScript**: Frontend logic
- **Responsive Design**: Mobile-friendly interface

### External Integrations

- **TMDB**: Movie data and metadata
- **OpenAI**: AI-powered recommendations
- **Jellyfin/Plex**: Media server availability
- **Radarr/Sonarr**: Download management

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use Django best practices
- Write tests for new features
- Document your code

## Troubleshooting

### Common Issues

1. **Database connection error**
   - Check PostgreSQL is running
   - Verify database credentials in `.env`

2. **TMDB API errors**
   - Verify API key is correct
   - Check rate limiting

3. **Media server integration issues**
   - Verify service URLs are accessible
   - Check API keys/tokens are valid

4. **Docker build fails**
   - Ensure Docker has enough memory
   - Check for conflicting port usage

### Logs

```bash
# Docker logs
docker-compose logs web
docker-compose logs db

# Django logs
python manage.py runserver --settings=suggesterr.settings
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The Movie Database (TMDB) for movie data
- OpenAI for AI recommendations
- Django and Django REST Framework communities
- Bootstrap for the UI framework