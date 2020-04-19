from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView

from django.contrib.auth.models import User
from django.db import transaction

from .constants import ResponseMessages


class UserLoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        """Checks for the login details of the user and sends the token if successfully authenticated.

        Overrides the default Token Authentication View for customized responses.

        """
        serializer = self.serializer_class(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response(data=ResponseMessages.INVALID_LOGIN_DATA, status=HTTP_401_UNAUTHORIZED)
        else:
            user = serializer.validated_data['user']
            token = Token.objects.get(user=user)
            return Response(data={"token": token.key}, status=HTTP_200_OK)


class UserRegisterView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """Creates a new user and generates their token with the provided email and password.

        """
        try:
            email = request.data['email']
            password = request.data['password']
        except KeyError:
            return Response(data=ResponseMessages.INVALID_REGISTERATION_KEYS, status=HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=email).exists():
            return Response(data=ResponseMessages.ALREADY_REGISTERED, status=HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            user = User.objects.create_user(username=email, email=email, password=password)
            Token.objects.create(user=user)
            return Response(data={'id': user.id, 'username': user.username}, status=HTTP_201_CREATED)
