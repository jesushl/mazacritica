from datetime import date, datetime, timezone

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from api.models import (
    Candidacy,
    Candidate,
    Comment,
    CommentReport,
    Election,
    ElectionZone,
    ModerationAction,
    Note,
    Office,
    PostalCode,
    PostalCodeZoneMapping,
    Source,
    Tag,
    UserProfile,
)

NEUTRAL_STATUS_TAGS = (
    (
        'Señalamiento',
        'Existe un señalamiento público; no implica una conclusión probada.',
    ),
    (
        'Denuncia presentada',
        'Se ha presentado una denuncia ante una autoridad o institución.',
    ),
    (
        'Investigación en curso',
        'Existe una investigación abierta o reportada por una fuente.',
    ),
    (
        'Presunta irregularidad',
        'Se reporta una posible irregularidad sin resolución firme.',
    ),
    (
        'Proceso judicial',
        'El asunto se encuentra relacionado con un proceso judicial.',
    ),
    (
        'Resolución firme',
        'Existe una resolución oficial firme sobre el asunto.',
    ),
)


class Command(BaseCommand):
    help = 'Carga datos ficticios y deterministas para desarrollo local.'

    @transaction.atomic
    def handle(self, *args, **options):
        editor = self._user('editor_demo', 'editor_demo@example.test', 'editor')
        moderator = self._user(
            'moderator_demo',
            'moderator_demo@example.test',
            'moderator',
        )
        member = self._user('member_demo', 'member_demo@example.test', 'member')
        topic = self._tags()
        source = self._source()
        published = self._notes(editor, source, topic)
        visible = self._comments(published, member)
        self._report_and_moderation(visible, member, moderator)
        self._elections()
        self.stdout.write(self.style.SUCCESS('Datos ficticios de demostración listos.'))

    def _user(self, username, email, group_name):
        user, created = User.objects.update_or_create(
            username=username,
            defaults={'email': email, 'is_active': True},
        )
        if created or not user.has_usable_password():
            user.set_password('demo-segura-2026')
            user.save(update_fields=['password'])
        UserProfile.objects.update_or_create(
            user=user,
            defaults={'nickname': username},
        )
        group, _created = Group.objects.get_or_create(name=group_name)
        user.groups.set([group])
        return user

    def _tags(self):
        for name, description in NEUTRAL_STATUS_TAGS:
            Tag.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    'name': name,
                    'kind': Tag.Kind.STATUS,
                    'description': description,
                    'is_active': True,
                },
            )
        topic, _created = Tag.objects.update_or_create(
            slug='transparencia-ficticia',
            defaults={
                'name': 'Transparencia ficticia',
                'kind': Tag.Kind.TOPIC,
                'description': 'Tema ficticio para el entorno de desarrollo.',
                'is_active': True,
            },
        )
        return topic

    def _source(self):
        source, _created = Source.objects.update_or_create(
            url='https://example.test/fuente-ficticia',
            defaults={
                'name': 'Fuente ficticia de demostración',
                'publisher': 'Redacción ficticia',
                'reference_notes': 'Documento inventado para desarrollo.',
            },
        )
        return source

    def _notes(self, editor, source, topic):
        published, _created = Note.objects.update_or_create(
            slug='nota-publicada-ficticia',
            defaults={
                'title': 'Nota publicada ficticia',
                'excerpt': 'Resumen ficticio de una nota publicada.',
                'content': 'Contenido ficticio publicado para desarrollo.',
                'status': Note.EditorialStatus.PUBLISHED,
                'source': source,
                'author': editor,
                'published_at': datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
            },
        )
        published.tags.set([
            topic,
            Tag.objects.get(slug=slugify('Señalamiento')),
        ])
        Note.objects.update_or_create(
            slug='nota-borrador-ficticia',
            defaults={
                'title': 'Nota borrador ficticia',
                'excerpt': 'Borrador ficticio.',
                'content': 'Contenido ficticio todavía en borrador.',
                'status': Note.EditorialStatus.DRAFT,
                'source': source,
                'author': editor,
                'published_at': None,
            },
        )
        Note.objects.update_or_create(
            slug='nota-archivada-ficticia',
            defaults={
                'title': 'Nota archivada ficticia',
                'excerpt': 'Nota ficticia archivada.',
                'content': 'Contenido ficticio archivado.',
                'status': Note.EditorialStatus.ARCHIVED,
                'source': source,
                'author': editor,
                'published_at': datetime(2025, 11, 2, 12, 0, tzinfo=timezone.utc),
            },
        )
        return published

    def _comments(self, note, member):
        nickname = member.profile.nickname
        visible, _created = Comment.objects.update_or_create(
            note=note,
            parent=None,
            body='Comentario visible ficticio.',
            defaults={
                'author': member,
                'nickname': nickname,
                'status': Comment.Status.VISIBLE,
            },
        )
        Comment.objects.update_or_create(
            note=note,
            parent=None,
            body='Comentario pendiente ficticio.',
            defaults={
                'author': member,
                'nickname': nickname,
                'status': Comment.Status.PENDING,
            },
        )
        Comment.objects.update_or_create(
            note=note,
            parent=None,
            body='Comentario rechazado ficticio.',
            defaults={
                'author': member,
                'nickname': nickname,
                'status': Comment.Status.REJECTED,
            },
        )
        Comment.objects.update_or_create(
            note=note,
            parent=visible,
            body='Respuesta directa ficticia.',
            defaults={
                'author': member,
                'nickname': nickname,
                'status': Comment.Status.VISIBLE,
            },
        )
        return visible

    def _report_and_moderation(self, comment, member, moderator):
        CommentReport.objects.update_or_create(
            comment=comment,
            reporter=member,
            defaults={'status': CommentReport.Status.OPEN},
        )
        ModerationAction.objects.update_or_create(
            comment=comment,
            actor=moderator,
            status=ModerationAction.Status.VISIBLE,
        )

    def _elections(self):
        first, _created = Election.objects.update_or_create(
            slug='eleccion-ficticia-2027',
            defaults={
                'name': 'Elección ficticia 2027',
                'held_on': date(2027, 6, 6),
                'description': 'Proceso electoral inventado.',
            },
        )
        Election.objects.update_or_create(
            slug='eleccion-ficticia-2030',
            defaults={
                'name': 'Elección ficticia 2030',
                'held_on': date(2030, 6, 2),
                'description': 'Segundo proceso electoral inventado.',
            },
        )
        executive, _created = Office.objects.update_or_create(
            slug='presidencia-ficticia',
            defaults={
                'name': 'Presidencia ficticia',
                'power': Office.Power.EXECUTIVE,
            },
        )
        Office.objects.update_or_create(
            slug='diputacion-ficticia',
            defaults={
                'name': 'Diputación ficticia',
                'power': Office.Power.LEGISLATIVE,
            },
        )
        judicial, _created = Office.objects.update_or_create(
            slug='magistratura-ficticia',
            defaults={
                'name': 'Magistratura ficticia',
                'power': Office.Power.JUDICIAL,
            },
        )
        confirmed_candidate, _created = Candidate.objects.update_or_create(
            slug='candidata-ficticia-uno',
            defaults={'name': 'Candidata Ficticia Uno'},
        )
        withdrawn_candidate, _created = Candidate.objects.update_or_create(
            slug='candidato-ficticio-dos',
            defaults={'name': 'Candidato Ficticio Dos'},
        )
        north, _created = ElectionZone.objects.update_or_create(
            code='ZN-F01',
            defaults={'name': 'Zona ficticia norte'},
        )
        south, _created = ElectionZone.objects.update_or_create(
            code='ZN-F02',
            defaults={'name': 'Zona ficticia sur'},
        )
        Candidacy.objects.update_or_create(
            candidate=confirmed_candidate,
            election=first,
            office=executive,
            zone=north,
            defaults={'status': Candidacy.Status.CONFIRMED},
        )
        Candidacy.objects.update_or_create(
            candidate=withdrawn_candidate,
            election=first,
            office=judicial,
            zone=south,
            defaults={'status': Candidacy.Status.WITHDRAWN},
        )
        unmapped, _created = PostalCode.objects.update_or_create(code='99000')
        mapped, _created = PostalCode.objects.update_or_create(code='99020')
        PostalCodeZoneMapping.objects.update_or_create(
            postal_code=mapped,
            zone=north,
            valid_from=date(2024, 1, 1),
            defaults={
                'valid_to': date(2027, 12, 31),
                'source': 'Acuerdo ficticio de la zona norte',
            },
        )
        PostalCodeZoneMapping.objects.update_or_create(
            postal_code=mapped,
            zone=south,
            valid_from=date(2025, 1, 1),
            defaults={
                'valid_to': date(2028, 12, 31),
                'source': 'Acuerdo ficticio de la zona sur',
            },
        )
        unmapped.zone_mappings.all().delete()
