from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Media

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ["id","order", "name", "media_type"]
    list_filter =  ['media_type']
    search_fields = ['name']