# Integrations Guide

This document explains how to set up and configure external service integrations with Suggesterr.

## Overview

Suggesterr integrates with several external services to provide a complete media management experience:

- **TMDB**: Movie and TV show metadata
- **Google Gemini**: AI-powered recommendations and chat
- **Jellyfin/Plex**: Media server integration for library awareness
- **Radarr/Sonarr**: Automated download management

## Required Integrations

### TMDB (The Movie Database)

**Purpose**: Primary source for movie and TV show metadata, ratings, and images.

**Setup:**

1. Create a free account at [TMDB](https://www.themoviedb.org/)
2. Go to Settings → API
3. Request an API key (usually approved instantly)
4. Add to your `.env` file:
   ```env
   TMDB_API_KEY=your-tmdb-api-key-here
   ```

**Features:**

- Movie and TV show metadata
- High-quality posters and backdrops
- User ratings and reviews
- Genre information
- Release dates and runtime

### Google Gemini AI

**Purpose**: Powers the AI recommendation engine and chat interface.

**Setup:**

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Create a new project or use existing
3. Generate an API key
4. Add to your `.env` file:
   ```env
   GOOGLE_GEMINI_API_KEY=your-gemini-api-key-here
   ```

**Features:**

- Natural language movie discovery
- Personalized recommendations
- Chat-based interface
- Context-aware suggestions
- User preference learning

## Optional Integrations

### Jellyfin Media Server

**Purpose**: Open-source media server for library awareness and availability checking.

**Prerequisites:**

- Jellyfin server running and accessible
- Movies and TV shows organized in libraries

**Setup:**

1. In Jellyfin admin panel, go to Dashboard → API Keys
2. Generate a new API key
3. Note your Jellyfin server URL
4. Add to your `.env` file:
   ```env
   JELLYFIN_URL=http://your-jellyfin-server:8096
   JELLYFIN_API_KEY=your-jellyfin-api-key
   ```

**Configuration:**

- Ensure your Jellyfin libraries are properly organized
- Movie library should contain movie files
- TV show library should contain TV series
- Metadata providers should be configured for best results

**Features:**

- Check what's available in your library
- Library-aware AI recommendations
- Direct links to content in Jellyfin
- Real-time availability updates

### Plex Media Server

**Purpose**: Commercial media server alternative to Jellyfin.

**Prerequisites:**

- Plex Media Server running
- Plex Pass (may be required for API access)

**Setup:**

1. Get your Plex token:
   - Method 1: Check browser network tab when accessing Plex Web
   - Method 2: Use Plex API documentation
   - Method 3: Use third-party tools like PlexAPI
2. Add to your `.env` file:
   ```env
   PLEX_URL=http://your-plex-server:32400
   PLEX_TOKEN=your-plex-token
   ```

**Features:**

- Library content awareness
- Availability checking
- Integration with Plex Web interface
- Support for multiple libraries

### Radarr (Movie Downloads)

**Purpose**: Automated movie downloading and management.

**Prerequisites:**

- Radarr v3+ installed and configured
- Download client configured (qBittorrent, Transmission, etc.)
- Indexers configured for torrent/usenet sources

**Setup:**

1. In Radarr, go to Settings → General
2. Copy the API Key
3. Note your Radarr URL
4. Add to your `.env` file:
   ```env
   RADARR_URL=http://your-radarr-server:7878
   RADARR_API_KEY=your-radarr-api-key
   ```

**Configuration:**

- Ensure root folders are configured
- Quality profiles should be set up
- Download clients must be configured and tested
- Indexers should be added and working

**Features:**

- One-click movie requests
- Quality profile selection
- Download monitoring
- Library integration

### Sonarr (TV Show Downloads)

**Purpose**: Automated TV show downloading and management.

**Prerequisites:**

- Sonarr v3+ installed and configured
- Download client configured
- Indexers configured for TV content

**Setup:**

1. In Sonarr, go to Settings → General
2. Copy the API Key
3. Note your Sonarr URL
4. Add to your `.env` file:
   ```env
   SONARR_URL=http://your-sonarr-server:8989
   SONARR_API_KEY=your-sonarr-api-key
   ```

**Features:**

- TV show season requests
- Episode tracking
- Series monitoring
- Season selection for downloads

## Configuration Testing

### Testing All Connections

Use the built-in connection test endpoint:

```bash
curl -X GET "http://localhost:8000/accounts/test_connections/" \
  --cookie "sessionid=your-session-id"
```

Or visit the test page in your browser:

```
http://localhost:8000/accounts/test_connections/
```

### Individual Service Testing

#### TMDB Test

```python
import requests
api_key = "your-tmdb-api-key"
response = requests.get(f"https://api.themoviedb.org/3/movie/550?api_key={api_key}")
print(response.json())
```

#### Jellyfin Test

```python
import requests
headers = {'X-MediaBrowser-Token': 'your-jellyfin-api-key'}
response = requests.get("http://your-jellyfin-server:8096/System/Info/Public", headers=headers)
print(response.json())
```

#### Radarr Test

```python
import requests
headers = {'X-Api-Key': 'your-radarr-api-key'}
response = requests.get("http://your-radarr-server:7878/api/v3/system/status", headers=headers)
print(response.json())
```

## Troubleshooting

### Common Issues

#### TMDB API Issues

- **Rate Limiting**: TMDB has rate limits. Suggesterr includes caching to minimize requests
- **Invalid Key**: Ensure your API key is correct and approved
- **Geo-blocking**: Some regions may have restrictions

**Solutions:**

- Check API key in TMDB dashboard
- Verify network connectivity
- Review application logs for specific errors

#### Jellyfin Connection Issues

- **Network Access**: Ensure Jellyfin is accessible from Suggesterr
- **API Key**: Verify the API key is correct and has proper permissions
- **Firewall**: Check firewall settings on both ends

**Solutions:**

```bash
# Test network connectivity
curl -I http://your-jellyfin-server:8096

# Test API key
curl -H "X-MediaBrowser-Token: your-api-key" \
  http://your-jellyfin-server:8096/System/Info/Public
```

#### Radarr/Sonarr Issues

- **API Version**: Ensure you're using v3+ of Radarr/Sonarr
- **Root Folders**: Must be configured in Radarr/Sonarr
- **Download Clients**: Must be properly configured

**Solutions:**

- Update to latest Radarr/Sonarr version
- Check root folder permissions
- Verify download client connectivity
- Review Radarr/Sonarr logs

#### Google Gemini Issues

- **API Quota**: Check your Google Cloud console for quota limits
- **Billing**: Ensure billing is enabled for your Google Cloud project
- **Model Access**: Verify access to Gemini 2.0 Flash model

**Solutions:**

- Check Google Cloud Console
- Review billing settings
- Test API key with simple request

### Network Configuration

#### Firewall Rules

Ensure these ports are accessible:

- **Jellyfin**: 8096 (default)
- **Plex**: 32400 (default)
- **Radarr**: 7878 (default)
- **Sonarr**: 8989 (default)

#### Docker Networking

If running in Docker, ensure services can communicate:

```yaml
# docker-compose.yml
networks:
  media-network:
    driver: bridge

services:
  suggesterr:
    networks:
      - media-network
```

#### Reverse Proxy Setup

If using a reverse proxy (Nginx, Traefik), ensure proper headers:

```nginx
location /jellyfin/ {
    proxy_pass http://jellyfin:8096/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Best Practices

### Security

- **API Keys**: Store securely in environment variables, never in code
- **Network Access**: Limit access to trusted networks when possible
- **Regular Updates**: Keep all services updated
- **Monitoring**: Set up monitoring for service availability

### Performance

- **Caching**: Suggesterr implements caching for external API calls
- **Rate Limiting**: Respect external service rate limits
- **Timeouts**: Configure appropriate timeouts for network calls
- **Health Checks**: Implement regular health checks

### Reliability

- **Error Handling**: Graceful degradation when services are unavailable
- **Retries**: Automatic retry logic for transient failures
- **Monitoring**: Alert on service failures
- **Backups**: Regular backups of configuration

## Advanced Configuration

### Custom Quality Profiles

#### Radarr Quality Profiles

```json
{
  "name": "HD-1080p",
  "cutoff": {
    "id": 7,
    "name": "Bluray-1080p"
  },
  "items": [
    { "quality": { "id": 1, "name": "SDTV" }, "allowed": false },
    { "quality": { "id": 8, "name": "WEBDL-1080p" }, "allowed": true },
    { "quality": { "id": 7, "name": "Bluray-1080p" }, "allowed": true }
  ]
}
```

#### Sonarr Quality Profiles

Configure similar quality profiles for TV shows with appropriate cutoffs and allowed qualities.

### Custom Indexers

Configure indexers in Radarr/Sonarr for optimal content discovery:

- Public trackers (legal content only)
- Private trackers (with proper authentication)
- Usenet indexers (with valid accounts)

### Library Organization

Organize your media libraries for optimal integration:

#### Jellyfin/Plex Structure

```
Movies/
├── Movie Title (Year)/
│   ├── Movie Title (Year).mkv
│   └── Movie Title (Year).nfo
└── Another Movie (Year)/
    ├── Another Movie (Year).mp4
    └── Another Movie (Year).nfo

TV Shows/
├── Show Name/
│   ├── Season 01/
│   │   ├── Show Name - S01E01.mkv
│   │   └── Show Name - S01E02.mkv
│   └── Season 02/
└── Another Show/
```

## Support and Resources

### Documentation Links

- [TMDB API Documentation](https://developers.themoviedb.org/3)
- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Jellyfin API Documentation](https://jellyfin.org/docs/general/networking/index.html)
- [Plex API Documentation](https://github.com/plexinc/plex-media-player/wiki/Remote-control-API)
- [Radarr API Documentation](https://radarr.video/docs/api/)
- [Sonarr API Documentation](https://sonarr.tv/#downloads)

### Community Resources

- [r/jellyfin](https://reddit.com/r/jellyfin)
- [r/radarr](https://reddit.com/r/radarr)
- [r/sonarr](https://reddit.com/r/sonarr)
- [Plex Forums](https://forums.plex.tv/)

### Getting Help

1. Check service logs first
2. Use the built-in connection test
3. Review this documentation
4. Check external service documentation
5. Create an issue on GitHub with logs and configuration details
