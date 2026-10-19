from django.contrib.auth.models import User
from rest_framework import permissions, serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import ProfileNicknameError, ensure_user_profile
from api.serializers.auth import RegisterSerializer

def _user_for_login(email, username):
    if email:
        lookup = {'email__iexact': str(email)}
    elif username:
        lookup = {'username__iexact': str(username)}
    else:
        return None
    try:
        return User.objects.get(**lookup)
    except (User.DoesNotExist, User.MultipleObjectsReturned):
        return None


def _account_payload(user, token):
    return {
        'token': token.key,
        'nickname': user.profile.nickname,
        'email': user.email,
        'groups': list(user.groups.order_by('name').values_list('name', flat=True)),
    }


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
            except serializers.ValidationError as exc:
                return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {
                    'id': user.id,
                    'email': user.email,
                    'nickname': user.profile.nickname,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password') or ''
        user = _user_for_login(email, username)
        if (
            user is None
            or not user.is_active
            or not user.check_password(password)
        ):
            return Response(
                {'detail': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            ensure_user_profile(user)
        except ProfileNicknameError as exc:
            return Response(
                {'detail': exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _created = Token.objects.get_or_create(user=user)
        return Response(_account_payload(user, token))


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        try:
            ensure_user_profile(user)
        except ProfileNicknameError as exc:
            return Response(
                {'detail': exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({
            'id': user.id,
            'email': user.email,
            'nickname': user.profile.nickname,
            'groups': list(
                user.groups.order_by('name').values_list('name', flat=True)
            ),
        })
