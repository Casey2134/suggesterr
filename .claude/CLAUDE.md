# Suggesterr - Django Development Guide

## 📚 CRITICAL DOCUMENTATION PATTERN

**ALWAYS ADD IMPORTANT DOCS HERE!** When you create or discover:

- Architecture diagrams → Add reference path here
- Database schemas → Add reference path here
- Problem solutions → Add reference path here
- Setup guides → Add reference path here

This prevents context loss! Update this file IMMEDIATELY when creating important docs.

## 🗺️ Key Documentation References

- **Virtual Environment Setup**: See below 🚨 READ THIS FIRST!
- **Django Apps Structure**: See below 🏗️
- **Database Architecture**: `/docs/DATABASE_ARCHITECTURE.md` 🗄️
- **API Architecture**: `/docs/API_ARCHITECTURE.md` 📡
- **Security Guidelines**: `/docs/SECURITY_CHECKLIST.md` 🔐 CRITICAL
- **AI Integration**: `/docs/AI_INTEGRATION_ARCHITECTURE.md` 🤖
- **Testing Strategy**: `/docs/TESTING_STRATEGY.md` 🧪 MANDATORY
- **Frontend Architecture**: `/docs/FRONTEND_ARCHITECTURE.md` 🎨
- **Code Quality Standards**: See below 📝

## Project Overview

Suggesterr is an AI-powered movie and TV show recommendation system built with Django. It integrates with Google Gemini 2.0 Flash for intelligent recommendations and connects with media management tools like Jellyfin, Plex, Radarr, and Sonarr.

## 🚨 Virtual Environment Setup - READ THIS FIRST!

**CRITICAL: Always use the virtual environment located at `./venv/`**

**⚠️ MANDATORY: The virtual environment MUST be activated before running ANY Python commands, Django commands, or installing packages. Failure to do so will cause dependency conflicts and errors.**

```bash
# Activate virtual environment (required for all development)
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Deactivate when done
deactivate
```

### Virtual Environment Rules

1. **ALWAYS activate `venv`** before any Python work
2. **Never run Python commands** without activating the virtual environment first
3. **Never install packages globally** - always use the activated venv
4. **Check your prompt** - should show `(venv)` when activated
5. **If you get import errors**, ensure venv is activated

## 🏗️ Django Apps Structure

- **movies/**: Core movie management, TMDB integration, Gemini AI service
- **tv_shows/**: TV show management and recommendations
- **recommendations/**: AI recommendation engine and algorithms
- **accounts/**: User authentication and settings
- **core/**: Dashboard and shared functionality
- **integrations/**: External service integrations (Jellyfin, Plex, Radarr, Sonarr)

## 🔧 Development Commands

**⚠️ IMPORTANT: All commands below require the virtual environment to be activated first!**

```bash
# FIRST: Always activate the virtual environment
source venv/bin/activate

# Run development server
python manage.py runserver

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Install packages (only with venv activated)
pip install package_name

# Run tests (only with venv activated)
pytest

# Run with coverage (only with venv activated)
coverage run -m pytest && coverage report

# Run specific app tests (only with venv activated)
python manage.py test recommendations
python manage.py test movies
python manage.py test accounts

# Check for missing migrations (only with venv activated)
python manage.py makemigrations --dry-run

# Django shell (only with venv activated)
python manage.py shell
```

## 🔐 Django Security Best Practices - CRITICAL

### Authentication & Authorization

- **Always use Django's built-in authentication system**
- **All user-specific endpoints require `@permission_classes([IsAuthenticated])`**
- **Check user ownership**: `queryset.filter(user=request.user)`
- **Use CSRF protection** on all POST requests

### Input Validation

- **Never trust user input** - Always validate and sanitize
- **Use Django serializers** for API data validation
- **Validate URLs and API keys** in real-time
- **Use Django's built-in validators** where possible

### API Security

- **Protect sensitive fields** with `write_only=True` in serializers
- **Use proper HTTP status codes** (200, 201, 400, 401, 403, 404, 500)
- **Handle exceptions gracefully** with try/catch blocks
- **Log security events** for monitoring

## 🧪 Testing Requirements - MANDATORY

**⚠️ CRITICAL: Virtual environment must be activated before running any tests!**

```bash
# FIRST: Activate virtual environment
source venv/bin/activate

# Run comprehensive tests before any feature
python manage.py test

# Run specific tests
python manage.py test recommendations.tests.test_quiz
python manage.py test accounts.tests.test_settings

# Test with coverage
coverage run --source='.' manage.py test
coverage report

# Run pytest (alternative test runner)
pytest

# Run with verbose output
python manage.py test --verbosity=2
```

### Security Testing Checklist ✅

- [ ] **Authentication required** for all user-specific endpoints
- [ ] **Input validation** on all form fields and API endpoints
- [ ] **CSRF protection** on all POST requests
- [ ] **Permission checks** ensure users can only access their own data
- [ ] **SQL injection prevention** through ORM usage
- [ ] **XSS prevention** through proper template escaping
- [ ] **API key protection** with write_only fields

## 📡 API Development (DRF)

### Serializers

```python
class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ['radarr_url', 'radarr_api_key']
        extra_kwargs = {
            'radarr_api_key': {'write_only': True},
        }
```

### ViewSets

```python
class UserSettingsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSettings.objects.filter(user=self.request.user)
```

### URL Structure

- **Template views**: `/recommendations/quiz/`
- **API endpoints**: `/recommendations/api/quiz/questions/`
- **Use separate `api_urls.py`** for cleaner organization

## 🗄️ Database Best Practices

### Models

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    personality_traits = models.JSONField(default=dict)
    quiz_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Profile'

    def __str__(self):
        return f"{self.user.username} Profile"
```

### Query Optimization

- **Use `select_related()`** for foreign keys
- **Use `prefetch_related()`** for many-to-many relationships
- **Add database indexes** for frequently queried fields
- **Use database constraints** where appropriate

## 🎨 Frontend Architecture

### CSS Framework

- **Use custom CSS variables** (NOT Bootstrap)
- **Theme variables**: `var(--bg-primary)`, `var(--accent-color)`, `var(--text-primary)`
- **Location**: `static/css/suggesterr.css`
- **Structure**: `main-content` → `section` → `section-header` + content

### JavaScript Patterns

- **API calls**: Use fetch with CSRF token handling
- **Real-time validation**: Field validation with visual feedback
- **State management**: LocalStorage for settings, session state for quiz
- **Error handling**: Toast notifications with themed styling

## 📝 Current Architecture Overview

### Key Features

- **Discovery Quiz System**: `recommendations/` app with personality-based recommendations
- **AI Recommendation Engine**: `recommendations/chat_service.py` combines user context
- **Settings Management**: Smart updates with real-time validation
- **External Integrations**: Jellyfin, Plex, Radarr, Sonarr support

### File Organization

```
recommendations/
├── models.py           # UserProfile, PersonalityQuiz
├── views.py            # ViewSets and template views
├── serializers.py      # DRF serializers
├── chat_service.py     # AI service logic
├── api_urls.py         # API endpoints
└── urls.py            # Template URLs
```

## 🚀 Development Workflow

### Adding New Features

1. **FIRST: Activate virtual environment** (`source venv/bin/activate`)
2. **Create models** with proper relationships and constraints
3. **Add serializers** for API validation
4. **Create API views** with authentication
5. **Add URL patterns** to `api_urls.py`
6. **Build frontend** with app's CSS framework
7. **Write comprehensive tests** (unit, integration, security)
8. **Test with existing patterns** (quiz/settings)

### Code Quality Checklist ✅

- [ ] **PEP 8 compliance** (use 4 spaces, max 79 chars)
- [ ] **Meaningful variable names**
- [ ] **Docstrings** for complex functions
- [ ] **Type hints** where appropriate
- [ ] **Error handling** with try/catch
- [ ] **Logging** for debugging and monitoring

## 🔒 Security Rules - NEVER IGNORE

1. **Never trust user input** - Always validate and sanitize
2. **Use Django's authentication** - Don't roll your own
3. **Implement proper permissions** - Check user ownership
4. **Protect API keys** - Use write_only serializer fields
5. **Use CSRF tokens** - Protect against cross-site requests
6. **Validate URLs and data** - Prevent injection attacks
7. **Test security scenarios** - Unauthorized access, invalid data

## 🎯 Project-Specific Patterns

- **AI Integration**: All user context flows through `chat_service.py`
- **Settings Management**: Only save filled fields, show detailed feedback
- **CSS Framework**: Custom variables, not Bootstrap classes
- **API Structure**: Separate `api_urls.py` for API endpoints
- **Testing**: Follow quiz/settings patterns for new features

## ⚠️ Critical Reminders

- **ALWAYS activate virtual environment** before ANY Python development work
- **Check your command prompt** shows `(venv)` before running commands
- **Never run Python/Django commands** without virtual environment activated
- **Run migrations** after model changes (with venv activated)
- **Write tests** for new functionality (with venv activated)
- **Follow security checklist** for all new features
- **Test everything** before deployment

## 🔧 Before Making Any Changes

1. **FIRST: Activate virtual environment** (`source venv/bin/activate`)
2. **Review existing code patterns** in the relevant app
3. **Check current tests** to understand expected behavior
4. **Understand data flow** through models → serializers → views
5. **Identify security implications** of the change
6. **Plan test coverage** for new functionality
7. **Consider performance impact** of database changes
8. **Review API consistency** with existing endpoints
9. **Run all tests** to ensure nothing is broken (with venv activated)

---

This guide ensures consistent, secure, and maintainable code following Django best practices while preserving the existing architecture and patterns of the Suggesterr project.
