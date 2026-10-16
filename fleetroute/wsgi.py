"""
WSGI config for the FleetRoute project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fleetroute.settings")

application = get_wsgi_application()
