def sync_user_flags(user, role, approved):
    """Synchronize Django auth flags from a member role and approval state."""
    if role == 'admin' and approved:
        user.is_staff = True
        user.is_superuser = True
    elif role == 'collaborator' and approved:
        user.is_staff = True
        user.is_superuser = False
    else:
        user.is_staff = False
        user.is_superuser = False