"""
URL configuration for notify_vac project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from notify import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/signup/', views.signup, name='signup'),
    path('api/users/', views.get_users, name='get_users'),
    path('api/user/', views.get_authenticated_user, name='get_authenticated_user'),
    path('api/user/update/', views.update_authenticated_user, name='update_authenticated_user'),
    path('api/user/history/', views.history_list, name='history_authenticated_user'),
    path('api/user/preferences/', views.user_preferences, name='preferences_authenticated_user'),
    path('api/user/weather_data/', views.weather_data, name='weather_authenticated_user'),
    path('api/user/location/', views.location_list, name='history_authenticated_user'),
    path('api/user/get_weather_data/', views.get_weather, name='get_weather_for_authenticated_user'),
    path('api/verify-email/<str:token>/', views.verify_email, name='verify-email'),
]
