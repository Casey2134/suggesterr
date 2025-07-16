# 🎬 Suggesterr - AI-Powered Movie Recommendation System

A comprehensive Django web application for intelligent movie and TV show recommendations with advanced AI-powered suggestions and seamless integration with popular media management tools like Jellyfin, Plex, Radarr, and Sonarr.

## ✨ Key Features

### 🤖 Advanced AI Recommendations
- **Google Gemini Integration**: State-of-the-art AI recommendations using Google's Gemini 2.0 Flash model
- **OpenAI GPT Integration**: Alternative AI engine for intelligent movie suggestions
- **Library-Aware AI**: Smart recommendations that consider your existing Plex/Jellyfin library
- **Mood-Based Suggestions**: Get recommendations based on your current mood (happy, sad, excited, etc.)
- **Similar Movie Discovery**: Find movies similar to ones you love
- **Collaborative Filtering**: Personalized suggestions based on user ratings and preferences

### 📚 Smart Library Integration
- **Library Context Awareness**: AI avoids recommending movies you already own
- **Collection Complementing**: Suggestions that fill gaps in your existing library
- **Plex & Jellyfin Support**: Seamless integration with your media servers
- **Real-Time Availability**: Check movie availability across your media libraries

### 🎭 Comprehensive Media Management
- **Movie & TV Show Database**: Complete database synced with The Movie Database (TMDB)
- **Download Automation**: Request movies/shows through Radarr and Sonarr
- **User Ratings & Watchlists**: Rate content and maintain personal watchlists
- **Genre Discovery**: Browse by genres with advanced filtering
- **Popular & Trending**: Stay updated with trending and top-rated content

### 🔧 Technical Excellence
- **Modern REST API**: Comprehensive API for all functionality
- **Responsive Web Interface**: Mobile-friendly, modern UI with Bootstrap 5
- **Docker Ready**: Easy deployment with Docker and Docker Compose
- **Background Processing**: Celery integration for heavy tasks
- **Comprehensive Testing**: Full test suite with API and integration tests

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

# API Keys (Required)
TMDB_API_KEY=your-tmdb-api-key

# AI Services (Choose one or both)
OPENAI_API_KEY=your-openai-api-key          # Optional: For OpenAI GPT recommendations
GOOGLE_GEMINI_API_KEY=your-gemini-api-key   # Optional: For Google Gemini recommendations (primary)

# Media Server Integration (Optional - for library context)
JELLYFIN_URL=http://localhost:8096
JELLYFIN_API_KEY=your-jellyfin-api-key
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your-plex-token

# Download Management (Optional)
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your-radarr-api-key
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your-sonarr-api-key
```

### API Keys Setup

#### Required
1. **TMDB API Key**: Sign up at https://www.themoviedb.org/settings/api

#### AI Services (Choose one or both)
2. **Google Gemini API Key**: Get from https://ai.google.dev/ (Recommended - Primary AI engine)
3. **OpenAI API Key**: Get from https://platform.openai.com/api-keys (Alternative AI engine)

#### Media Server Integration (Optional - Enables Library Context)
4. **Jellyfin API Key**: Generate in Jellyfin Dashboard > API Keys
5. **Plex Token**: Follow https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

#### Download Management (Optional)
6. **Radarr/Sonarr API Keys**: Found in Settings > General > Security

### 🚀 Library Context Feature

To enable smart library-aware recommendations:

1. **Configure your media server** in User Settings:
   - Choose either Jellyfin or Plex
   - Enter your server URL and API key/token
   - Save settings

2. **Benefits of Library Context**:
   - AI won't recommend movies you already own
   - Suggestions complement your existing collection
   - Recommendations fill gaps in similar genres/themes
   - Works automatically once configured

## API Documentation

### Authentication

The API uses session-based authentication. Most endpoints require authentication.

### Endpoints

#### 🎬 Movies
- `GET /api/movies/` - List movies with filtering
- `GET /api/movies/{id}/` - Get movie details
- `GET /api/movies/popular/` - Get popular movies
- `GET /api/movies/top_rated/` - Get top-rated movies
- `GET /api/movies/by_genre/?genre_id=28` - Get movies by genre ID
- `POST /api/movies/{id}/request_movie/` - Request movie on Radarr

#### 🤖 AI Recommendations (New!)
- `GET /api/movies/ai_recommendations/` - AI-powered personalized recommendations
  - Parameters: `genres`, `mood`, `year_range`
  - **Library-aware**: Automatically considers your Plex/Jellyfin library
- `GET /api/movies/mood_recommendations/` - Mood-based recommendations
  - Parameters: `mood` (happy, sad, excited, relaxed, romantic, adventurous, thoughtful, nostalgic)
- `GET /api/movies/similar_movies/` - Find similar movies
  - Parameters: `title` (movie title to find similar movies for)

#### 📺 TV Shows
- `GET /api/tv-shows/` - List TV shows with filtering
- `GET /api/tv-shows/{id}/` - Get TV show details
- `GET /api/tv-shows/popular/` - Get popular TV shows
- `GET /api/tv-shows/ai_recommendations/` - AI-powered TV recommendations
- `GET /api/tv-shows/mood_recommendations/` - Mood-based TV recommendations
- `POST /api/tv-shows/{id}/request_tv_show/` - Request TV show on Sonarr

#### 🎭 Genres
- `GET /api/genres/` - List all genres

#### ⭐ User Ratings
- `GET /api/ratings/` - Get user's ratings
- `POST /api/ratings/` - Rate a movie

#### 📋 Watchlist
- `GET /api/watchlist/` - Get user's watchlist
- `POST /api/watchlist/` - Add movie to watchlist

#### 🎯 Recommendations
- `GET /api/recommendations/` - Get user's recommendations
- `POST /api/recommendations/generate/` - Generate new recommendations (with library context)

#### ⚙️ User Settings
- `GET /api/settings/` - Get user settings (including media server config)
- `POST /api/settings/` - Update user settings

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

- **TMDB**: Comprehensive movie and TV show data
- **Google Gemini**: Primary AI engine for intelligent recommendations
- **OpenAI GPT**: Alternative AI engine for recommendations  
- **Jellyfin/Plex**: Media server integration with library context awareness
- **Radarr/Sonarr**: Automated download management

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