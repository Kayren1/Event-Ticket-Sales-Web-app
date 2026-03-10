"""
WSGI config for paperweight project.

It exposes the WSGI callable as a module-level variable named `application`.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/

This file is used by:
- Gunicorn: gunicorn paperweight.wsgi:application
- Vercel: api/index.py imports this application
"""

import os
from django.core.wsgi import get_wsgi_application

# Ensure Django settings module is set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paperweight.settings')

# Get the WSGI application
application = get_wsgi_application()
