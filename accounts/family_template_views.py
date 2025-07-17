from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .family_models import FamilyProfile
from .family_group_models import FamilyGroup, FamilyMembership


@login_required
def family_profiles_view(request):
    """Main family profiles management page"""
    profiles = FamilyProfile.objects.filter(parent_user=request.user)
    context = {
        'profiles': profiles,
        'profile_count': profiles.count(),
        'max_profiles': 6,
        'active_profile': request.session.get('active_profile_id'),
    }
    return render(request, 'accounts/family_profiles.html', context)


@login_required
def parental_dashboard_view(request):
    """Parental dashboard for monitoring all profiles"""
    profiles = FamilyProfile.objects.filter(parent_user=request.user)
    context = {
        'profiles': profiles,
    }
    return render(request, 'accounts/parental_dashboard.html', context)


@login_required
def profile_settings_view(request, profile_id):
    """Settings page for individual profile"""
    try:
        profile = FamilyProfile.objects.get(id=profile_id, parent_user=request.user)
    except FamilyProfile.DoesNotExist:
        return redirect('accounts:family_profiles')
    
    context = {
        'profile': profile,
    }
    return render(request, 'accounts/profile_settings.html', context)


@login_required
def content_requests_view(request):
    """View for managing content requests"""
    profiles = FamilyProfile.objects.filter(parent_user=request.user)
    context = {
        'profiles': profiles,
    }
    return render(request, 'accounts/content_requests.html', context)


@login_required
@require_http_methods(["POST"])
def switch_profile(request, profile_id):
    """Switch active profile"""
    try:
        profile = FamilyProfile.objects.get(id=profile_id, parent_user=request.user)
        request.session['active_profile_id'] = profile.id
        request.session['active_profile_name'] = profile.profile_name
        request.session['active_profile_age'] = profile.age
        return JsonResponse({
            'success': True,
            'profile_name': profile.profile_name,
            'profile_id': profile.id
        })
    except FamilyProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profile not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def clear_profile(request):
    """Clear active profile (switch back to parent)"""
    request.session.pop('active_profile_id', None)
    request.session.pop('active_profile_name', None)
    request.session.pop('active_profile_age', None)
    return JsonResponse({'success': True})


@login_required
def family_management_view(request):
    """New family management page for User-based family groups"""
    return render(request, 'accounts/family_management.html')


@login_required
def family_dashboard_view(request):
    """Family dashboard for monitoring all family members"""
    return render(request, 'accounts/family_dashboard.html')