"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('api/authentication/', include("apps.authentication.urls")),
    path('api/profile/', include("apps.user_profile.urls")),
    path('api/blog/', include('apps.blog.urls')),
    path('api/media/', include('apps.media.urls')),
    #path('api/newsletter/', include('apps.newsletter.urls')),
    
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    # path("auth/", include("djoser.social.urls")),
    path('admin/', admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
