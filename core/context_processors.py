iha ydef user_roles(request):
    user = request.user
    if not user.is_authenticated:
        return {}

    is_superadmin = user.is_superuser
    groups = set(user.groups.values_list('name', flat=True))

    user_branch = None
    if not is_superadmin and 'branch_admin' in groups:
        try:
            user_branch = user.profile.branch
        except Exception:
            pass

    is_accountant_only = (not is_superadmin) and ('accountant' in groups) and len(groups) == 1
    is_callcentre = 'call_centre_admin' in groups

    # O'quv bo'limi foydalanuvchisi — faqat students_manager/agent, superadmin emas
    is_school_only = (
        not is_superadmin and
        ('students_manager' in groups or 'students_agent' in groups) and
        not any(g in groups for g in ['accountant','hr','seller','production_manager','branch_admin','enrollment_agent','enrollment_manager'])
    )

    return {
        'is_superadmin':      is_superadmin,
        'is_accountant':      is_superadmin or 'accountant'         in groups,
        'is_accountant_only': is_accountant_only,
        'is_hr':              is_superadmin or 'hr'                 in groups,
        'is_seller':          is_superadmin or 'seller'             in groups,
        'is_branch_admin':    is_superadmin or 'branch_admin'       in groups,
        'is_production_mgr':  is_superadmin or 'production_manager' in groups,
        'is_enrollment':      is_superadmin or 'enrollment_agent'   in groups or 'enrollment_manager' in groups,
        'is_students':        is_superadmin or 'students_agent'     in groups or 'students_manager' in groups or 'enrollment_agent' in groups or 'enrollment_manager' in groups,
<<<<<<< HEAD
        'is_callcentre':      is_superadmin or is_callcentre,
=======
        'is_cc_admin':        is_superadmin or 'callcenter_admin'   in groups or 'callcenter_supervisor' in groups,
        'is_school_only':     is_school_only,
>>>>>>> 235c534415dec3cf0e5950a41d3f0293594dd271
        'user_branch':        user_branch,
    }
