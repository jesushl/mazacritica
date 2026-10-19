from rest_framework import serializers

from api.models import (
    Candidacy,
    Candidate,
    Election,
    ElectionZone,
    Office,
    PostalCode,
    PostalCodeZoneMapping,
)

class ElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ['id', 'name', 'slug', 'held_on', 'description']
        read_only_fields = ['slug']


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'name', 'slug', 'power']
        read_only_fields = ['slug']


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class ElectionZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectionZone
        fields = ['id', 'name', 'code']


class PostalCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostalCode
        fields = ['id', 'code']


class CandidacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidacy
        fields = ['id', 'candidate', 'election', 'office', 'zone', 'status']


class PostalCodeZoneMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostalCodeZoneMapping
        fields = ['id', 'postal_code', 'zone', 'source', 'valid_from', 'valid_to']

    def validate(self, attrs):
        valid_from = attrs.get('valid_from', getattr(self.instance, 'valid_from', None))
        valid_to = attrs.get('valid_to', getattr(self.instance, 'valid_to', None))
        if valid_from and valid_to and valid_from > valid_to:
            raise serializers.ValidationError({
                'valid_from': 'La vigencia inicial no puede ser posterior a la final.',
            })
        return attrs
