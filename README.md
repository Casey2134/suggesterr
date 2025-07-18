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
    image: suggesterr:latest
    container_name: suggesterr
    environment:
      # Required API Keys
      - TMDB_API_KEY=your-tmdb-api-key
      - GOOGLE_GEMINI_API_KEY=your-gemini-api-key
      
      # Optional - Admin user
      - DJANGO_SUPERUSER_USERNAME=admin
      - DJANGO_SUPERUSER_PASSWORD=admin123
      - DJANGO_SUPERUSER_EMAIL=admin@suggesterr.local
      
      # Optional - Media server integration
      - JELLYFIN_URL=http://your-jellyfin:8096
      - JELLYFIN_API_KEY=your-jellyfin-key
      
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

See [DOCKER_SIMPLE_SETUP.md](DOCKER_SIMPLE_SETUP.md) for detailed instructions.

---

## 🏢 Advanced Production Setup

For advanced multi-container production deployments with separate database servers:

### Prerequisites

- Docker and Docker Compose
- Domain name (for production SSL)
- Required API keys (see configuration section)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd suggesterr
cp .env.example .env
```

### 2. Deploy with Docker

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Sync movie data
docker-compose -f docker-compose.prod.yml exec web python manage.py sync_movies
```

## 🔧 Configuration

### Required API Keys

1. **TMDB API Key** 
   - Sign up at https://www.themoviedb.org/settings/api
   - Free tier available

2. **Google Gemini API Key**
   - Get from https://ai.google.dev/
   - Required for AI recommendations

### Optional Integrations

3. **Jellyfin API Key**
   - Dashboard → API Keys → Add API Key

4. **Plex Token**
   - Follow: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

5. **Radarr/Sonarr API Keys**
   - Settings → General → Security → API Key

### Security Configuration

The application includes comprehensive security measures:

- **Rate Limiting**: 5 login attempts/min, 100 API requests/min
- **Content Security Policy**: Prevents XSS attacks
- **HSTS**: Enforces HTTPS connections
- **Secure Cookies**: HttpOnly and Secure flags enabled
- **Input Validation**: All user input is sanitized
- **Error Handling**: Prevents information disclosure

## 📊 Architecture

### Backend Stack
- **Django 4.2** - Web framework
- **Django REST Framework** - API
- **PostgreSQL** - Database
- **Redis** - Caching/Sessions
- **Celery** - Background tasks

### Security Features
- **Field-level encryption** for API keys
- **Rate limiting** with django-ratelimit
- **CSP** with django-csp
- **Input sanitization** and validation
- **Secure error handling**

### Infrastructure
- **Docker** containerization
- **Nginx** reverse proxy
- **SSL/TLS** termination
- **Security headers**

## 🛠️ Development

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DEBUG=True
export SECRET_KEY=your-dev-secret-key
export TMDB_API_KEY=your-tmdb-key
export GOOGLE_GEMINI_API_KEY=your-gemini-key

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Testing

```bash
# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 🔐 Security Features

### Authentication & Authorization
- Session-based authentication
- Rate-limited login attempts
- CSRF protection
- Secure password validation

### Data Protection
- Field-level encryption for sensitive data
- Secure API key storage
- Input validation and sanitization
- XSS protection

### Infrastructure Security
- HTTPS/SSL enforcement
- Security headers (CSP, HSTS, X-Frame-Options)
- Secure Docker configuration
- Network isolation

### Monitoring & Logging
- Comprehensive logging
- Error tracking
- Security event monitoring
- Audit trails

## 📈 Performance

### Optimizations
- Redis caching
- Database query optimization
- Static file compression
- CDN-ready static files

### Scalability
- Horizontal scaling with Docker
- Load balancer ready
- Database connection pooling
- Background task processing

## 🚨 Security Checklist

Before production deployment:

- [ ] Generate secure SECRET_KEY
- [ ] Configure HTTPS/SSL certificates
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Generate encryption key for API keys
- [ ] Set up database backups
- [ ] Configure log monitoring
- [ ] Review security headers
- [ ] Test rate limiting
- [ ] Verify input validation

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