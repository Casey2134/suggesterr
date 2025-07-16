from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
import json
from datetime import date

from .models import Movie, Genre, UserRating, UserWatchlist, MovieRecommendation
from .services import MovieService, RecommendationService
from .gemini_service import GeminiService


class MovieModelTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name='Action', tmdb_id=28)
        self.movie = Movie.objects.create(
            title='Test Movie',
            overview='Test overview',
            release_date=date(2023, 1, 1),
            tmdb_id=12345,
            vote_average=7.5,
            vote_count=1000,
            popularity=85.5
        )
        self.movie.genres.add(self.genre)

    def test_movie_creation(self):
        self.assertEqual(self.movie.title, 'Test Movie')
        self.assertEqual(self.movie.tmdb_id, 12345)
        self.assertEqual(self.movie.vote_average, 7.5)
        self.assertTrue(self.movie.genres.filter(name='Action').exists())

    def test_movie_str(self):
        expected_str = 'Test Movie (2023)'
        self.assertEqual(str(self.movie), expected_str)

    def test_genre_str(self):
        self.assertEqual(str(self.genre), 'Action')


class UserRatingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.movie = Movie.objects.create(
            title='Test Movie',
            tmdb_id=12345
        )
        self.rating = UserRating.objects.create(
            user=self.user,
            movie=self.movie,
            rating=8
        )

    def test_rating_creation(self):
        self.assertEqual(self.rating.rating, 8)
        self.assertEqual(self.rating.user, self.user)
        self.assertEqual(self.rating.movie, self.movie)

    def test_rating_str(self):
        expected_str = 'testuser - Test Movie: 8/10'
        self.assertEqual(str(self.rating), expected_str)

    def test_unique_user_movie_constraint(self):
        # Trying to create another rating for the same user and movie should fail
        with self.assertRaises(Exception):
            UserRating.objects.create(
                user=self.user,
                movie=self.movie,
                rating=9
            )


class MovieAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.genre = Genre.objects.create(name='Action', tmdb_id=28)
        self.movie = Movie.objects.create(
            title='Test Movie',
            overview='Test overview',
            release_date=date(2023, 1, 1),
            tmdb_id=12345,
            vote_average=7.5,
            vote_count=1000,
            popularity=85.5
        )
        self.movie.genres.add(self.genre)

    def test_get_movies_list(self):
        url = reverse('movie-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Movie')

    def test_get_movie_detail(self):
        url = reverse('movie-detail', kwargs={'pk': self.movie.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Movie')
        self.assertEqual(response.data['tmdb_id'], 12345)

    def test_search_movies(self):
        url = reverse('movie-list')
        response = self.client.get(url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_genre(self):
        url = reverse('movie-list')
        response = self.client.get(url, {'genre': 'Action'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_available_only(self):
        self.movie.available_on_jellyfin = True
        self.movie.save()
        
        url = reverse('movie-list')
        response = self.client.get(url, {'available_only': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_popular_movies_endpoint(self):
        url = reverse('movie-popular')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_top_rated_movies_endpoint(self):
        self.movie.vote_count = 150  # Meet minimum vote count
        self.movie.save()
        
        url = reverse('movie-top-rated')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_movies_by_genre_endpoint(self):
        url = reverse('movie-by-genre')
        response = self.client.get(url, {'genre': 'Action'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_movies_by_genre_missing_parameter(self):
        url = reverse('movie-by-genre')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_movie_unauthenticated(self):
        url = reverse('movie-request-movie', kwargs={'pk': self.movie.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('movies.services.RadarrService.request_movie')
    def test_request_movie_authenticated(self, mock_request):
        mock_request.return_value = True
        
        self.client.force_authenticate(user=self.user)
        url = reverse('movie-request-movie', kwargs={'pk': self.movie.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.movie.refresh_from_db()
        self.assertTrue(self.movie.requested_on_radarr)


class UserRatingAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.movie = Movie.objects.create(
            title='Test Movie',
            tmdb_id=12345
        )
        self.client.force_authenticate(user=self.user)

    def test_create_rating(self):
        url = reverse('userrating-list')
        data = {
            'movie_id': self.movie.id,
            'rating': 8
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserRating.objects.count(), 1)

    def test_get_user_ratings(self):
        UserRating.objects.create(
            user=self.user,
            movie=self.movie,
            rating=8
        )
        
        url = reverse('userrating-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_rating_requires_authentication(self):
        self.client.force_authenticate(user=None)
        url = reverse('userrating-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MovieServiceTest(TestCase):
    def setUp(self):
        self.movie_service = MovieService()
        self.genre = Genre.objects.create(name='Action', tmdb_id=28)

    @patch('movies.services.TMDbMovie')
    @patch('movies.services.TMDbGenre')
    def test_sync_genres_from_tmdb(self, mock_tmdb_genre, mock_tmdb_movie):
        mock_genre_instance = MagicMock()
        mock_genre_instance.movie_list.return_value = [
            {'id': 28, 'name': 'Action'},
            {'id': 35, 'name': 'Comedy'}
        ]
        mock_tmdb_genre.return_value = mock_genre_instance
        
        result = self.movie_service.sync_genres_from_tmdb()
        
        self.assertTrue(result)
        self.assertEqual(Genre.objects.count(), 2)
        self.assertTrue(Genre.objects.filter(name='Comedy', tmdb_id=35).exists())

    @patch('movies.services.TMDbMovie')
    def test_sync_popular_movies(self, mock_tmdb_movie):
        mock_movie_instance = MagicMock()
        mock_movie_instance.popular.return_value = [
            {
                'id': 12345,
                'title': 'Test Movie',
                'original_title': 'Test Movie',
                'overview': 'Test overview',
                'release_date': '2023-01-01',
                'poster_path': '/test.jpg',
                'backdrop_path': '/test_bg.jpg',
                'vote_average': 7.5,
                'vote_count': 1000,
                'popularity': 85.5,
                'genre_ids': [28]
            }
        ]
        mock_tmdb_movie.return_value = mock_movie_instance
        
        result = self.movie_service.sync_popular_movies(pages=1)
        
        self.assertTrue(result)
        self.assertEqual(Movie.objects.count(), 1)
        movie = Movie.objects.first()
        self.assertEqual(movie.title, 'Test Movie')
        self.assertEqual(movie.tmdb_id, 12345)

    def test_create_or_update_movie_from_tmdb(self):
        tmdb_data = {
            'id': 12345,
            'title': 'Test Movie',
            'original_title': 'Test Movie',
            'overview': 'Test overview',
            'release_date': '2023-01-01',
            'poster_path': '/test.jpg',
            'backdrop_path': '/test_bg.jpg',
            'vote_average': 7.5,
            'vote_count': 1000,
            'popularity': 85.5,
            'genre_ids': [28]
        }
        
        movie = self.movie_service.create_or_update_movie_from_tmdb(tmdb_data)
        
        self.assertIsNotNone(movie)
        self.assertEqual(movie.title, 'Test Movie')
        self.assertEqual(movie.tmdb_id, 12345)
        self.assertTrue(movie.genres.filter(tmdb_id=28).exists())


class RecommendationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.recommendation_service = RecommendationService()
        
        # Create test movies
        self.genre = Genre.objects.create(name='Action', tmdb_id=28)
        self.movie1 = Movie.objects.create(
            title='Movie 1',
            tmdb_id=1,
            popularity=90.0,
            vote_average=8.0
        )
        self.movie1.genres.add(self.genre)
        
        self.movie2 = Movie.objects.create(
            title='Movie 2',
            tmdb_id=2,
            popularity=85.0,
            vote_average=7.5
        )
        self.movie2.genres.add(self.genre)

    def test_generate_recommendations_new_user(self):
        recommendations = self.recommendation_service.generate_recommendations(self.user)
        
        # Should return popular movies for new users
        self.assertGreater(len(recommendations), 0)
        self.assertEqual(recommendations[0].user, self.user)

    def test_generate_recommendations_with_ratings(self):
        # Add some ratings for the user
        UserRating.objects.create(user=self.user, movie=self.movie1, rating=9)
        
        recommendations = self.recommendation_service.generate_recommendations(self.user)
        
        self.assertGreater(len(recommendations), 0)
        self.assertEqual(recommendations[0].user, self.user)

    def test_get_preferred_genres(self):
        # Create high-rated movies
        UserRating.objects.create(user=self.user, movie=self.movie1, rating=9)
        UserRating.objects.create(user=self.user, movie=self.movie2, rating=8)
        
        high_rated = UserRating.objects.filter(user=self.user, rating__gte=8)
        preferred_genres = self.recommendation_service._get_preferred_genres(high_rated)
        
        self.assertGreater(len(preferred_genres), 0)
        self.assertEqual(preferred_genres[0][0], self.genre)

    def test_calculate_similarity(self):
        user1_ratings = {1: 8, 2: 7, 3: 9}
        user2_ratings = {1: 9, 2: 6, 3: 8}
        common_movies = {1, 2, 3}
        
        similarity = self.recommendation_service._calculate_similarity(
            user1_ratings, user2_ratings, common_movies
        )
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, -1.0)
        self.assertLessEqual(similarity, 1.0)


class IntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_frontend_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Suggesterr')
        self.assertContains(response, 'Movie Recommendations')

    def test_api_endpoints_accessible(self):
        # Test that API endpoints are accessible
        endpoints = [
            '/api/genres/',
            '/api/movies/',
            '/api/movies/popular/',
            '/api/movies/top_rated/',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [200, 404])  # 404 is OK if no data


class AdminIntegrationTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client = Client()

    def test_admin_login(self):
        response = self.client.post('/admin/login/', {
            'username': 'admin',
            'password': 'adminpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful login

    def test_admin_movie_list(self):
        self.client.force_login(self.admin_user)
        response = self.client.get('/admin/movies/movie/')
        self.assertEqual(response.status_code, 200)


class GeminiServiceTVTest(TestCase):
    def setUp(self):
        self.gemini_service = GeminiService()

    @patch.object(GeminiService, '_make_request')
    @patch.object(GeminiService, '_search_tv_show_on_tmdb')
    def test_get_tv_mood_based_recommendations(self, mock_search_tv, mock_make_request):
        mock_make_request.return_value = '{"recommendations": [{"title": "Test Show", "year": 2022, "reason": "Feel-good"}]}'
        mock_search_tv.return_value = {"title": "Test Show", "year": 2022, "id": 1}
        result = self.gemini_service.get_tv_mood_based_recommendations('happy')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'Test Show')
        self.assertEqual(result[0]['ai_reason'], 'Feel-good')

    @patch.object(GeminiService, '_make_request')
    @patch.object(GeminiService, '_search_tv_show_on_tmdb')
    def test_get_personalized_tv_recommendations(self, mock_search_tv, mock_make_request):
        mock_make_request.return_value = '{"recommendations": [{"title": "Personalized Show", "year": 2021, "reason": "Recommended for you"}]}'
        mock_search_tv.return_value = {"title": "Personalized Show", "year": 2021, "id": 2}
        prefs = {"genres": ["comedy"], "mood": "happy", "year_range": "2020-2024"}
        result = self.gemini_service.get_personalized_tv_recommendations(prefs)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'Personalized Show')
        self.assertEqual(result[0]['ai_reason'], 'Recommended for you')

    @patch.object(GeminiService, '_make_request')
    @patch.object(GeminiService, '_search_tv_show_on_tmdb')
    def test_get_similar_tv_shows(self, mock_search_tv, mock_make_request):
        mock_make_request.return_value = '{"recommendations": [{"title": "Similar Show", "year": 2020, "reason": "Similar themes"}]}'
        mock_search_tv.return_value = {"title": "Similar Show", "year": 2020, "id": 3}
        result = self.gemini_service.get_similar_tv_shows('Some Show')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'Similar Show')
        self.assertEqual(result[0]['ai_reason'], 'Similar themes')
