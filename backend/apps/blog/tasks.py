from celery import shared_task
import logging
import redis
from django.conf import settings

from .models import PostAnalytics, Post, CategoryAnalytics, Category

logger = logging.getLogger(__name__)

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=6379, db=0)

@shared_task
def increment_post_impressions(post_id):
    """Incrementa las impressiones del post asociado"""
    logger.info("Task to: Update Post Impressions")
    try:
        analytics, created = PostAnalytics.objects.get_or_create(post__id=post_id)
        analytics.increment_impression()
    except Exception as e:
        logger.info(f"Error incrementando las impresiones para el Post ID {post_id}:{str(e)}")


@shared_task
def increment_post_view_task(slug, ip_address):
    """Incrementa las vistas de un post"""
    try:
        post = Post.objects.get(slug=slug)
        post_analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        post_analytics.increment_view(ip_address)
    except Exception as e:
        logger.info(f"Error incrementing views for Post Slug {slug}:{str(e)}")


@shared_task
def sync_impressions_to_db():
    """Sincroniza las impresiones guardadas en redis con la base de datos de Posgress"""
    #Obtener las claves que tenemos en redis
    keys = redis_client.keys("post:impressions:*")
    for key in keys:
        try:
            # Decodificar y extraer el ID de la categoria desde la clave redis
            post_id = key.decode("utf-8").split(":")[-1]
            try:
                post = Post.objects.get(id=post_id)
            except Post.DoesNotExist:
                logger.info(f"Post with ID {post_id} does not exist")
                continue

            #Obtener Impresiones de Redis
            impressions = int(redis_client.get(key))
            if impressions == 0:
                redis_client.delete(key)
                continue

            #Obtener y crear instancia de category analytics
            analytics, created = PostAnalytics.objects.get_or_create(post=post)

            #Incrementar impresiones
            analytics.impressions += impressions
            analytics.save()
            # Actualizar la tasa de Clicks(CTR)
            analytics._update_click_through_rate()
            #Elimnar la clave de redis despues de sincronizar
            redis_client.delete(key)
        except Exception as e:
            logger.info(f"Error syncing impressions for {key}:{str(e)}")

@shared_task
def sync_category_impressions_to_db():
    """Sincroniza las impresiones guardadas en redis con la base de datos de Posgress"""
    #Obtener las claves que tenemos en redis
    keys = redis_client.keys("category:impressions:*")
    for key in keys:
        try:
            #Decodificar y extraer el ID de la categoria desde la clave redis
            category_id = key.decode("utf-8").split(":")[-1]
            #Validar que la categoria existe
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                logger.info(f"Category with ID {category_id} does not exist. ")
                continue

            #Obtener Impresiones de Redis
            impressions = int(redis_client.get(key))
            if impressions == 0:
                redis_client.delete(key)
                continue

            #Obtener y crear instancia de category analytics
            analytics, created = CategoryAnalytics.objects.get_or_create(category=category)
            #Imcrementar impressiones
            analytics.impressions += impressions
            analytics.save()
            #Actualizar la tasa de Clicks
            analytics._update_click_through_rate()
            #Eliminar la clave de redis
            redis_client.delete(key)
        except Exception as e:
            logger.info(f"Error syncing category impressions for {key}:{str(e)}")
