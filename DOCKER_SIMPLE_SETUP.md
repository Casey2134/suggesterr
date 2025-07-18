# 🐳 Simple Docker Setup (Like Radarr/Sonarr)

## Quick Start

Just like other *arr applications, Suggesterr can now be deployed with a single Docker container!

### 1. Create docker-compose.yml

```yaml
services:
  suggesterr:
    image: suggesterr:latest  # or build from source
    container_name: suggesterr
    environment:
      # Required API Keys - Get these from:
      # TMDB: https://www.themoviedb.org/settings/api
      # Gemini: https://ai.google.dev/
      - TMDB_API_KEY=your-tmdb-api-key
      - GOOGLE_GEMINI_API_KEY=your-gemini-api-key
      
      # Optional - Admin user (created automatically on first run)
      - DJANGO_SUPERUSER_USERNAME=admin
      - DJANGO_SUPERUSER_PASSWORD=admin123
      - DJANGO_SUPERUSER_EMAIL=admin@suggesterr.local
      
      # Optional - Media server integration
      - JELLYFIN_URL=http://your-jellyfin-server:8096
      - JELLYFIN_API_KEY=your-jellyfin-api-key
      - PLEX_URL=http://your-plex-server:32400
      - PLEX_TOKEN=your-plex-token
      
      # Optional - Download management
      - RADARR_URL=http://your-radarr-server:7878
      - RADARR_API_KEY=your-radarr-api-key
      - SONARR_URL=http://your-sonarr-server:8989
      - SONARR_API_KEY=your-sonarr-api-key
      
      - TZ=Etc/UTC
    volumes:
      - /path/to/suggesterr/config:/config
    ports:
      - 8000:8000
    restart: unless-stopped
```

### 2. Get Required API Keys

**TMDB API Key (Required)**
1. Go to https://www.themoviedb.org/settings/api
2. Create account and request API key
3. Copy the API key

**Google Gemini API Key (Required)**
1. Go to https://ai.google.dev/
2. Get API key for Gemini
3. Copy the API key

### 3. Update docker-compose.yml

Replace the placeholder values:
- `your-tmdb-api-key` → Your actual TMDB API key
- `your-gemini-api-key` → Your actual Gemini API key
- `/path/to/suggesterr/config` → Local path for persistent data

### 4. Start the Container

```bash
# Start the container
docker-compose up -d

# Check logs
docker-compose logs -f suggesterr
```

### 5. Access Suggesterr

- **Web Interface**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Login**: admin / admin123 (or your custom credentials)

## What's Included

This single container includes:
- ✅ **Django Web Application**
- ✅ **PostgreSQL Database**
- ✅ **Redis Cache**
- ✅ **Nginx Reverse Proxy**
- ✅ **Celery Background Tasks**
- ✅ **Automatic Database Setup**
- ✅ **Security Headers & Rate Limiting**
- ✅ **Health Checks**

## Volume Structure

The `/config` volume contains:
```
/config/
├── database/     # PostgreSQL data
├── logs/         # Application logs
├── media/        # User uploaded files
└── static/       # Static web files
```

## Optional Configuration

### Media Server Integration

Add your media server details to automatically check what movies you already have:

```yaml
# For Jellyfin
- JELLYFIN_URL=http://192.168.1.100:8096
- JELLYFIN_API_KEY=your-jellyfin-api-key

# For Plex
- PLEX_URL=http://192.168.1.100:32400
- PLEX_TOKEN=your-plex-token
```

### Download Automation

Connect to Radarr/Sonarr for automatic downloads:

```yaml
# For Radarr (Movies)
- RADARR_URL=http://192.168.1.100:7878
- RADARR_API_KEY=your-radarr-api-key

# For Sonarr (TV Shows)
- SONARR_URL=http://192.168.1.100:8989
- SONARR_API_KEY=your-sonarr-api-key
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `TMDB_API_KEY` | ✅ | TMDB API key for movie data |
| `GOOGLE_GEMINI_API_KEY` | ✅ | Google Gemini API key for AI features |
| `DJANGO_SUPERUSER_USERNAME` | ❌ | Admin username (default: admin) |
| `DJANGO_SUPERUSER_PASSWORD` | ❌ | Admin password (default: admin123) |
| `DJANGO_SUPERUSER_EMAIL` | ❌ | Admin email |
| `JELLYFIN_URL` | ❌ | Jellyfin server URL |
| `JELLYFIN_API_KEY` | ❌ | Jellyfin API key |
| `PLEX_URL` | ❌ | Plex server URL |
| `PLEX_TOKEN` | ❌ | Plex authentication token |
| `RADARR_URL` | ❌ | Radarr server URL |
| `RADARR_API_KEY` | ❌ | Radarr API key |
| `SONARR_URL` | ❌ | Sonarr server URL |
| `SONARR_API_KEY` | ❌ | Sonarr API key |
| `TZ` | ❌ | Timezone (default: Etc/UTC) |

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs suggesterr

# Common issues:
# - Missing required API keys
# - Port 8000 already in use
# - Volume permissions
```

### Can't access web interface
```bash
# Check if container is running
docker-compose ps

# Check port mapping
netstat -tulpn | grep 8000
```

### Database issues
```bash
# Restart container to reinitialize
docker-compose down
docker-compose up -d
```

## Updating

```bash
# Pull latest image
docker-compose pull

# Restart container
docker-compose down && docker-compose up -d
```

## Building from Source

If you want to build from source instead of using a pre-built image:

```bash
# Clone repository
git clone <repository-url>
cd suggesterr

# Update docker-compose.yml to build instead of pull
services:
  suggesterr:
    build:
      context: .
      dockerfile: Dockerfile.allinone
    # ... rest of config
```

That's it! Your Suggesterr instance will be running with all services included in a single container, just like Radarr, Sonarr, and other *arr applications.