from rest_framework import serializers
from .models import (Post, Category, Heading, PostView, PostAnalytics, PostInteraction,
                     Comment, PostShare, PostLike, CategoryAnalytics)
from ..media.serializers import MediaSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class CategoryListSerializer(serializers.ModelSerializer):
    thumbnail = MediaSerializer()
    class Meta:
        model = Category
        fields = [
            'name',
            'slug',
            'thumbnail',
        ]

class CategoryAnalyticsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = CategoryAnalytics
        fields = ["id",
                  "category_name",
                  "views",
                  "impressions",
                  "clicks",
                  "click_trough_rate",
                  "avg_time_on_page",]

    def get_category_name(self,obj):
        return obj.category.name

class HeadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Heading
        fields = ["title",
                  "slug",
                  "level",
                  "order",
                  ]

class PostViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostView
        fields = "__all__"

class PostSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    headings = HeadingSerializer(many=True)
    view_count = serializers.SerializerMethodField()
    thumbnail = MediaSerializer()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = "__all__"

    def get_view_count(self,obj):
        return obj.post_analytics.views if obj.post_analytics else 0

    def get_user(self, obj):
        if obj.user:
            return {
                "id": obj.user.id,
                "username": obj.user.username,
                "email": obj.user.email,
            }
        return None


class PostListSerializer(serializers.ModelSerializer):
    category = CategoryListSerializer()
    view_count = serializers.SerializerMethodField()
    thumbnail = MediaSerializer()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "description",
            "thumbnail",
            "slug",
            "category",
            "view_count",
        ]

    def get_view_count(self,obj):
        return obj.post_analytics.views if obj.post_analytics else 0

class PostAnalyticsSerializer(serializers.ModelSerializer):
    post_title = serializers.SerializerMethodField()

    class Meta:
        model = PostAnalytics
        fields = ["id",
                  "post_title",
                  "impressions",
                  "clicks",
                  "click_trough_rate",
                  "avg_time_on_page",
                  "views",
                  "likes",
                  "comments",
                  "shares",
                  ]

    def get_post_title(self, obj):
        return obj.post.title

class PostInteractionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    post_title = serializers.SerializerMethodField()
    comment_content = serializers.SerializerMethodField()

    def get_post_title(self, obj):
        return obj.post.title

    def get_comment_content(self, obj):
        return obj.comment.content if obj.comment else None

    class Meta:
        model = PostInteraction
        fields = [
            "id",
            "user",
            "post",
            "post_title",
            "interaction_type",
            "interaction_category",
            "weight",
            "timestamp",
            "device_type",
            "ip_address",
            "hour_of_day",
            "day_of_week",
            "comment_content",
        ]

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    post_title = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    #replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "post",
            "post_title",
            "parent",
            "content",
            "created_at",
            "updated_at",
            "is_active",
            "replies_count",
        ]

    def get_post_title(self, obj):
        return obj.post.title

    def get_replies(self, obj):
        replies = obj.replies.filter(is_active=True)
        return CommentSerializer(replies, many=True).data

    def get_replies_count(self, obj):
        return obj.replies.filter(is_active=True).count()

class PostLikeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = PostLike
        fields = [
            "id",
            "post",
            "user",
            "timestamp",
        ]

class PostShareSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = PostShare
        fields = [
            "id",
            "post",
            "user",
            "platform",
            "timestamp",
        ]