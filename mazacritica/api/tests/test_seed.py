from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db.models import Count
from django.test import TestCase

from api.models import (
    Candidacy,
    Candidate,
    Comment,
    CommentReport,
    Election,
    ModerationAction,
    Note,
    Office,
    PostalCode,
    PostalCodeZoneMapping,
    Source,
    Tag,
    UserProfile,
)

class SeedDemoDataTests(TestCase):
    def test_seed_demo_data_is_idempotent_and_fictional(self):
        call_command('seed_demo_data')
        self._assert_fictional_shape()
        counts = self._snapshot()
        call_command('seed_demo_data')
        self.assertEqual(self._snapshot(), counts)
        self._assert_fictional_shape()

    def _snapshot(self):
        return (
            User.objects.count(),
            UserProfile.objects.count(),
            Tag.objects.count(),
            Source.objects.count(),
            Note.objects.count(),
            Comment.objects.count(),
            CommentReport.objects.count(),
            ModerationAction.objects.count(),
            Election.objects.count(),
            Office.objects.count(),
            Candidate.objects.count(),
            Candidacy.objects.count(),
            PostalCode.objects.count(),
            PostalCodeZoneMapping.objects.count(),
        )

    def _assert_fictional_shape(self):
        self.assertEqual(
            set(User.objects.values_list('username', flat=True)),
            {'editor_demo', 'moderator_demo', 'member_demo'},
        )
        for username, group_name in (
            ('editor_demo', 'editor'),
            ('moderator_demo', 'moderator'),
            ('member_demo', 'member'),
        ):
            user = User.objects.get(username=username)
            self.assertEqual(user.profile.nickname, username)
            self.assertTrue(user.email.endswith('@example.test'))
            self.assertEqual(user.groups.count(), 1)
            self.assertTrue(user.groups.filter(name=group_name).exists())
            self.assertEqual(Group.objects.get(name=group_name).user_set.count(), 1)

        for name in (
            'Señalamiento',
            'Denuncia presentada',
            'Investigación en curso',
            'Presunta irregularidad',
            'Proceso judicial',
            'Resolución firme',
        ):
            self.assertTrue(Tag.objects.filter(name=name, kind=Tag.Kind.STATUS).exists())
        self.assertGreaterEqual(Tag.objects.filter(kind=Tag.Kind.TOPIC).count(), 1)
        self.assertGreaterEqual(Source.objects.count(), 1)
        self.assertEqual(
            set(Note.objects.values_list('status', flat=True)),
            {
                Note.EditorialStatus.PUBLISHED,
                Note.EditorialStatus.DRAFT,
                Note.EditorialStatus.ARCHIVED,
            },
        )
        self.assertEqual(Note.objects.count(), 3)
        self.assertEqual(
            set(Comment.objects.filter(parent__isnull=True).values_list('status', flat=True)),
            {Comment.Status.VISIBLE, Comment.Status.PENDING, Comment.Status.REJECTED},
        )
        reply = Comment.objects.get(parent__isnull=False)
        self.assertIsNone(reply.parent.parent_id)
        self.assertEqual(Comment.objects.filter(parent__isnull=False).count(), 1)
        self.assertEqual(CommentReport.objects.count(), 1)
        self.assertEqual(ModerationAction.objects.count(), 1)
        self.assertEqual(Election.objects.count(), 2)
        self.assertEqual(
            set(Office.objects.values_list('power', flat=True)),
            {Office.Power.EXECUTIVE, Office.Power.LEGISLATIVE, Office.Power.JUDICIAL},
        )
        self.assertGreaterEqual(Candidate.objects.count(), 2)
        self.assertTrue(
            Candidacy.objects.filter(status=Candidacy.Status.WITHDRAWN).exists()
        )
        self.assertEqual(PostalCode.objects.filter(zone_mappings__isnull=True).count(), 1)
        mapped = PostalCode.objects.annotate(
            mapping_count=Count('zone_mappings'),
        ).get(mapping_count=2)
        self.assertEqual(mapped.zone_mappings.count(), 2)
        for mapping in mapped.zone_mappings.all():
            self.assertTrue(mapping.source)
            self.assertLessEqual(mapping.valid_from, mapping.valid_to)
