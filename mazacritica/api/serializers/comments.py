from rest_framework import serializers

from api.models import Comment

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
