from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .family_views import (
    FamilyProfileViewSet,
    ContentFilterViewSet,
    ContentRequestViewSet,
    ProfileLimitsViewSet,
    ProfileActivityViewSet,
    ParentApprovedContentViewSet,
    ParentalDashboardViewSet,
)
from .family_group_views import (
    FamilyGroupViewSet,
    FamilyMembershipViewSet,
    UserContentFilterViewSet,
    UserContentRequestViewSet,
    UserLimitsViewSet,
    UserActivityViewSet,
    FamilyInvitationViewSet,
    FamilyManagementViewSet,
)

# Create API router
router = DefaultRouter()

# Legacy family profile endpoints
router.register(r'profiles', FamilyProfileViewSet, basename='family-profiles')
router.register(r'content-filters', ContentFilterViewSet, basename='content-filters')
router.register(r'content-requests', ContentRequestViewSet, basename='content-requests')
router.register(r'profile-limits', ProfileLimitsViewSet, basename='profile-limits')
router.register(r'profile-activities', ProfileActivityViewSet, basename='profile-activities')
router.register(r'approved-content', ParentApprovedContentViewSet, basename='approved-content')
router.register(r'dashboard', ParentalDashboardViewSet, basename='parental-dashboard')

# New family group endpoints
router.register(r'family-groups', FamilyGroupViewSet, basename='family-groups')
router.register(r'family-memberships', FamilyMembershipViewSet, basename='family-memberships')
router.register(r'user-content-filters', UserContentFilterViewSet, basename='user-content-filters')
router.register(r'user-content-requests', UserContentRequestViewSet, basename='user-content-requests')
router.register(r'user-limits', UserLimitsViewSet, basename='user-limits')
router.register(r'user-activities', UserActivityViewSet, basename='user-activities')
router.register(r'family-invitations', FamilyInvitationViewSet, basename='family-invitations')
router.register(r'family-management', FamilyManagementViewSet, basename='family-management')

# URL patterns
urlpatterns = [
    path('api/family/', include(router.urls)),
]