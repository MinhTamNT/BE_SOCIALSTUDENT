from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework_recursive.fields import RecursiveField

from SocialApp.models import Former, User, Post, Image, Comment, ReactionPost,Story,Friend,Lecturer

class UserSerializer(serializers.ModelSerializer):
    avatar_user = serializers.SerializerMethodField(source='avatar_user')
    def get_avatar_user(self, user):
        if user.avatar_user:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(user.avatar_user)
            return user.avatar_user.url
        return None
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'username', 'avatar_user', 'cover_photo', 'role', 'verified']
class StorySerializer(serializers.ModelSerializer):
    media_file = SerializerMethodField()
    user = UserSerializer()
    def get_media_file(self, instance):
        if instance.media.exists():
            return instance.media.first().media_file.url + ".mp4"
        return None
    class Meta:
        model = Story
        fields = ['id', 'user', 'media_file','created_at']

class FormerSerializer(serializers.ModelSerializer):

    class Meta(UserSerializer.Meta):
        model = Former
        fields = UserSerializer.Meta.fields
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True}
        }


class LecturerSerializer(serializers.ModelSerializer):

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


class ImageSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation
    class Meta:
        model = Image
        fields = ['image', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    image = SerializerMethodField()
    def get_image(self, obj):
        images = Image.objects.filter(post_id=obj.id)
        serializer = ImageSerializer(images, many=True).data
        return serializer
    class Meta:
        model = Post
        fields = ['id', 'user', 'title', 'content', 'image', 'on_comment']

class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReactionPost
        fields = ['id', 'post', 'user', 'reaction_type']

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

