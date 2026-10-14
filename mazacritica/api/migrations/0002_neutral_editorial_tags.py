from django.db import migrations
from django.utils.text import slugify


NEUTRAL_TAGS = [
    (
        'Señalamiento',
        'status',
        'Existe un señalamiento público; no implica una conclusión probada.',
    ),
    (
        'Denuncia presentada',
        'status',
        'Se ha presentado una denuncia ante una autoridad o institución.',
    ),
    (
        'Investigación en curso',
        'status',
        'Existe una investigación abierta o reportada por una fuente.',
    ),
    (
        'Presunta irregularidad',
        'status',
        'Se reporta una posible irregularidad sin resolución firme.',
    ),
    (
        'Proceso judicial',
        'status',
        'El asunto se encuentra relacionado con un proceso judicial.',
    ),
    (
        'Resolución firme',
        'status',
        'Existe una resolución oficial firme sobre el asunto.',
    ),
]


def add_neutral_tags(apps, schema_editor):
    Tag = apps.get_model('api', 'Tag')
    for name, kind, description in NEUTRAL_TAGS:
        Tag.objects.get_or_create(
            slug=slugify(name),
            defaults={
                'name': name,
                'kind': kind,
                'description': description,
            },
        )


def remove_neutral_tags(apps, schema_editor):
    Tag = apps.get_model('api', 'Tag')
    Tag.objects.filter(
        slug__in=[slugify(name) for name, _, _ in NEUTRAL_TAGS],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_neutral_tags, remove_neutral_tags),
    ]
