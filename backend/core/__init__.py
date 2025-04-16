from __future__ import absolute_import, unicode_literals

# Este import asegura que celery.py se carga cuando Django arranca.
from .celery import app as celery_app

__all__ = ('celery_app',)