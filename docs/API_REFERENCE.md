# API Reference

This document provides a comprehensive reference for all API endpoints in the Suggesterr application.

## Base URL

- **Development**: `http://localhost:8000/api/`
- **Production**: `https://your-domain.com/api/`

## Authentication

### Session Authentication (Web Interface)

The web interface uses Django's session-based authentication. Users must log in through the web interface.

### API Key Authentication (Optional)

For API clients, token-based authentication can be implemented. Currently uses session authentication.

## Response Format

All API responses are in JSON format with consistent structure:

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "count": 10,
  "next": "http://example.com/api/endpoint/?page=2",
  "previous": null
}
```

### Error Response

```json
{
  "status": "error",
  "error": "Error message",
  "details": { ... }
}
```

## Movies API

### List Movies

```
GET /api/movies/
```

**Parameters:**

- `page` (integer): Page number for pagination
- `search` (string): Search movies by title
- `genre` (string): Filter by genre
- `year` (integer): Filter by release year
- `rating_gte` (float): Minimum rating filter

**Response:**

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/movies/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Inception",
      "overview": "A thief who steals corporate secrets...",
      "release_date": "2010-07-16",
      "poster_path": "/path/to/poster.jpg",
      "backdrop_path": "/path/to/backdrop.jpg",
      "vote_average": 8.8,
      "vote_count": 12000,
      "genres": ["Action", "Sci-Fi"],
      "runtime": 148,
      "tmdb_id": 27205,
      "mpaa_rating": "PG-13",
      "available_on": ["jellyfin", "plex"],
      "in_watchlist": true
    }
  ]
}
```

### Get Movie Details

```
GET /api/movies/{id}/
```

**Response:**

```json
{
  "id": 1,
  "title": "Inception",
  "overview": "A thief who steals corporate secrets...",
  "release_date": "2010-07-16",
  "poster_path": "/path/to/poster.jpg",
  "backdrop_path": "/path/to/backdrop.jpg",
  "vote_average": 8.8,
  "vote_count": 12000,
  "genres": ["Action", "Sci-Fi"],
  "runtime": 148,
  "tmdb_id": 27205,
  "mpaa_rating": "PG-13",
  "available_on": ["jellyfin"],
  "in_watchlist": false,
  "recommended_by_ai": true,
  "recommendation_reason": "Based on your love for mind-bending thrillers"
}
```

### Get AI Recommendations

```
GET /api/movies/ai_recommendations/
```

**Parameters:**

- `mood` (string): Current mood (e.g., "action", "comedy", "drama")
- `limit` (integer): Number of recommendations (default: 10)

**Response:**

```json
{
  "recommendations": [
    {
      "movie": {
        "id": 1,
        "title": "Inception",
        "overview": "...",
        "poster_path": "/path/to/poster.jpg",
        "vote_average": 8.8,
        "genres": ["Action", "Sci-Fi"]
      },
      "reason": "Perfect for your current mood",
      "confidence": 0.95,
      "available": true
    }
  ],
  "context": {
    "user_preferences": ["action", "sci-fi"],
    "mood": "thoughtful",
    "time_of_day": "evening"
  }
}
```

### Request Movie Download

```
POST /api/movies/{id}/request_movie/
```

**Request Body:**

```json
{
  "quality_profile": "HD-1080p"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Movie requested successfully",
  "radarr_status": "added",
  "estimated_download_time": "2-4 hours"
}
```

### Add to Watchlist

```
POST /api/movies/{id}/add_to_watchlist/
```

**Response:**

```json
{
  "status": "success",
  "message": "Added to watchlist"
}
```

### Remove from Watchlist

```
DELETE /api/movies/{id}/remove_from_watchlist/
```

### Provide Feedback

```
POST /api/movies/{id}/feedback/
```

**Request Body:**

```json
{
  "feedback_type": "negative",
  "reason": "not_interested"
}
```

## TV Shows API

### List TV Shows

```
GET /api/tv-shows/
```

**Parameters:**

- `page` (integer): Page number
- `search` (string): Search by title
- `genre` (string): Filter by genre
- `status` (string): Filter by status (returning, ended, etc.)

**Response:**

```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "name": "Breaking Bad",
      "overview": "A high school chemistry teacher...",
      "first_air_date": "2008-01-20",
      "last_air_date": "2013-09-29",
      "poster_path": "/path/to/poster.jpg",
      "vote_average": 9.5,
      "genres": ["Drama", "Crime"],
      "status": "Ended",
      "number_of_seasons": 5,
      "number_of_episodes": 62,
      "tmdb_id": 1396,
      "tv_rating": "TV-MA"
    }
  ]
}
```

### Get TV Show Details

```
GET /api/tv-shows/{id}/
```

### Get TV Show AI Recommendations

```
GET /api/tv-shows/ai_recommendations/
```

### Request TV Show Download

```
POST /api/tv-shows/{id}/request_tv_show/
```

**Request Body:**

```json
{
  "seasons": [1, 2, 3],
  "quality_profile": "HD-1080p"
}
```

## Chat/Recommendations API

### Send Chat Message

```
POST /api/chat/message/
```

**Request Body:**

```json
{
  "message": "I want to watch something funny tonight",
  "context": {
    "mood": "comedy",
    "time_available": "2 hours"
  }
}
```

**Response:**

```json
{
  "response": "I'd recommend 'The Grand Budapest Hotel'...",
  "recommendations": [
    {
      "type": "movie",
      "id": 123,
      "title": "The Grand Budapest Hotel",
      "reason": "Perfect quirky comedy for tonight"
    }
  ],
  "conversation_id": "conv_123"
}
```

### Get Chat History

```
GET /api/chat/history/
```

**Parameters:**

- `conversation_id` (string): Specific conversation
- `limit` (integer): Number of messages

**Response:**

```json
{
  "messages": [
    {
      "id": 1,
      "user_message": "I want something funny",
      "ai_response": "I recommend...",
      "timestamp": "2024-01-15T20:30:00Z",
      "recommendations": [...]
    }
  ]
}
```

### Start New Conversation

```
POST /api/chat/new_conversation/
```

## User Management API

### Login

```
POST /api/accounts/login/
```

**Request Body:**

```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**

```json
{
  "status": "success",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "message": "Login successful"
}
```

### Register

```
POST /api/accounts/register/
```

**Request Body:**

```json
{
  "username": "newuser@example.com",
  "password": "password123",
  "password_confirm": "password123",
  "first_name": "Jane",
  "last_name": "Doe"
}
```

### Logout

```
POST /api/accounts/logout/
```

### Get User Settings

```
GET /api/accounts/settings/
```

**Response:**

```json
{
  "user_preferences": {
    "preferred_genres": ["action", "sci-fi"],
    "content_ratings": ["PG", "PG-13", "R"],
    "streaming_services": ["netflix", "hulu"]
  },
  "integrations": {
    "jellyfin_configured": true,
    "radarr_configured": true,
    "plex_configured": false
  }
}
```

### Update User Settings

```
PUT /api/accounts/settings/
```

**Request Body:**

```json
{
  "preferred_genres": ["comedy", "drama"],
  "jellyfin_url": "http://localhost:8096",
  "jellyfin_api_key": "your-api-key"
}
```

### Test Connections

```
GET /api/accounts/test_connections/
```

**Response:**

```json
{
  "tmdb": {
    "status": "connected",
    "message": "API key valid"
  },
  "jellyfin": {
    "status": "connected",
    "library_count": 1500
  },
  "radarr": {
    "status": "error",
    "message": "Invalid API key"
  },
  "gemini": {
    "status": "connected",
    "model": "gemini-2.0-flash"
  }
}
```

## Search API

### Global Search

```
GET /api/search/
```

**Parameters:**

- `q` (string): Search query
- `type` (string): Content type ("movie", "tv", "all")

**Response:**

```json
{
  "movies": [...],
  "tv_shows": [...],
  "total_results": 25
}
```

## Health Check API

### System Health

```
GET /api/health/
```

**Response:**

```json
{
  "status": "healthy",
  "database": "connected",
  "external_apis": {
    "tmdb": "operational",
    "gemini": "operational"
  },
  "version": "1.0.0",
  "uptime": "5 days, 12 hours"
}
```

## Error Codes

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Custom Error Codes

- `INVALID_API_KEY`: API key is invalid or expired
- `EXTERNAL_SERVICE_ERROR`: External service (TMDB, Gemini) error
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded
- `CONTENT_NOT_AVAILABLE`: Requested content not available

## Rate Limiting

### Default Limits

- **Authentication endpoints**: 5 requests per minute
- **Search endpoints**: 100 requests per hour
- **AI recommendation endpoints**: 50 requests per hour
- **General API endpoints**: 1000 requests per hour

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642694400
```

## Pagination

All list endpoints support pagination with the following parameters:

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

Response includes:

- `count`: Total number of items
- `next`: URL for next page
- `previous`: URL for previous page
- `results`: Array of items

## Examples

### Get Movie Recommendations for Comedy Night

```bash
curl -X GET "http://localhost:8000/api/movies/ai_recommendations/?mood=comedy&limit=5" \
  -H "Content-Type: application/json" \
  --cookie "sessionid=your-session-id"
```

### Search for Action Movies

```bash
curl -X GET "http://localhost:8000/api/movies/?search=action&genre=Action" \
  -H "Content-Type: application/json"
```

### Request Movie Download

```bash
curl -X POST "http://localhost:8000/api/movies/123/request_movie/" \
  -H "Content-Type: application/json" \
  -d '{"quality_profile": "HD-1080p"}' \
  --cookie "sessionid=your-session-id"
```

### Chat for Recommendations

```bash
curl -X POST "http://localhost:8000/api/chat/message/" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to watch a mind-bending sci-fi movie"}' \
  --cookie "sessionid=your-session-id"
```

## SDK and Libraries

Currently, the API is RESTful and can be consumed by any HTTP client. Consider these approaches:

### JavaScript/TypeScript

```javascript
const response = await fetch("/api/movies/ai_recommendations/", {
  credentials: "include", // Include cookies for session auth
});
const data = await response.json();
```

### Python

```python
import requests

session = requests.Session()
session.post('/api/accounts/login/', data={'username': 'user', 'password': 'pass'})
response = session.get('/api/movies/ai_recommendations/')
```

### cURL Examples

See the examples section above for common cURL commands.
