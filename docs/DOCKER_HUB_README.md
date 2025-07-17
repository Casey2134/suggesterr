# Suggesterr - Movie & TV Recommendation System

🎬 A comprehensive movie and TV show recommendation system built for homelab environments.

## Quick Start

### Using Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: suggesterr
      POSTGRES_USER: suggesterr
      POSTGRES_PASSWORD: your-password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  web:
    image: caseycutshall/suggesterr:latest
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://suggesterr:your-password@db:5432/suggesterr
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=your-secret-key
      - TMDB_API_KEY=your-tmdb-key
      - GOOGLE_GEMINI_API_KEY=your-gemini-key
    ports:
      - "8080:8000"
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media

  celery:
    image: caseycutshall/suggesterr:latest
    command: celery -A suggesterr worker --loglevel=info
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://suggesterr:your-password@db:5432/suggesterr
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=your-secret-key
      - TMDB_API_KEY=your-tmdb-key
      - GOOGLE_GEMINI_API_KEY=your-gemini-key

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

## Features

- 🎬 **Movie & TV Recommendations** - Personalized suggestions
- 👨‍👩‍👧‍👦 **Family Profiles** - Parental controls and content filtering
- 🤖 **AI-Powered** - Google Gemini integration for smart recommendations
- 📱 **Responsive UI** - Modern web interface
- 🔗 **Media Server Integration** - Jellyfin, Plex support
- 📥 **Download Management** - Radarr, Sonarr integration

## Required Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@db:5432/dbname

# Django
SECRET_KEY=your-secret-key
DEBUG=false
ALLOWED_HOSTS=your-server-ip

# External APIs
TMDB_API_KEY=your-tmdb-key
GOOGLE_GEMINI_API_KEY=your-gemini-key
```

## Optional Media Server Integration

```env
# Jellyfin
JELLYFIN_URL=http://jellyfin:8096
JELLYFIN_API_KEY=your-key

# Plex
PLEX_URL=http://plex:32400
PLEX_TOKEN=your-token

# Download Managers
RADARR_URL=http://radarr:7878
RADARR_API_KEY=your-key
SONARR_URL=http://sonarr:8989
SONARR_API_KEY=your-key
```

## Health Checks

The container includes health check endpoints:

- `/health/` - Application health status
- `/ready/` - Readiness probe
- `/live/` - Liveness probe

## Ports

- `8000` - Web application (HTTP)

## Volumes

- `/app/staticfiles` - Static files (CSS, JS, images)
- `/app/media` - User uploaded media files

## API Keys Setup

### TMDB API Key
1. Register at https://www.themoviedb.org/
2. Go to Settings → API
3. Create an API key
4. Add to `TMDB_API_KEY` environment variable

### Google Gemini API Key
1. Go to https://ai.google.dev/
2. Create a project
3. Enable Gemini API
4. Create API key
5. Add to `GOOGLE_GEMINI_API_KEY` environment variable

## Supported Tags

- `latest` - Latest stable release
- `v1.0.0` - Specific version tags
- `main` - Development branch

## Supported Architectures

- `linux/amd64` - x86_64
- `linux/arm64` - ARM64/AArch64

## Security

- Runs as non-root user
- Input validation and sanitization
- CSRF protection
- Rate limiting support
- Security headers

## Links

- **GitHub**: https://github.com/Casey2134/suggesterr
- **Documentation**: https://github.com/Casey2134/suggesterr#readme
- **Issues**: https://github.com/Casey2134/suggesterr/issues

---

**Built with ❤️ for the homelab community**