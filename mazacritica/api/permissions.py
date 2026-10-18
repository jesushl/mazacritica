from rest_framework.permissions import BasePermission


def user_is_editor(user):
    return bool(
        user
        and user.is_authenticated
        and user.groups.filter(name='editor').exists()
    )


class IsEditor(BasePermission):
    message = 'Solo el grupo editor puede modificar contenido editorial.'

    def has_permission(self, request, view):
        return user_is_editor(request.user)
