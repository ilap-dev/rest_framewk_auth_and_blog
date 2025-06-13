import uuid
from ipaddress import ip_address

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework_api.views import StandardAPIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, APIException
import redis
from django.conf import settings
from django.utils.decorators import method_decorator

#Hacer cache predeterminado (1 minuto) que se guarda en redis
from django.views.decorators.cache import cache_page

#Hacer cache personalizada que se guarda en redis
from django.core.cache import cache
from unicodedata import category

from .models import (Post, Heading, PostAnalytics, Category, CategoryAnalytics, PostInteraction, PostView, Comment)
from .serializers import (PostListSerializer, PostSerializer, HeadingSerializer, CategoryListSerializer, CommentSerializer)
from core.permissions import HasValidAPIKey
from .utils import get_client_ip
from .tasks import increment_post_view_task
from faker import Faker
import random
from django.utils.text import slugify
from django.db.models import Q, F, Prefetch
from django.shortcuts import get_object_or_404
from apps.authentication.models import UserAccount
from utils.string_utils import sanitize_string

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=6379, db=0)

#class PostListView(ListAPIView):
#    queryset = Post.objects.all()
#    serializer_class = PostListSerializer

class PostListView(StandardAPIView):
    #Establecer un api key para permitir/denegar el uso de la solicitud HTTP
    #permission_classes = [HasValidAPIKey]

    def get(self, request, *args, **kwargs):
        try:
            search = request.query_params.get("search","").strip()
            sorting = request.query_params.get("sorting", None)
            ordering = request.query_params.get("ordering", None)
            categories = request.query_params.getlist("category", [])
            page = request.query_params.get("p","1")
            #cache_key = f"post_list:{search}:{sorting}:{ordering}:{categories}:{page}"
            cache_key = f"post_list:{search}:{sorting}:{ordering}"
            #HACER CACHE PERSONALIZADA
            #Verificar si los datos que se requieren estan en una cache guardada
            cached_posts = cache.get(cache_key)
            #si existe retornar la cache a la vista del usuario
            if cached_posts:
                if search != "":
                    search_lower = search.lower()
                    cached_posts = [
                        post for post in cached_posts
                        if search_lower in post.get('title','').lower()
                           or search_lower in post.get('description','').lower()
                           or search_lower in post.get('content','').lower()
                           or search_lower in post.get('keywords','').lower()
                    ]

                for post in cached_posts:
                    redis_client.incr(f"post:impressions:{post['id']}")
                return self.paginate(request, cached_posts)

            # si no existe, obtener los posts de la base de datos
            if search != "":
                posts = Post.postobjects.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(content__icontains=search) |
                    Q(keywords__icontains=search)
                )
            else:
                posts = Post.postobjects.all()
                #.select_related("category").prefetch_related(
                #    Prefetch("post_analytics", to_attr="analytics_cache")
                #))

            if not posts.exists():
                raise NotFound(detail="No Posts Found!")

            if sorting:
                if sorting == 'newest':
                    posts = posts.order_by("-created_at")
                elif sorting == 'recently_updated':
                    posts = posts.order_by("-updated_at")
                elif sorting == 'most_viewed':
                    posts = posts.annotate(popularity=F("post_analytics__views")).order_by("-popularity")
            if ordering:
                if ordering == 'az':
                    posts = posts.order_by("title")
                if ordering == 'za':
                    posts = posts.order_by("-title")

            #Serializamos los datos de los posts
            serialized_posts = PostListSerializer(posts, many=True).data

            #Guardar datos de los posts/la vista del usuario en la cache llamada "post_list"
            cache.set(cache_key, serialized_posts, timeout=(60 * 5) )

            for post in posts:
                #incrementar impressiones en redis
                redis_client.incr(f"post:impressions:{post.id}")
                #increment_post_impressions.delay(post.id)

            return self.paginate(request, serialized_posts)

        except Exception as e:
            raise APIException(detail=f"An Unexpected Error Ocurred: {str(e)}")

#class PostDetailView(RetrieveAPIView):
#    queryset = Post.objects.all()
#    serializer_class = PostSerializer
#    lookup_field = 'slug'

class PostDetailView(StandardAPIView):
    # Establecer un api key para permitir/denegar el uso de la solicitud HTTP
    #permission_classes = [HasValidAPIKey]

    def get(self, request):
        ip_address = get_client_ip(request)
        slug = request.query_params.get("slug")
        user = request.user if request.user.is_authenticated else None

        if not slug:
            raise NotFound(detail="A valid slug must be provided")

        try:
            #    increment_post_view_task.delay(cached_post['slug'], ip_address)
            #    return self.response(cached_post)
            #sino esta en cache, obtener el post de la base de datos
            cached_post = cache.get(f"post_detail:{slug}")
            if cached_post:
                serialized_post = PostSerializer(cached_post).data
                self._register_view_interaction(cached_post, ip_address,user)
                return self.response(serialized_post)

            post = Post.postobjects.get(slug=slug)
            serialized_post = PostSerializer(post).data
            #Guardar el post en la cache
            cache.set(f"post_detail:{slug}", post, timeout=60 * 5 )

            self._register_view_interaction(post, ip_address, user)

            ##return self.paginate(request, serialized_post)

        except Post.DoesNotExist:
            raise NotFound(detail="The request Post does not exist")
        except Exception as e:
            raise APIException(detail=f"An Unexpected Error Ocurred HERE: {str(e)}")

        return self.response(serialized_post)

    def _register_view_interaction(self, post, ip_address, user):

        if not PostView.objects.filter(post=post, ip_address=ip_address, user=user).exists():
            PostView.objects.create(post=post, ip_address=ip_address, user=user)
            try:
                PostInteraction.objects.create(
                    user=user,
                    post=post,
                    interaction_type="view",
                    ip_address=ip_address,
                )
            except Exception as e:
                raise ValueError(f"Error Creating Postinteraction: {e}")

            analytics, _ = PostAnalytics.objects.get_or_create(post=post)
            analytics.increment_metric('view')



class PostHeadingView(StandardAPIView):
    # Establecer un api key para permitir/denegar el uso de la solicitud HTTP
    #permission_classes = [HasValidAPIKey]
    def get(self, request):
        post_slug = request.query_params.get("slug")
        heading_objects = Heading.objects.filter(post__slug=post_slug)
        serialized_data = HeadingSerializer(heading_objects, many=True).data
        return self.response(serialized_data)

    # serializer_class = HeadingSerializer
    #HACER CACHE AUTOMATICA de 1 minuto
    # Incluir que nuestra pagina web mantega una cache en redis, permitiendo que nuestra vista sea mas rapida
    # Sin embargo las actualizaciones no se veran reflejadas hasta que se elimine el cache
    # aqui se mantiene la cache por un minuto (60 * 1) y luego se elimina automaticamente
    #@method_decorator(cache_page(60 * 1))
    #def get_queryset(self):
    #post_slug = self.kwargs.get('slug')
    #return Heading.objects.filter(post__slug = post_slug)

class IncrementPostClickView(StandardAPIView):
    # Establecer un api key para permitir/denegar el uso de la solicitud HTTP
    #permission_classes = [HasValidAPIKey]

    def post(self,request):
        """Incrementa el contador de clicks de un post basado en su slug"""
        data = request.data
        try:
            post = Post.postobjects.get(slug=data['slug'])
        except Post.DoesNotExist:
            raise NotFound(detail="The request post does not exist")

        try:
            post_analytics, created = PostAnalytics.objects.get_or_create(post=post)
            post_analytics.increment_click()
        except Exception as e:
            raise APIException(
                detail=f"An  Error Ocurred While updating Post Analytics: {str(e)}")
        return self.response({
            "message":"Click Incremented Successfully",
            "clicks": post_analytics.clicks
        })

class IncrementCategoryClickView(StandardAPIView):
    # Establecer un api key para permitir/denegar el uso de la solicitud HTTP
    #permission_classes = [HasValidAPIKey]

    def category(self,request):
        """Incrementa el contador de clicks de un post basado en su slug"""
        data = request.data
        try:
            category = Category.objects.get(slug=data['slug'])
        except Category.DoesNotExist:
            raise NotFound(detail="The request category does not exist")

        try:
            category_analytics, created = CategoryAnalytics.objects.get_or_create(category=category)
            category_analytics.increment_click()
        except Exception as e:
            raise APIException(
                detail=f"An  Error Ocurred While updating Category Analytics: {str(e)}")
        return self.response({
            "message":"Click Incremented Successfully",
            "clicks": category_analytics.clicks
        })

class ListPostCommentsView(StandardAPIView):
    def get(self, request):
        post_slug = request.query_params.get("slug", None)

        if not post_slug:
            raise NotFound(detail= "A valid post must be provided")

        try:
            post = Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise ValueError(f"Post: {post_slug} doesn't exist")
        #Obtener solo los comentarios principales
        comments = Comment.objects.filter(post=post, parent=None)
        serialized_comments = CommentSerializer(comments, many=True).data

        return self.paginate(request, serialized_comments)

class PostCommentViews(StandardAPIView):
    def post(self, request):
        post_slug = request.data.get("slug", None)
        user = request.user
        ip_address = get_client_ip(request)
        content = sanitize_string(request.data.get('content', None))

        if not post_slug:
            raise NotFound(detail= "A valid post must be provided")

        try:
            post = Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise ValueError(f"Post: {post_slug} doesn't exist")

        #crear comentario
        comment = Comment.objects.create(
            user=user,
            post=post,
            content=content
        )
        #Actualizar interaccion post
        self._register_comment_interaction(comment, post, ip_address, user)
        return self.response(f"Comment created for post {post_slug}")

    def put(self, request):
        comment_id = request.data.get('comment_id',None)
        user = request.user
        content = sanitize_string(request.data.get("content", None))

        if not comment_id:
            raise NotFound(detail= "A valid comment_id must be provided")
        try:
            comment = Comment.objects.get(id=comment_id, user=request.user)
        except Comment.DoesNotExist:
            raise ValueError(f"Comment with ID: {comment_id} and username: {user.username} doesn't exist")

        comment.content = content
        comment.save()
        return self.response(f"Comment with ID: {comment_id},  It's Content Updated Successfully")

    def delete(self, request):
        comment_id = request.query_params.get('comment_id',None)

        if not comment_id:
            raise NotFound(detail= "A valid comment_id must be provided")
        try:
            comment = Comment.objects.get(id=comment_id, user=request.user)
        except Comment.DoesNotExist:
            raise ValueError(f"Comment with ID: {comment_id} and username: {user.username} doesn't exist")
        comment.delete()

        return self.response("Comment delete Succesfully")

    def _register_comment_interaction(self, comment, post, ip_address, user):

        # Registrar la interacción tipo "comment"
        PostInteraction.objects.create(
            user=user,
            post=post,
            interaction_type="comment",
            comment=comment,
        )
        # Incrementar el contador de comentarios
        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.increment_metric("comments")

class CategoryListView(StandardAPIView):
    def get(self, request, *args, **kwargs):

        try:
            search = request.query_params.get("search", "").strip()
            cache_key = f"category_list:{search}"
            cached_categories = cache.get(cache_key)
            if cached_categories:
                if search != "":
                    search_lower = search.lower()
                    cached_categories = [
                        category for category in cached_categories
                        if search_lower in category.get('name','').lower()
                           or search_lower in category.get('description','').lower()
                           or search_lower in category.get('title','').lower()
                           or search_lower in category.get('slug', '').lower()
                    ]

                for category in cached_categories:
                    redis_client.incr(f"category:impressions:{category.id}")
                return self.paginate(request, cached_categories)

            categories = Category.objects.all()
            # si no existe, obtener los posts de la base de datos
            if search != "":
                categories = categories.filter(
                    Q(name__icontains=search) |
                    Q(description__icontains=search) |
                    Q(title__icontains=search) |
                    Q(slug__icontains=search)
                )


            if not categories.exists():
                raise NotFound(detail="No Categories Found!")

            serialized_categories = CategoryListSerializer(categories, many=True).data

            cache.set(cache_key, serialized_categories, timeout=(60 * 5))

            for category in categories:
                redis_client.incr(f"category:impressions:{category.id}")
            return  self.paginate(request, serialized_categories)

        except Exception as e:
            raise APIException(detail=f"An Unexpected Error Ocurred: {str(e)}")

class CategoryDetailView(StandardAPIView):
    def get(self, request):
        try:
            slug = request.query_params.get("slug", None)
            if not slug:
                return self.error("Missing Slug Parameter")

            category = get_object_or_404(Category, slug=slug)

            posts = Post.postobjects.filter(category=category).select_related("category").prefetch_related(
                Prefetch("post_analytics", to_attr="analytics_cache")
            )

            if not posts.exists():
                raise NotFound(detail=f"No Posts Found For Category '{category.name}' ")

            serialized_posts = PostListSerializer(posts, many=True).data

            return self.paginate(request, serialized_posts)
        except Exception as e:
            raise APIException(detail=f"An unexpected Error occurred: {str(e)}")

class GenerateFakePostsView(StandardAPIView):
    def get(self, request):
        fake = Faker()

        # asegurar que exista un editor
        user, _ = UserAccount.objects.get_or_create(
            username="test_editor",
            defaults={
                "email": "test_editor@example.com",
                "password": 'admin1',
                "is_staff": True,
            },
        )

        categories = list(Category.objects.all())
        if not categories:
            return self.response("No hay categorias disponibles para asignar a los posts",400)

        posts_to_generate = 100
        status_options = ["draft", "published"]
        for _ in range(posts_to_generate):
            title = fake.sentence(nb_words=6)
            user = UserAccount.objects.get(username="test_editor")
            post = Post(
                id=uuid.uuid4(),
                user=user,
                title=title,
                description = fake.sentence(nb_words=12),
                content=fake.paragraph(nb_sentences=5),
                keywords=", ".join(fake.words(nb=5)),
                slug=slugify(title),
                category=random.choice(categories),
                status=random.choice(status_options),
            )
            post.save()
        return self.response(f"{posts_to_generate} posts generados exitosamente.")

    def __str__(self):
        return self.user.username

class GenerateFakeAnalyticsView(StandardAPIView):
    def get(self, request):
        fake = Faker()

        posts = Post.objects.all()
        if not posts:
            return self.response({"error":"No hay posts disponibles para generar analiticas"}, status=400)

        analytics_to_generate = len(posts)
        for post in posts:
            views = random.randint(50,1000)
            impressions = views + random.randint(100,2000)
            clicks = random.randint(0, views)
            avg_time_on_page = round(random.uniform(10,300), 2)

            analytics, created = PostAnalytics.objects.get_or_create(post=post)
            analytics.views = views
            analytics.impressions = impressions
            analytics.clicks = clicks
            analytics.avg_time_on_page = avg_time_on_page
            analytics._update_click_through_rate()
            analytics.save()
        return self.response({"message": f"Analiticas generadas para {analytics_to_generate} posts."})

