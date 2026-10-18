import re

from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import Comment, Note, Source, Tag, UserProfile

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
        with transaction.atomic():
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
        return user


def validate_comment_body(value):
    if value is None or not str(value).strip():
        raise serializers.ValidationError('El comentario no puede estar vacío.')
    if len(value) > 1000:
        raise serializers.ValidationError(
            'El comentario admite como máximo 1000 caracteres.'
        )
    return value


class CommentReadSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'note',
            'author',
            'parent',
            'nickname',
            'body',
            'status',
            'created_at',
            'updated_at',
            'replies',
        ]

    def get_replies(self, obj):
        if obj.parent_id:
            return []
        replies = [
            reply for reply in obj.replies.all()
            if reply.status == Comment.Status.VISIBLE
        ]
        replies.sort(key=lambda reply: (reply.created_at, reply.id))
        return CommentReadSerializer(replies, many=True).data


class CommentCreateSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(required=False, allow_blank=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Comment
        fields = ['body', 'parent', 'nickname']

    def validate_body(self, value):
        return validate_comment_body(value)

    def validate_parent(self, parent):
        if parent is None:
            return parent
        note = self.context['note']
        if parent.parent_id is not None:
            raise serializers.ValidationError(
                'Una respuesta no puede tener respuestas.'
            )
        if parent.note_id != note.id:
            raise serializers.ValidationError(
                'El comentario padre pertenece a otra nota.'
            )
        return parent

    def create(self, validated_data):
        validated_data.pop('nickname', None)
        user = self.context['request'].user
        return Comment.objects.create(
            note=self.context['note'],
            author=user,
            nickname=user.profile.nickname,
            status=Comment.Status.PENDING,
            **validated_data,
        )


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['body']

    def validate_body(self, value):
        return validate_comment_body(value)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'kind', 'description', 'is_active']
        read_only_fields = ['slug']


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = [
            'id',
            'name',
            'url',
            'publisher',
            'published_at',
            'reference_notes',
            'created_at',
        ]
        read_only_fields = ['created_at']


class NoteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.filter(is_active=True),
        many=True,
        required=False,
    )
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Note
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'content',
            'status',
            'source',
            'tags',
            'author',
            'published_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['slug', 'author', 'created_at', 'updated_at']

    def validate(self, attrs):
        status = attrs.get('status', getattr(self.instance, 'status', None))
        published_at = attrs.get(
            'published_at',
            getattr(self.instance, 'published_at', None),
        )
        if status == Note.EditorialStatus.PUBLISHED and not published_at:
            raise serializers.ValidationError({
                'published_at': (
                    'Una nota publicada debe tener fecha de publicación.'
                ),
            })
        return attrs