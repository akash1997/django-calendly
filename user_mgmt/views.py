from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView

from django.contrib.auth.models import User
from django.db import transaction


class PersonLoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response(
                data="Invalid login data, please try again!", status=HTTP_401_UNAUTHORIZED
            )
        else:
            user = serializer.validated_data['user']
            token = Token.objects.get(user=user)
            return Response(data={"token": token.key}, status=HTTP_200_OK)


class PersonRegisterView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            email = request.data['email']
            password = request.data['password']
        except:
            return Response(data="Invalid register data received!", status=HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=email).exists():
            return Response(data="This email is already registered!", status=HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            user = User.objects.create_user(username=email, email=email, password=password)
            Token.objects.create(user=user)
            return Response(data={"id": user.id}, status=HTTP_200_OK)
