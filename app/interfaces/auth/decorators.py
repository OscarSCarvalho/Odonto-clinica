from functools import wraps
from flask import session, redirect, url_for, abort


def requer_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def requer_perfil(*perfis):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            if session.get('perfil') not in perfis:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator
