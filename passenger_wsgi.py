import sys
import os

# Set the path to your Django project directory (where manage.py is)
PROJECT_HOME = os.path.dirname(os.path.abspath(__file__))
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

os.environ['DJANGO_SETTINGS_MODULE'] = 'expense_manager.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
