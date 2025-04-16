import uuid

from django.core.serializers import serialize
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import format_html
from django.utils.timezone import now
from ckeditor.fields import RichTextField
from .utils import get_client_ip
from core.storage_backends import PublicMediaStorage
from ..media.models import Media
from ..media.serializers import MediaSerializer
from django.utils.text import slugify


#Crear una funcion que permita guardar la imagen en el blog especifico
#creado por el usuario
def blog_thumbnail_directory(instance, filename):
    sanitized_title = instance.title.replace(" ","_")
    return "thumbnails/blog/{0}/{1}".format(sanitized_title, filename)

#Crear una funcion que permita guardar la imagen de una categoria especifica
def category_thumbnail_directory(instance, filename):
    sanitized_name = instance.name.replace(" ", "_")
    return "thumbnails/blog_categories/{0}/{1}".format(sanitized_name, filename)

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #parent: Se usa "self" para indicar que este campo es una clave foránea a la
    # misma tabla (Category). Esto significa que una categoría puede tener una
    # "categoría padre", formando una relación de categoría y subcategoría.
    # ejemplo: Electrónica
    # ├── Celulares
    # │   ├── iPhone
    # │   ├── Samsung
    # ├── Computadoras
    # │   ├── Laptops
    # │   ├── PCs de Escritorio
    parent = models.ForeignKey("self",related_name="children",
                               on_delete=models.CASCADE,blank=True, null=True)
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.ForeignKey(Media, on_delete=models.SET_NULL,
                                  related_name='blog_category_thumbnail', blank=True, null=True)
    #thumbnail = models.ImageField(upload_to=category_thumbnail_directory, blank=True, null=True)
    slug = models.CharField(max_length=128)
    #se define esta clase en los modelos para que se puedan leer de una manera
    #ordenada/correcta la clase en el admin manager django:
    def __str__(self):
        return self.name

    def thumbnail_preview(self):
        if self.thumbnail:
            serializer = MediaSerializer(instance=self.thumbnail)
            url = serializer.data.get('url')
            if url:
                return format_html('<img src="{}" style="width: 100px; height: auto; />',url)
        return 'No Thumbnail'
    thumbnail_preview.short_description = "Thumbnail Preview"

class CategoryView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_view')
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

class CategoryAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name='category_analytics')

    views = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    click_through_rate = models.FloatField(default=0)
    avg_time_on_page = models.FloatField(default=0)

    def _update_click_through_rate(self):
        if self.impressions > 0:
            self.click_through_rate = (self.clicks/self.impressions) * 100
        else:
            self.click_through_rate = 0
        self.save()

    def increment_click(self):
        self.clicks += 1
        self.save()
        self._update_click_through_rate()

    def increment_impression(self):
        self.impressions += 1
        self.save()
        self._update_click_through_rate()

    def increment_view(self, ip_address):
        #ip_address = get_client_ip(request)
        if not CategoryView.objects.filter(category=self.category, ip_address=ip_address).exists():
            CategoryView.objects.create(category=self.category, ip_address=ip_address)
            self.views +=1
            self.save()

class Post(models.Model):

    #Aqui se configura que cuando los usuarios hagan una peticion/request POST, el servicio
    #Solo devuelva los post establecidos como 'published'
    class PostObjects(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(status='published')

    status_options = (
        ('draft','Draft'),
        ('published', 'Published')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=128)
    description =  models.CharField(max_length=256)
    #views = models.PositiveIntegerField(default=0)  # Agregar el campo con valor predeterminado
    #Cuando se borre la categoria de este post, usando 'on_delete=models.PROTECT'
    # se proteje el post, es decir no se borra este post
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    content = RichTextField(blank=True, null=True)
    #thumbnail = models.ImageField(upload_to=blog_thumbnail_directory, storage=PublicMediaStorage())
    thumbnail = models.ForeignKey(Media, on_delete=models.SET_NULL,
                                  related_name='post_thumbnail', blank=True, null=True)

    keywords = models.CharField(max_length=128)
    slug = models.CharField(max_length=128)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=12, choices=status_options, default='draft')
    objects = models.Manager() #default manager
    postobjects = PostObjects() #custom manager

    #Para ver nuestro modelo ordenado en el admin manager Django, se definen clases meta:
    class Meta:
        ordering = ("status","-created_at")

    #se define esta clase en los modelos para que se puedan leer de una manera
    #ordenada/correcta la clase en el admin manager django:
    def __str__(self):
        return self.title

    def thumbnail_preview(self):
        if self.thumbnail:
            serializer = MediaSerializer(instance=self.thumbnail)
            url = serializer.data.get('url')
            if url:
                return format_html('<img src="{}" style="width: 100px; height: auto; />',url)
        return 'No Thumbnail'
    thumbnail_preview.short_description = "Thumbnail Preview"

class PostView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_view')
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

class PostAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='post_analytics')
    views = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    click_through_rate = models.FloatField(default=0)
    avg_time_on_page = models.FloatField(default=0)

    def increment_click(self):
        self.clicks += 1
        self.save()
        self._update_click_through_rate()

    def _update_click_through_rate(self):
        if self.impressions > 0:
            self.click_through_rate = (self.clicks/self.impressions) * 100
        else:
            self.click_through_rate = 0
        self.save()

    def increment_impression(self):
        self.impressions += 1
        self.save()
        self._update_click_through_rate()

    def increment_view(self, ip_address):
        #ip_address = get_client_ip(request)
        if not PostView.objects.filter(post=self.post, ip_address=ip_address).exists():
            PostView.objects.create(post=self.post, ip_address=ip_address)
            self.views +=1
            self.save()

class Heading(models.Model):
    """Crear una clase que permita crear un menu html del post"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #Cuando se borre el post, usando 'on_delete=models.PROTECT'
    # se proteje el heading, es decir no se borra este heading
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='headings')
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    level = models.IntegerField(
    choices=(
        (1,"H1"),
        (2,"H2"),
        (3,"H3"),
        (4,"H4"),
        (5,"H5"),
        (6,"H6"),
    ))
    order = models.PositiveIntegerField() #Solo permitir numeros positivos
    class Meta:
        ordering = ["order"]

    #Este es un metodo que se define cuando el modelo se guarda, en este caso, usamos
    # el metodo para definir un 'slug' cuando el usuario no lo define, usado el titulo
    # del post
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title) #slugify: Convierte los espacios en blanco en guiones '-'
        super().save(*args, **kwargs)

@receiver(post_save, sender=Post)
def create_post_analytics(sender, instance, created, **kwargs):
    if created:
        PostAnalytics.objects.create(post=instance)

@receiver(post_save, sender=Category)
def create_category_analytics(sender, instance, created, **kwargs):
    if created:
        CategoryAnalytics.objects.create(category=instance)