from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User

from .models import *


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class WeatherDataSerializer(ModelSerializer):
     class Meta:
        model = WeatherData
        fields = ['id', 'user', 'location_name', 'temperature', 'humidity', 'wind_speed', 'condition', 'timestamp']

        
class UserPreferencesSerializer(ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = ['id', 'user', 'unit', 'theme', 'notification_enabled']

class HistorySerializer(ModelSerializer):
    class Meta:
        model = History
        fields = ['id', 'user', 'location_name', 'weather_data', 'searched_at']

class LocationSerializer(ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'user', 'location_name', 'latitude', 'longitude','saved_at']

class SettingsSerializer(ModelSerializer):
    class Meta:
        model = Settings
        fields = ['id', 'name', 'value']