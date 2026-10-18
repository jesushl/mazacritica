import re

from django.conf import settings
from django.db import models
from django.utils.text import slugify

NICKNAME_PATTERN = re.compile(r'[a-z0-9_]{3,30}')


class ProfileNicknameError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def ensure_user_profile(user):
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        nickname = (user.username or '').strip().lower()
        if NICKNAME_PATTERN.fullmatch(nickname) is None:
            raise ProfileNicknameError(
                'El nombre de usuario no puede usarse como nickname.'
            )
        if UserProfile.objects.filter(nickname=nickname).exists():
            raise ProfileNicknameError('Ese nickname ya está registrado.')
        profile = UserProfile.objects.create(user=user, nickname=nickname)
        user.profile = profile
        return profile


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    nickname = models.CharField(max_length=30, unique=True)

    def save(self, *args, **kwargs):
        self.nickname = self.nickname.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nickname


class Tag(models.Model):
    class Kind(models.TextChoices):
        TOPIC = 'topic', 'Tema'
        STATUS = 'status', 'Estado'

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.TOPIC,
    )
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Source(models.Model):
    name = models.CharField(max_length=160)
    url = models.URLField(unique=True)
    publisher = models.CharField(max_length=160, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    reference_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.name


class Note(models.Model):
    class EditorialStatus(models.TextChoices):
        DRAFT = 'draft', 'Borrador'
        PUBLISHED = 'published', 'Publicada'
        ARCHIVED = 'archived', 'Archivada'

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    excerpt = models.CharField(max_length=320, blank=True)
    content = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=EditorialStatus.choices,
        default=EditorialStatus.DRAFT,
    )
    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
        related_name='notes',
    )
    tags = models.ManyToManyField(Tag, related_name='notes', blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_notes',
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Comment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        VISIBLE = 'visible', 'Visible'
        REJECTED = 'rejected', 'Rechazado'

    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='comments',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )
    nickname = models.CharField(max_length=30)
    body = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.nickname}: {self.body[:40]}'


class CommentReport(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Abierto'
        CLOSED = 'closed', 'Cerrado'

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='reports',
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='comment_reports',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['comment', 'reporter'],
                condition=models.Q(status='open'),
                name='unique_open_comment_report_per_member',
            ),
        ]

    def __str__(self):
        return f'Reporte de {self.reporter_id} sobre {self.comment_id}'


class ModerationAction(models.Model):
    class Status(models.TextChoices):
        VISIBLE = 'visible', 'Visible'
        REJECTED = 'rejected', 'Rechazado'

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='moderation_actions',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='moderation_actions',
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.actor_id} marcó {self.comment_id} como {self.status}'


class Election(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    held_on = models.DateField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['held_on', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Office(models.Model):
    class Power(models.TextChoices):
        EXECUTIVE = 'executive', 'Ejecutivo'
        LEGISLATIVE = 'legislative', 'Legislativo'
        JUDICIAL = 'judicial', 'Judicial'

    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    power = models.CharField(max_length=20, choices=Power.choices)

    class Meta:
        ordering = ['power', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Candidate(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ElectionZone(models.Model):
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=40, unique=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code


class PostalCode(models.Model):
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code


class Candidacy(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'confirmed', 'Confirmada'
        UNCONFIRMED = 'unconfirmed', 'Sin confirmar'
        WITHDRAWN = 'withdrawn', 'Retirada'

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.PROTECT,
        related_name='candidacies',
    )
    election = models.ForeignKey(
        Election,
        on_delete=models.PROTECT,
        related_name='candidacies',
    )
    office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        related_name='candidacies',
    )
    zone = models.ForeignKey(
        ElectionZone,
        on_delete=models.PROTECT,
        related_name='candidacies',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )

    class Meta:
        ordering = ['election', 'office', 'candidate']
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'election', 'office', 'zone'],
                name='unique_candidacy_candidate_election_office_zone',
            ),
        ]

    def __str__(self):
        return f'{self.candidate} / {self.office}'


class PostalCodeZoneMapping(models.Model):
    postal_code = models.ForeignKey(
        PostalCode,
        on_delete=models.CASCADE,
        related_name='zone_mappings',
    )
    zone = models.ForeignKey(
        ElectionZone,
        on_delete=models.PROTECT,
        related_name='postal_code_mappings',
    )
    source = models.CharField(max_length=255)
    valid_from = models.DateField()
    valid_to = models.DateField()

    class Meta:
        ordering = ['postal_code__code', 'zone__code', 'valid_from']
        constraints = [
            models.UniqueConstraint(
                fields=['postal_code', 'zone', 'valid_from'],
                name='unique_postal_zone_valid_from',
            ),
        ]

    def __str__(self):
        return f'{self.postal_code} → {self.zone}'
