from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class WeatherData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location_name = models.CharField(max_length=255)
    temperature = models.FloatField()
    humidity = models.IntegerField()
    wind_speed = models.FloatField(null=True, blank=True)
    condition = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Weather in {self.location_name} for {self.user.email}"
    

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    unit = models.CharField(max_length=10, default='Celsius')
    theme = models.CharField(max_length=10, default='light')
    notification_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Preferences for {self.user.email}"
    

class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location_name = models.CharField(max_length=255)
    weather_data = models.ForeignKey(WeatherData, on_delete=models.CASCADE)
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Search history for {self.user.email}"


class Location(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location_name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Location: {self.location_name} for {self.user.email}"
    
class Settings(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"Setting: {self.name}"