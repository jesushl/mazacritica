from django.contrib.auth.models import Group, User

from api.models import UserProfile


def create_group_user(username, email, password, group_name, nickname=None):
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
    user.groups.add(Group.objects.get_or_create(name=group_name)[0])
    if nickname is not None:
        UserProfile.objects.create(user=user, nickname=nickname)
    return user
