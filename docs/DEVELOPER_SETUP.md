# Developer Setup Guide

This guide will help you set up the Suggesterr development environment on your local machine.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- (Optional) Docker and Docker Compose for containerized development

## Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/Casey2134/suggesterr.git
   cd suggesterr
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration (see below)
   ```

5. **Run database migrations**

   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**

   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**

   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Web Interface: http://localhost:8000
   - Admin Interface: http://localhost:8000/admin
   - API Documentation: See [API_REFERENCE.md](API_REFERENCE.md)

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
SECRET_KEY=your-super-secret-django-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Required API Keys
TMDB_API_KEY=your-tmdb-api-key-here
GOOGLE_GEMINI_API_KEY=your-google-gemini-api-key-here

# Database (Optional - uses SQLite by default)
DB_HOST=localhost
DB_NAME=suggesterr
DB_USER=suggesterr
DB_PASSWORD=suggesterr
DB_PORT=5432

# Optional External Services
JELLYFIN_URL=http://your-jellyfin-server:8096
JELLYFIN_API_KEY=your-jellyfin-api-key
PLEX_URL=http://your-plex-server:32400
PLEX_TOKEN=your-plex-token
RADARR_URL=http://your-radarr-server:7878
RADARR_API_KEY=your-radarr-api-key
SONARR_URL=http://your-sonarr-server:8989
SONARR_API_KEY=your-sonarr-api-key

# Security (Optional)
ENCRYPTION_KEY=your-encryption-key-for-sensitive-data
FORCE_SSL=False
```

### Getting API Keys

#### TMDB API Key (Required)

1. Create an account at [The Movie Database](https://www.themoviedb.org/)
2. Go to Settings > API
3. Request an API key (free)
4. Add the API key to your `.env` file

#### Google Gemini API Key (Required)

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Create a new project or use an existing one
3. Generate an API key
4. Add the API key to your `.env` file

#### Media Server Integration (Optional)

- **Jellyfin**: Enable API access in Jellyfin settings and generate an API key
- **Plex**: Get your Plex token from the Plex server settings
- **Radarr/Sonarr**: Generate API keys in the respective applications' settings

## Database Setup

### SQLite (Default for Development)

SQLite is used by default and requires no additional setup. The database file will be created automatically at `db.sqlite3`.

### PostgreSQL (Production/Optional)

For production-like development:

1. **Install PostgreSQL**

   ```bash
   # macOS
   brew install postgresql
   brew services start postgresql

   # Ubuntu/Debian
   sudo apt install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **Create database and user**

   ```sql
   sudo -u postgres psql
   CREATE DATABASE suggesterr;
   CREATE USER suggesterr WITH PASSWORD 'suggesterr';
   GRANT ALL PRIVILEGES ON DATABASE suggesterr TO suggesterr;
   \q
   ```

3. **Update .env file**
   ```env
   DB_HOST=localhost
   DB_NAME=suggesterr
   DB_USER=suggesterr
   DB_PASSWORD=suggesterr
   DB_PORT=5432
   ```

## Development Commands

### Django Management Commands

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver

# Run development server on specific port
python manage.py runserver 8080

# Open Django shell
python manage.py shell

# Clear movie database (custom command)
python manage.py clear_movie_db

# Sync availability with media servers (custom command)
python manage.py sync_availability
```

### Testing

```bash
# Run all tests
python manage.py test

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Run specific app tests
python manage.py test movies
python manage.py test accounts
```

### Code Quality

```bash
# Install development dependencies
pip install -r requirements.txt

# Format code (if you add a formatter)
black .

# Lint code (if you add a linter)
flake8 .
```

## Docker Development (Alternative)

If you prefer containerized development:

1. **Build and run with Docker Compose**

   ```bash
   docker-compose up -d
   ```

2. **Run migrations in container**

   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser in container**

   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **View logs**
   ```bash
   docker-compose logs -f web
   ```

## Project Structure

```
suggesterr/
├── accounts/           # User authentication and settings
├── core/              # Base functionality and health checks
├── integrations/      # Media server and download client integrations
├── movies/            # Movie models, TMDB integration, AI recommendations
├── recommendations/   # AI-powered recommendation engine
├── tv_shows/          # TV show models and functionality
├── static/            # Static files (CSS, JS, images)
├── templates/         # Django templates
├── docs/             # Documentation
├── manage.py         # Django management script
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variables template
└── README.md         # Project overview
```

## Development Workflow

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

   - Follow Django best practices
   - Write tests for new functionality
   - Update documentation if needed

3. **Run tests**

   ```bash
   python manage.py test
   ```

4. **Commit and push**

   ```bash
   git add .
   git commit -m "Add your feature description"
   git push origin feature/your-feature-name
   ```

5. **Create a pull request**
   - Describe your changes
   - Reference any related issues
   - Wait for code review

## Common Issues and Solutions

### Issue: TMDB API not working

**Solution**: Verify your TMDB API key is correct and active. Check the TMDB API documentation for rate limits.

### Issue: Database migration errors

**Solution**:

```bash
# Reset migrations (development only)
python manage.py migrate accounts zero
python manage.py migrate
```

### Issue: Static files not loading

**Solution**:

```bash
python manage.py collectstatic
# Ensure DEBUG=True in development
```

### Issue: Media server integration not working

**Solution**:

1. Check server URLs are accessible
2. Verify API keys/tokens are correct
3. Test connections via `/accounts/test_connections/`

## IDE Setup

### VS Code

Recommended extensions:

- Python
- Django
- GitLens
- Thunder Client (for API testing)

### PyCharm

1. Open project in PyCharm
2. Configure Python interpreter to use your virtual environment
3. Set Django settings module: `suggesterr.settings`

## Getting Help

- Check the [Architecture documentation](ARCHITECTURE.md) for system overview
- Review [API Reference](API_REFERENCE.md) for endpoint details
- Check existing issues on GitHub
- Create a new issue for bugs or feature requests

## Next Steps

Once you have the development environment set up:

1. Read the [Architecture Overview](ARCHITECTURE.md)
2. Review the [API Reference](API_REFERENCE.md)
3. Check out the [Integrations Guide](INTEGRATIONS.md)
4. Explore the codebase and start contributing!
