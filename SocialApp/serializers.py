from dataclasses import fields
from pyexpat import model

from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework_recursive.fields import RecursiveField

from SocialApp.models import Former, User, Post,  Comment, ReactionPost,Story,Friend,Lecturer,StoryMedia,PostMedia



class BaseModalUser(serializers.ModelSerializer):
    avatar_user = serializers.SerializerMethodField(source='avatar_user')
    def get_avatar_user(self, user):
        if user.avatar_user:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(user.avatar_user)
            return user.avatar_user.url
        return None

class UserSerializer(BaseModalUser):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'username', 'avatar_user', 'cover_photo', 'role', 'verified']
class StoryMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryMedia
        fields = ['media_type', 'media_file']
class StorySerializer(serializers.ModelSerializer):
    media_file = SerializerMethodField()
    user = UserSerializer()

    def get_media_file(self, instance):
        video_media = instance.media.filter(media_type='video').first()
        if video_media:
            return video_media.media_file.url + (".mp4")
        else:
            image_media = instance.media.filter(media_type='image')
            if image_media.exists():
                return [media.media_file.url for media in image_media]
        return None
    class Meta:
        model = Story
        fields = ['id', 'user', 'media_file','created_at']

class FormerSerializer(BaseModalUser):
    avatar_user = serializers.SerializerMethodField(source='avatar_user')

    def get_avatar_user(self, user):
        if user.avatar_user:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(user.avatar_user)
            return user.avatar_user.url
        return None
    class Meta(UserSerializer.Meta):
        model = Former
        fields = UserSerializer.Meta.fields
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True}
        }

class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = "__all__"
class LecturerSerializer(BaseModalUser):
    avatar_user = serializers.SerializerMethodField(source='avatar_user')
    def get_avatar_user(self, user):
        if user.avatar_user:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(user.avatar_user)
            return user.avatar_user.url
        return None
    class Meta(UserSerializer.Meta):
        model = Lecturer
        fields = UserSerializer.Meta.fields + ['stories']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True}
        }



class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'avatar_user', 'cover_photo', 'role']


class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    media_file = serializers.SerializerMethodField()
    reaction = serializers.SerializerMethodField()

    def get_media_file(self, post):
        media_files = post.media.all()
        media_file_urls = [media.media_file.url.replace("/https%3A/", "https://") for media in media_files]
        return media_file_urls

    def get_reaction(self, post):
        reaction = ReactionPost.objects.filter(post=post)
        reaction_serializer = ReactionSerializer(reaction, many=True)
        return reaction_serializer.data

    class Meta:
        model = Post
        fields = ['id', 'user', 'content', 'media_file', 'on_comment','created_at','reaction']


class ReactionSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()  # Custom field để hiển thị id của người dùng

    def get_user_id(self, obj):
        return obj.user.id
    class Meta:
        model = ReactionPost
        fields = ['id', 'user_id', 'reaction_type']

class CommentSerializer(serializers.ModelSerializer):
    have_replies = serializers.SerializerMethodField()
    def get_have_replies(self, obj):
        return Comment.objects.filter(parent_comment=obj).exists()
    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'comment', 'parent_comment', 'have_replies', 'created_at']


class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friend
        fields = '__all_'

