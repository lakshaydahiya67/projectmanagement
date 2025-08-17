import logging
from functools import wraps
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required as django_login_required
from django.http import HttpResponse

logger = logging.getLogger(__name__)

# Use Django's built-in login_required decorator
# This is now just an alias for consistency with existing code
jwt_login_required = django_login_required

def class_login_required(cls):
    """
    Decorator for class-based views that checks for authentication.
    Applies login_required to all handler methods.
    """
    for name, method in cls.__dict__.items():
        # Check if it's a handler method
        if name.lower() in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'):
            setattr(cls, name, method_decorator(django_login_required)(method))
    return cls

# Alias for backward compatibility
class_jwt_login_required = class_login_required