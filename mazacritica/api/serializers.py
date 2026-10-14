from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Note, Source, Tag


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
        )


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