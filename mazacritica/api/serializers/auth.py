import re

from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from api.models import UserProfile

NICKNAME_PATTERN = re.compile(r'[a-z0-9_]{3,30}')

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    nickname = serializers.CharField()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Ese correo ya está registrado.')
        return value

    def validate_nickname(self, value):
        normalized = value.strip().lower()
        if NICKNAME_PATTERN.fullmatch(normalized) is None:
            raise serializers.ValidationError(
                'El nickname debe tener de 3 a 30 caracteres y solo puede usar a-z, 0-9 y _.'
            )
        if (
            User.objects.filter(username=normalized).exists()
            or UserProfile.objects.filter(nickname=normalized).exists()
        ):
            raise serializers.ValidationError('Ese nickname ya está registrado.')
        return normalized

    def validate(self, attrs):
        candidate = User(username=attrs['nickname'], email=attrs['email'])
        try:
            validate_password(attrs['password'], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                if User.objects.filter(email__iexact=validated_data['email']).exists():
                    raise serializers.ValidationError({
                        'email': 'Ese correo ya está registrado.',
                    })
                user = User.objects.create_user(
                    username=validated_data['nickname'],
                    email=validated_data['email'],
                    password=validated_data['password'],
                )
                UserProfile.objects.create(
                    user=user,
                    nickname=validated_data['nickname'],
                )
                member_group, _created = Group.objects.get_or_create(name='member')
                user.groups.add(member_group)
        except IntegrityError:
            raise serializers.ValidationError({
                'email': 'Ese correo ya está registrado.',
            })
        return user
