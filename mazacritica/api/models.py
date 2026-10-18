from django.conf import settings
from django.db import models
from django.utils.text import slugify


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
