#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎬 Starting Suggesterr...${NC}"

# Create config directory if it doesn't exist
mkdir -p /config/{database,logs,media,static}
chown -R suggesterr:suggesterr /config
chmod -R 755 /config

# Set default environment variables if not provided
export DEBUG=${DEBUG:-False}
export SECRET_KEY=${SECRET_KEY:-$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")}
export DB_NAME=${DB_NAME:-suggesterr}
export DB_USER=${DB_USER:-suggesterr}
export DB_PASSWORD=${DB_PASSWORD:-suggesterr}
export DB_HOST=${DB_HOST:-localhost}
export DB_PORT=${DB_PORT:-5432}
export REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}

# Generate encryption key if not provided
if [ -z "$ENCRYPTION_KEY" ]; then
    export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo -e "${YELLOW}⚠️  Generated new encryption key. Save this key: $ENCRYPTION_KEY${NC}"
fi

# Start PostgreSQL
echo -e "${GREEN}🐘 Starting PostgreSQL...${NC}"
sudo service postgresql start

# Wait for PostgreSQL to be ready
echo -e "${GREEN}⏳ Waiting for PostgreSQL to be ready...${NC}"
until sudo -u postgres psql -c '\q' 2>/dev/null; do
    sleep 1
done

# Create database and user if they don't exist
echo -e "${GREEN}🔧 Setting up database...${NC}"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || sudo -u postgres createdb $DB_NAME
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER'" | grep -q 1 || sudo -u postgres createuser $DB_USER
sudo -u postgres psql -c "ALTER USER $DB_USER PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL ON SCHEMA public TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;"

# Start Redis
echo -e "${GREEN}🔴 Starting Redis...${NC}"
redis-server --daemonize yes --dir /config --logfile /config/logs/redis.log

# Wait for Redis to be ready
echo -e "${GREEN}⏳ Waiting for Redis to be ready...${NC}"
until redis-cli ping 2>/dev/null; do
    sleep 1
done

# Run Django setup
echo -e "${GREEN}🐍 Setting up Django...${NC}"

# Debug: Check if Django can start
echo -e "${GREEN}🔍 Checking Django configuration...${NC}"
python manage.py check || echo "Django check had warnings"

# Run migrations
echo -e "${GREEN}📦 Running database migrations...${NC}"
python manage.py migrate --noinput

# Collect static files
echo -e "${GREEN}📁 Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear

# Create superuser if credentials are provided
if [ ! -z "$DJANGO_SUPERUSER_USERNAME" ] && [ ! -z "$DJANGO_SUPERUSER_PASSWORD" ] && [ ! -z "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo -e "${GREEN}👤 Creating superuser...${NC}"
    python manage.py createsuperuser --noinput || echo "Superuser already exists"
fi

# Sync movie data if TMDB_API_KEY is provided
if [ ! -z "$TMDB_API_KEY" ]; then
    echo -e "${GREEN}🎭 Syncing movie data...${NC}"
    python manage.py sync_movies --popular-pages=2 || echo "Movie sync completed with warnings"
fi

# Start Nginx
echo -e "${GREEN}🌐 Starting Nginx...${NC}"
nginx

# Start Supervisor to manage Django and Celery
echo -e "${GREEN}🚀 Starting application services...${NC}"
exec supervisord -c /etc/supervisor/supervisord.conf