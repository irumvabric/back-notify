from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view # type: ignore
from django.contrib.auth.models import User
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.hashers import make_password

from django.core.mail import send_mail
from django.core.signing import Signer, BadSignature
from django.conf import settings
from django.contrib.auth import get_user_model

signer = Signer()


@api_view(['POST'])
def signup(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Cet utilisateur existe déjà.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create(
        username=username,
        password=make_password(password),
        email=email,
        is_active=False  # Désactiver jusqu'à la vérification de l'email
    )

    send_verification_email(user)  # Envoi de l'email de vérification

    return Response({'message': 'Utilisateur créé avec succès. Vérifiez votre email.'}, status=status.HTTP_201_CREATED)

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

@api_view(['GET'])
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
    token = signer.sign(user.email)
    verification_link = f"http://localhost:8000/api/verify-email/{token}"
    
    subject = 'Vérification de votre email'
    message = f'Cliquez sur le lien suivant pour vérifier votre email : {verification_link}'
    from_email = settings.DEFAULT_FROM_EMAIL
    
    send_mail(subject, message, from_email, [user.email])


@api_view(['GET'])
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
