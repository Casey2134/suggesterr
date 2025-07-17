# Suggesterr - Django Project Overview

## Project Description

Suggesterr is an AI-powered movie and TV show recommendation system built with Django. It integrates with Google Gemini 2.0 Flash for intelligent recommendations and connects with media management tools like Jellyfin, Plex, Radarr, and Sonarr.

## Virtual Environment Setup

**IMPORTANT: Always use the virtual environment located at `./venv/`**

```bash
# Activate virtual environment (required for all development)
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Deactivate when done
deactivate
```

## Django Apps Structure

- **movies/**: Core movie management, TMDB integration, Gemini AI service
- **tv_shows/**: TV show management and recommendations
- **recommendations/**: AI recommendation engine and algorithms
- **accounts/**: User authentication and settings
- **core/**: Dashboard and shared functionality
- **integrations/**: External service integrations (Jellyfin, Plex, Radarr, Sonarr)

## Development Commands

```bash
# Run development server
python manage.py runserver

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Run tests
pytest

# Run with coverage
coverage run -m pytest && coverage report
```

## Django Best Practices - ALWAYS FOLLOW

### 1. Models

- Use proper field types and constraints
- Always add `__str__` methods for admin clarity
- Use Django's built-in validators
- Follow naming conventions: CamelCase for models, snake_case for fields
- Add proper Meta classes with ordering and verbose names

### 2. Views

- Use class-based views (CBVs) for complex logic
- Use function-based views (FBVs) for simple operations
- Always validate user input
- Use proper HTTP status codes
- Handle exceptions gracefully
- Use Django's permission system

### 3. URLs

- Use descriptive URL names
- Group related URLs in app-specific url files
- Use path() over url() for better readability
- Include namespace for app URLs

### 4. Templates

- Extend base templates properly
- Use template inheritance effectively
- Load static files correctly with `{% load static %}`
- Use CSRF tokens in forms
- Escape user content properly

### 5. Settings

- Use environment variables for sensitive data
- Separate settings for different environments
- Never commit secrets to version control
- Use Django's security features (CSRF, XSS protection, etc.)

### 6. Database

- Use migrations for all schema changes
- Create proper indexes for frequently queried fields
- Use select_related() and prefetch_related() to avoid N+1 queries
- Use database constraints where appropriate

### 7. Security

- Always validate and sanitize user input
- Use Django's built-in authentication system
- Implement proper permission checks
- Use HTTPS in production
- Keep dependencies updated

### 8. API Development (DRF)

- Use proper serializers for data validation
- Implement proper pagination
- Use viewsets for CRUD operations
- Add proper error handling
- Use throttling for rate limiting

### 9. Testing

- Write tests for all critical functionality
- Use Django's TestCase for database tests
- Use factory-boy for test data generation
- Test both positive and negative scenarios
- Maintain good test coverage

### 10. Performance

- Use database indexes appropriately
- Implement caching where beneficial
- Use pagination for large datasets
- Optimize query performance with select_related/prefetch_related
- Use Celery for background tasks

## Code Quality Standards

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to classes and complex functions
- Keep functions small and focused
- Use type hints where appropriate
- Comment complex business logic
  -update this file with any context for future ai models

## File Organization

- Keep models, views, and serializers organized by functionality
- Use separate files for large modules (e.g., services.py)
- Group related functionality in the same app
- Follow Django's app structure conventions

## Integration Services

- **Gemini AI**: movies/gemini_service.py
- **TMDB**: movies/tmdb_service.py, movies/tmdb_tv_service.py
- **External APIs**: integrations/services.py

## Key Features & Architecture

### Discovery Quiz System

- **Location**: `recommendations/` app
- **Models**: `UserProfile`, `PersonalityQuiz` (recommendations/models.py)
- **API Endpoints**:
  - `GET /recommendations/api/quiz/questions/` - Get quiz questions
  - `POST /recommendations/api/quiz/submit/` - Submit answers
  - `GET /recommendations/api/quiz/profile/` - Get user profile
  - `POST /recommendations/api/quiz/retake/` - Reset quiz
- **Frontend**: `/recommendations/quiz/` - Interactive quiz interface
- **Integration**: Personality data automatically feeds into Gemini AI prompts

### AI Recommendation Engine

- **Service**: `recommendations/chat_service.py`
- **Context Building**: Combines user library, negative feedback, and personality data
- **Personalization**: Uses quiz results to tailor Gemini prompts
- **Pattern**: All user context (library, preferences, personality) merged into single prompt

### Settings Management

- **Smart Updates**: Only saves filled fields, detects changes
- **Real-time Validation**: URL and API key validation with visual feedback
- **Local Storage**: Theme and service configurations persist locally
- **Pattern**: Validate → Save only changed fields → Show detailed feedback

## Frontend Architecture

### CSS Framework

- **Custom Variables**: Uses app-specific CSS variables (not Bootstrap)
- **Theme System**: `var(--bg-primary)`, `var(--accent-color)`, `var(--text-primary)`
- **Location**: `static/css/suggesterr.css`
- **Structure**: `main-content` → `section` → `section-header` + content
- **Responsive**: Mobile-first approach with custom breakpoints

### JavaScript Patterns

- **API Calls**: Use fetch with CSRF token handling
- **State Management**: LocalStorage for settings, session state for quiz
- **Error Handling**: Toast notifications with themed styling
- **Validation**: Real-time field validation with visual feedback

## Database Models

### User Personality System

```python
# UserProfile - One-to-one with User
personality_traits = JSONField()  # Calculated from quiz
preferred_genres = JSONField()    # Direct from quiz
preferred_decades = JSONField()   # Direct from quiz
quiz_completed = BooleanField()   # Completion status

# PersonalityQuiz - Quiz questions and mapping
trait_mapping = JSONField()       # Maps answers to personality traits
answer_options = JSONField()      # Question options
```

### Recommendation Context

- **UserNegativeFeedback**: Tracks "not interested" items
- **ChatConversation/ChatMessage**: Stores AI chat history
- **Integration**: All data flows into `chat_service.py` for context building

## API Patterns

### Authentication

- All quiz and settings endpoints require `@permission_classes([IsAuthenticated])`
- Use `request.user` for user-specific data
- CSRF protection on all POST requests

### Response Formats

```python
# Success: {"data": {...}, "message": "..."}
# Error: {"error": "...", "details": {...}}
# Quiz: {"questions": [...], "profile": {...}}
```

### URL Structure

- Template views: `/recommendations/quiz/`
- API endpoints: `/recommendations/api/quiz/questions/`
- Separate `api_urls.py` for cleaner organization

## Development Workflow

### Adding New Features

1. Create models with proper relationships
2. Add serializers for API validation
3. Create API views with authentication
4. Add URL patterns to `api_urls.py`
5. Build frontend with app's CSS framework
6. Test with quiz/settings patterns
7. Integrate with existing services

### Testing Commands

```bash
# Run specific app tests
python manage.py test recommendations

# Create sample quiz questions
python manage.py shell < create_quiz_questions.py

# Check for missing migrations
python manage.py makemigrations --dry-run
```

## Common Patterns in This Project

- Use serializers for API data validation
- Implement service classes for complex business logic (chat_service.py)
- Use management commands for data sync operations
- Follow REST API conventions for endpoints
- Use proper error handling and logging
- **CSS**: Use app's custom variables, not Bootstrap classes
- **JS**: Real-time validation with visual feedback
- **APIs**: Separate api_urls.py for better organization
- **Context**: Merge all user data into single AI prompt

## Remember

- Always activate the virtual environment before development
- Run migrations after model changes
- Write tests for new functionality
- Follow Django security best practices
- Use the existing code patterns and conventions
- **Use custom CSS variables** - not Bootstrap (var(--bg-primary), var(--accent-color))
- **API structure** - use api_urls.py for API endpoints, main urls.py for templates
- **AI Integration** - all user context flows through chat_service.py
- **Settings** - only save filled fields, show detailed feedback
- Check the API documentation for endpoint specifications
