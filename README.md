# 🎬 Suggesterr - AI-Powered Movie Recommendation System

A secure, production-ready Django web application for intelligent movie and TV show recommendations with advanced AI-powered suggestions and seamless integration with popular media management tools.

## ✨ Features

### 🔒 **Security First**
- **Field-level encryption** for sensitive user data (API keys)
- **Rate limiting** on authentication and API endpoints
- **Content Security Policy** and comprehensive security headers
- **Input validation** and sanitization to prevent XSS/injection attacks
- **Secure error handling** that prevents information disclosure
- **HTTPS/SSL ready** with proper security configurations

### 🤖 **AI-Powered Recommendations**
- **Google Gemini 2.0 Flash** integration for intelligent recommendations
- **Library-aware AI** that considers your existing Plex/Jellyfin collection
- **Mood-based suggestions** and personalized recommendations
- **Chat-based interface** for natural language movie discovery

### 📚 **Media Management Integration**
- **Plex & Jellyfin** support with encrypted API key storage
- **Radarr & Sonarr** integration for automated downloads
- **TMDB integration** for comprehensive movie/TV show database
- **Real-time availability** checking across your media libraries

### 🛡️ **Production Ready**
- **Docker containerized** with secure multi-stage builds
- **PostgreSQL** support with connection pooling
- **Redis** caching and session management
- **Nginx** reverse proxy with security headers
- **Comprehensive logging** and error monitoring

## 🚀 Quick Start (Simple Docker Setup)

### Easy Single-Container Deployment (Like Radarr/Sonarr)

```yaml
# docker-compose.yml
services:
  suggesterr:
    image: casey073/suggesterr:latest
    container_name: suggesterr
    environment:
      # Required API Keys - Get these from:
      # TMDB: https://www.themoviedb.org/settings/api
      # Gemini: https://ai.google.dev/
      - TMDB_API_KEY=your-tmdb-api-key
      - GOOGLE_GEMINI_API_KEY=your-gemini-api-key
      
      # Security settings - Add your server IP/domain here
      - ALLOWED_HOSTS=localhost,127.0.0.1,your-server-ip,your-domain.com
      - FORCE_SSL=False
      - DEBUG=True
      
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

### Get Required API Keys

1. **TMDB API Key**: https://www.themoviedb.org/settings/api
2. **Google Gemini API Key**: https://ai.google.dev/

### Deploy

```bash
# Start container
docker-compose up -d

# Access at http://localhost:8000
```

**That's it!** Everything (database, cache, web server) is included in one container.

### Configuration Notes

- **ALLOWED_HOSTS**: Add your server's IP address and domain name
- **FORCE_SSL**: Set to `True` in production with proper SSL certificates
- **DEBUG**: Set to `False` in production
- **CSRF_TRUSTED_ORIGINS**: Add if using reverse proxies or non-standard ports

The container automatically:
- Creates the database and runs migrations
- Sets up the admin user (if credentials provided)
- Syncs movie data from TMDB (if API key provided)
- Starts all required services (PostgreSQL, Redis, Nginx, Django)

---


## 📋 API Documentation

### Authentication Endpoints
- `POST /accounts/login/` - User login
- `POST /accounts/register/` - User registration
- `POST /accounts/logout/` - User logout

### Movie Endpoints
- `GET /api/movies/` - List movies
- `GET /api/movies/{id}/` - Movie details
- `GET /api/movies/ai_recommendations/` - AI recommendations
- `POST /api/movies/{id}/request_movie/` - Request on Radarr

### TV Show Endpoints
- `GET /api/tv-shows/` - List TV shows
- `GET /api/tv-shows/ai_recommendations/` - AI recommendations
- `POST /api/tv-shows/{id}/request_tv_show/` - Request on Sonarr

### Chat Endpoints
- `POST /api/chat/message/` - Send chat message
- `GET /api/chat/history/` - Get chat history

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all security checks pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- TMDB for movie data
- Google Gemini for AI capabilities
- Django and DRF communities
- Security research community

---

**⚠️ Security Note**: This application has been security hardened and is ready for production deployment. Always keep dependencies updated and monitor security advisories.
