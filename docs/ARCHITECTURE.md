# Architecture Overview

This document provides a comprehensive overview of the Suggesterr application architecture, including its components, data flow, and key design decisions.

## System Overview

Suggesterr is a Django-based web application that provides AI-powered movie and TV show recommendations with seamless integration to popular media management tools. The system is designed with a modular architecture that separates concerns and enables easy extensibility.

## High-Level Architecture

```mermaid
graph TD
    subgraph Clients
        WC[Web Client] --&gt; DjangoWebApp
        MC[Mobile Client] --&gt; DjangoWebApp
        API[API Client] --&gt; DjangoWebApp
    end

    DjangoWebApp[Django Web App Suggesterr] --&gt; TMDB[TMDB API<br>(Movie Data)]
    DjangoWebApp --&gt; Gemini[Google Gemini<br>(AI Engine)]
    DjangoWebApp --&gt; MediaServers[Media Servers<br>(Plex/Jellyfin)]
    DjangoWebApp --&gt; DownloadClients[Download Clients<br>(Radarr/Sonarr)]


Django Application Structure

Core Apps

1. core/ - Base Functionality

Purpose: Provides foundational functionality used across the application.

Key Components:

    Health check endpoints

    Error handling

    Base models and utilities

    Middleware for request processing

    Common validators

Models:

    Genre - Movie/TV show genres

Views:

    Health check endpoints

    Dashboard views

    Search functionality

2. accounts/ - User Management

Purpose: Handles user authentication, registration, and user settings.

Key Components:

    User authentication (login/logout/register)

    User settings and preferences

    Integration credentials management

    API key storage (encrypted)

Models:

    UserSettings - User preferences and API credentials

Key Features:

    Secure API key storage with field-level encryption

    Integration testing endpoints

    User preference management

3. movies/ - Movie Management

Purpose: Core movie functionality with TMDB integration and AI recommendations.

Key Components:

    TMDB API integration

    Movie database management

    AI-powered recommendations via Google Gemini

    Availability checking across media servers

Models:

    Movie - Movie information from TMDB

    MovieWatchlist - User movie watchlists

    MovieRecommendation - AI-generated recommendations

    UserNegativeFeedback - User feedback for recommendation improvement

Services:

    TMDBService - TMDB API integration

    GeminiService - AI recommendation engine

    Movie recommendation algorithms

Key Features:

    Real-time TMDB data synchronization

    AI-powered personalized recommendations

    Media server availability checking

    Download automation via Radarr

4. tv_shows/ - TV Show Management

Purpose: TV show functionality parallel to movies.

Key Components:

    TV show models and data management

    Season and episode tracking

    Integration with Sonarr for downloads

Models:

    TVShow - TV show information

    Season and episode tracking

Key Features:

    TV show recommendations

    Season-based download management

    Sonarr integration

5. recommendations/ - AI Recommendation Engine

Purpose: Advanced AI-powered recommendation system with chat interface.

Key Components:

    Google Gemini integration

    Chat-based recommendation interface

    User personality analysis

    Recommendation personalization

Models:

    ChatConversation - User conversation history

    ChatMessage - Individual chat messages

    PersonalityQuiz - User personality assessment

    UserProfile - Enhanced user profiles for recommendations

Services:

    ChatService - Handles chat-based interactions

    AI context management

    Recommendation algorithms

Key Features:

    Natural language movie discovery

    Context-aware recommendations

    User personality-based suggestions

    Chat history and context retention

6. integrations/ - External Service Integration

Purpose: Manages connections to external media management services.

Key Components:

    Media server integration (Jellyfin, Plex)

    Download client integration (Radarr, Sonarr)

    Service health monitoring

    API abstraction layer

Services:

    JellyfinService - Jellyfin media server integration

    PlexService - Plex media server integration

    RadarrService - Radarr movie download automation

    SonarrService - Sonarr TV show download automation

Key Features:

    Multi-platform media server support

    Automated download requests

    Library availability checking

    Connection health monitoring

Data Flow

1. User Registration and Setup

Code snippet

sequenceDiagram
    actor User
    User->>Suggesterr: Register Account
    Suggesterr->>Suggesterr: Create Account
    User->>Suggesterr: Configure API Keys
    Suggesterr->>Suggesterr: Integration Testing

2. Movie Discovery Flow

Code snippet

sequenceDiagram
    actor User
    User->>Suggesterr: Search/Browse Movies
    Suggesterr->>TMDB API: Query Movie Data
    TMDB API-->>Suggesterr: Movie Data
    Suggesterr->>Suggesterr: Update Movie Database
    Suggesterr-->>User: Display UI
    Suggesterr->>Media Servers: Check Availability
    Media Servers-->>Suggesterr: Availability Status

3. AI Recommendation Flow

Code snippet

sequenceDiagram
    actor User
    User->>Suggesterr: Request Recommendation
    Suggesterr->>Suggesterr: Gather Context
    Suggesterr->>Google Gemini: Process AI Request
    Google Gemini-->>Suggesterr: Recommendation Data
    Suggesterr->>Suggesterr: Generate Recommendation
    Suggesterr->>Suggesterr: Personalization
    Suggesterr-->>User: Display Recommendation

4. Download Request Flow

Code snippet

sequenceDiagram
    actor User
    User->>Suggesterr: Request Download
    Suggesterr->>Media Servers: Check Availability
    Media Servers-->>Suggesterr: Availability Status
    alt Available
        Suggesterr->>Download Clients: Send Download Request
        Download Clients-->>Suggesterr: Download Queued
        Suggesterr->>Download Clients: Monitor Status
        Download Clients-->>Suggesterr: Status Updates
        Suggesterr-->>User: Notify User
    else Not Available
        Suggesterr-->>User: Notify Not Available
    end

Database Design

Key Relationships

Code snippet

classDiagram
    class User {
        +id
    }
    class UserSettings {
        +user_id
    }
    class MovieWatchlist {
        +user_id
        +movie_id
    }
    class MovieRecommendation {
        +user_id
        +movie_id
    }
    class ChatConversation {
        +user_id
    }
    class UserProfile {
        +user_id
    }
    class Movie {
        +id
        +tmdb_id
    }
    class UserNegativeFeedback {
        +user_id
        +movie_id
    }
    class ChatMessage {
        +conversation_id
    }

    User "1" -- "1" UserSettings : has
    User "1" -- "0..*" MovieWatchlist : creates
    User "1" -- "0..*" MovieRecommendation : receives
    User "1" -- "0..*" ChatConversation : initiates
    User "1" -- "1" UserProfile : has

    Movie "1" -- "0..*" MovieWatchlist : included_in
    Movie "1" -- "0..*" MovieRecommendation : is_suggested
    Movie "1" -- "0..*" UserNegativeFeedback : receives_feedback

    ChatConversation "1" -- "0..*" ChatMessage : contains

Data Storage Strategy

    Movie/TV Data: Cached from TMDB with periodic synchronization

    User Preferences: Stored locally with encrypted sensitive data

    AI Context: Session-based with conversation history

    Integration Data: Real-time queries with caching for performance

Security Architecture

Authentication & Authorization

    Django's built-in authentication system

    Session-based authentication for web interface

    Token-based authentication available for API clients

Data Protection

    Field-level encryption for sensitive API keys

    HTTPS enforcement in production

    Content Security Policy (CSP) headers

    CSRF protection

    XSS protection

API Security

    Rate limiting on authentication endpoints

    Input validation and sanitization

    Secure error handling (no information disclosure)

    API key rotation support

AI Integration Architecture

Google Gemini Integration

    Model: Gemini 2.0 Flash for fast, intelligent responses

    Context Management: Maintains conversation history and user preferences

    Personalization: Incorporates user viewing history and feedback

    Library Awareness: Considers available content in user's media library

Recommendation Algorithm

    User Profiling: Analyzes viewing history and preferences

    Context Gathering: Includes current mood, time, and available content

    AI Processing: Gemini processes context and generates suggestions

    Filtering: Results filtered by availability and user restrictions

    Personalization: Final ranking based on user's unique profile

External Integrations

TMDB (The Movie Database)

    Purpose: Primary source for movie/TV metadata

    Data Sync: Periodic synchronization of popular content

    Rate Limits: Respects API limits with intelligent caching

Media Servers

    Jellyfin: Open-source media server integration

    Plex: Commercial media server support

    Features: Library scanning, availability checking, metadata syncing

Download Automation

    Radarr: Movie download automation

    Sonarr: TV show download automation

    Features: Automated requests, quality profile selection, monitoring

Performance Considerations

Caching Strategy

    Database Caching: Redis for session data and frequent queries

    API Response Caching: TMDB responses cached to reduce API calls

    Static File Caching: CDN-ready static file serving

Optimization Techniques

    Database Indexing: Optimized indexes for frequent queries

    Query Optimization: Efficient Django ORM usage

    Lazy Loading: Deferred loading of heavy resources

    Pagination: API responses paginated for performance

Deployment Architecture

Container Structure

Code snippet

flowchart TD
    DockerContainer[Docker Container]
    subgraph Inside Docker
        Nginx(Nginx - Reverse Proxy)
        DjangoApp(Django Application - Gunicorn)
        PostgreSQL(PostgreSQL Database)
        Redis(Redis Cache)
    end

    DockerContainer --&gt; Nginx
    Nginx --&gt; DjangoApp
    DjangoApp --&gt; PostgreSQL
    DjangoApp --&gt; Redis
```
