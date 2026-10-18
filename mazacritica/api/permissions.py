from rest_framework.permissions import BasePermission


def user_in_group(user, group_name):
    return bool(
        user
        and user.is_authenticated
        and user.groups.filter(name=group_name).exists()
    )


def user_is_editor(user):
    return user_in_group(user, 'editor')


def user_is_moderator(user):
    return user_in_group(user, 'moderator')


def user_can_moderate(user):
    return user_is_editor(user) or user_is_moderator(user)


class IsMemberOrEditor(BasePermission):
    message = 'Solo una persona registrada puede comentar.'

    def has_permission(self, request, view):
        return user_in_group(request.user, 'member') or user_is_editor(request.user)


class IsEditor(BasePermission):
    message = 'Solo el grupo editor puede modificar contenido editorial.'

    def has_permission(self, request, view):
        return user_is_editor(request.user)
