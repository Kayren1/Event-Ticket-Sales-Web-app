"""
Vercel WSGI entry point for Django application.
This file is the serverless function handler for Vercel.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paperweight.settings')

# Setup Django
import django
django.setup()

# Import WSGI application
from paperweight.wsgi import application

# Export handler for Vercel
# Vercel will call this handler for each request
def handler(environ, start_response):
    """
    WSGI handler for Vercel.
    """
    return application(environ, start_response)
