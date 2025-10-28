# cargodb/wsgi.py
import os
from dotenv import load_dotenv
from django.core.wsgi import get_wsgi_application

# Укажите путь к вашему файлу .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cargodb.settings")
application = get_wsgi_application()


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cargodb.settings")

application = get_wsgi_application()
