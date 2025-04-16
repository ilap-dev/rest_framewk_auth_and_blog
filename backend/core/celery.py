from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

#Buscar la configuracion de Django y usarla en celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
#Definir el nombre de la aplicacion, en nuestro caso es core
app = Celery("core")
#Desactivar la configuracion de la ubicacion
app.conf.enable_utc = False
#Activar la configuracion de la ubicacion a una establecida por nosotros
app.conf.update(timezone="America/Mexico_City")

app.config_from_object("django.conf:settings", namespace="CELERY")
#Indicarle a celery que automaticamente encuentre las tareas que debe ejecutar
#En nuestras aplicaciones
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
