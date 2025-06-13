from django.urls import path
from .views import (PostListView,
                    PostDetailView,
                    PostHeadingView,
                    IncrementPostClickView,
                    CategoryListView,
                    CategoryDetailView,
                    GenerateFakePostsView,
                    GenerateFakeAnalyticsView,
                    IncrementCategoryClickView,
                    PostCommentViews, ListPostCommentsView
                    )

urlpatterns = [
    path('generate_posts/',GenerateFakePostsView.as_view()),
    path('generate_analytics/',GenerateFakeAnalyticsView.as_view()),
    path('posts/',PostListView.as_view(), name='post-list'),
    path('post/',PostDetailView.as_view(), name='post-detail'),
    path('post/headings/',PostHeadingView.as_view(), name='post-headings'),
    path('post/increment_click/',IncrementPostClickView.as_view(), name='increment-post-click'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('category/posts/', CategoryDetailView.as_view(), name='category-posts'),
    path('category/increment_click/', IncrementCategoryClickView.as_view(), name='increment-category-click'),
    path('post/comment/', PostCommentViews.as_view()),
    path('post/comments/', ListPostCommentsView.as_view()),
]