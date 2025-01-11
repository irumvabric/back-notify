from django.http import JsonResponse
from django.shortcuts import render
import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view 
from django.contrib.auth.models import User
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken


from .serializers import WeatherDataSerializer
from .serializers import UserPreferencesSerializer
from .serializers import HistorySerializer
from .serializers import LocationSerializer
from .serializers import SettingsSerializer

from .models import *

from django.core.mail import send_mail
from django.core.signing import Signer, BadSignature
from django.conf import settings
from django.contrib.auth import get_user_model

signer = Signer()


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    if User.objects.filter(username=username).exists() and User.objects.filter(email=email).exists():
        return Response({'error': 'Cet utilisateur existe déjà.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create(
        first_name = first_name,
        last_name = last_name,
        username=username,
        password=make_password(password),
        email=email,
        is_active=False  # Désactiver jusqu'à la vérification de l'email
    )

    send_verification_email(user)  # Envoi de l'email de vérification


    return Response({'message': 'Utilisateur créé avec succès. Vérifiez votre email.'}, status=status.HTTP_201_CREATED)



@api_view(['POST'])
def add_weather_data(request):
    location_name = request.data.get('location_name')
    user_id = request.data.get('user_id')
    weather_data_id = request.data.get('weather_data_id')

    # Fetch user and weather data objects
    try:
        user = User.objects.get(id=user_id)
        weather_data = WeatherData.objects.get(id=weather_data_id)
    except (User.DoesNotExist, WeatherData.DoesNotExist) as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Create History entry
    history = History.objects.create(
        location_name=location_name,
        user=user,
        weather_data=weather_data
    )

    # Optional: Serialize and return the created History object
    serializer = HistorySerializer(history)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'username', 'email']

@api_view(['GET'])
@permission_classes([AllowAny])
def get_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_authenticated_user(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data["refresh_token"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response(status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_authenticated_user(request):
    user = request.user
    user.username = request.data.get('username', user.username)
    user.email = request.data.get('email', user.email)

    if request.data.get('password'):
        user.password = make_password(request.data.get('password'))

    user.save()
    return Response({'message': 'Informations de l\'utilisateur modifiées avec succès.'}, status=status.HTTP_200_OK)


def send_verification_email(user):
    # Generate the verification token
    token = signer.sign(user.email)

    # Local and production links
    local_link = f"http://localhost:8000/api/verify-email/{token}"
    production_link = f"http://139.162.155.97:8542/api/verify-email/{token}"
    
    # Construct and send the email with both links
    subject = 'Vérification de votre email'
    message = (
        f'Cliquez sur le lien suivant pour vérifier votre email (environnement local) : {local_link}\n\n'
        f'Ou utilisez ce lien pour l\'environnement de production : {production_link}'
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [user.email])



@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, token):
    User = get_user_model()
    
    try:
        email = signer.unsign(token)
        user = User.objects.get(email=email)

        if user.is_active:
            return Response({'message': 'Votre email est déjà vérifié.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        return Response({'message': 'Votre email a été vérifié avec succès.'}, status=status.HTTP_200_OK)
    
    except (User.DoesNotExist, BadSignature):
        return Response({'error': 'Le lien de vérification est invalide.'}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

# WeatherDataListCreateView
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def weather_data(request):
    if request.method == 'GET':
        weather_data = WeatherData.objects.filter(user=request.user)
        serializer = WeatherDataSerializer(weather_data, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = WeatherDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


# UserPreferencesView
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_preferences(request):
    try:
        preferences = UserPreferences.objects.get(user=request.user)
    except UserPreferences.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserPreferencesSerializer(preferences)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = UserPreferencesSerializer(preferences, data=request.data, partial=request.method=='PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# HistoryListView
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def history_list(request):
    if request.method == 'GET':
        history = History.objects.filter(user=request.user)
        serializer = HistorySerializer(history, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = HistorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# LocationListCreateView
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def location_list(request):
    if request.method == 'GET':
        locations = Location.objects.filter(user=request.user)
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# SettingsListView
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def settings_list(request):
    settings = Settings.objects.all()
    serializer = SettingsSerializer(settings, many=True)
    return Response(serializer.data)

# get_weather (already in FBV style, just adding api_view decorator)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_weather(request):
    # Get coordinates from request parameters
    lat = request.data.get('lat')
    lon = request.data.get('lon')
    
    # Validate input parameters
    if not lat or not lon:
        return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)
    
    try:
        # Convert to float to validate coordinates
        lat = float(lat)
        lon = float(lon)
        
        # Validate coordinate ranges
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return JsonResponse({'error': 'Invalid coordinate values'}, status=400)
        
        # OpenWeatherMap API configuration
        api_key = settings.OPENWEATHER_API_KEY  # Make sure this is set in your settings.py
        url = f'http://api.openweathermap.org/data/2.5/weather'
        
        # Parameters for the API request
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'units': 'Celsius'  # Use metric units (Celsius, meters/sec)
        }
        
        # Make request to OpenWeatherMap API
        response = requests.get(url, params=params, timeout=5)  # 5 seconds timeout
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse the response
        weather_data = response.json()
        
        # Optional: Format the response to include only needed data
        formatted_response = {
            'temperature': weather_data['main']['temp'],
            'feels_like': weather_data['main']['feels_like'],
            'humidity': weather_data['main']['humidity'],
            'pressure': weather_data['main']['pressure'],
            'weather_description': weather_data['weather'][0]['description'],
            'wind_speed': weather_data['wind']['speed'],
            'city_name': weather_data['name'],
            'country': weather_data['sys']['country']
        }
        
        
        
        return JsonResponse(formatted_response)
        
    except ValueError:
        return JsonResponse({'error': 'Invalid coordinate format'}, status=400)
    except requests.Timeout:
        return JsonResponse({'error': 'Weather service timeout'}, status=504)
    except requests.RequestException as e:
        return JsonResponse({'error': f'Weather service error: {str(e)}'}, status=502)
    except KeyError as e:
        return JsonResponse({'error': f'Unexpected response format: {str(e)}'}, status=502)
    except Exception as e:
        # Log the unexpected error here
        return JsonResponse({'error': 'Internal server error'}, status=500)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_weather_data(request):
    # Retrieve coordinates from request data
    lat = request.data.get('lat')
    lon = request.data.get('lon')
    location_name = request.data.get('location_name', 'Unknown Location')

    # Validate input parameters
    if not lat or not lon:
        return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)

    try:
        # Convert to float for validation
        lat = float(lat)
        lon = float(lon)

        # Validate coordinate ranges
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return JsonResponse({'error': 'Invalid coordinate values'}, status=400)

        # OpenWeatherMap API configuration
        api_key = settings.OPENWEATHER_API_KEY
        url = 'http://api.openweathermap.org/data/2.5/weather'
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'units': 'metric'  # Using metric units (Celsius, meters/sec)
        }

        # Make request to OpenWeatherMap API
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()

        # Parse the response
        weather_data = response.json()

        # Format response data to save in WeatherData model
        weather_record = {
            'user': request.user,
            'location_name': location_name,
            'temperature': weather_data['main']['temp'],
            'humidity': weather_data['main']['humidity'],
            'wind_speed': weather_data['wind']['speed'],
            'condition': weather_data['weather'][0]['description'],
        }

        # Save weather data to WeatherData model
        weather_instance = WeatherData.objects.create(**weather_record)
        
        # Optionally serialize and return saved data
        saved_data = {
            'id': weather_instance.id,
            'user': weather_instance.user.id,
            'location_name': weather_instance.location_name,
            'temperature': weather_instance.temperature,
            'humidity': weather_instance.humidity,
            'wind_speed': weather_instance.wind_speed,
            'condition': weather_instance.condition,
            'timestamp': weather_instance.timestamp,
        }

        return JsonResponse(saved_data, status=status.HTTP_201_CREATED)

    except ValueError:
        return JsonResponse({'error': 'Invalid coordinate format'}, status=400)
    except requests.Timeout:
        return JsonResponse({'error': 'Weather service timeout'}, status=504)
    except requests.RequestException as e:
        return JsonResponse({'error': f'Weather service error: {str(e)}'}, status=502)
    except KeyError as e:
        return JsonResponse({'error': f'Unexpected response format: {str(e)}'}, status=502)
    except Exception as e:
        return JsonResponse({'error': 'Internal server error'}, status=500)


