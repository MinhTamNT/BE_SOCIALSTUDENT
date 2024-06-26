import random

from django.core.cache import cache
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from rest_framework import viewsets, status, generics, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
import cloudinary.uploader

from BackendSocialFormer.celery import send_otp
# from .utils import *
from SocialApp import perms
from SocialApp.models import User, Post, PostMedia, Comment, ReactionPost,Story,Friend,StoryMedia
from SocialApp.serializers import FormerSerializer, LecturerSerializer, PostSerializer, CommentSerializer, \
    ReactionSerializer,StorySerializer,FriendSerializer,PostMediaSerializer


# Create your views here.
class UserViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = FormerSerializer
    parser_classes = [parsers.MultiPartParser, ]

    @action(methods=['GET', 'PUT'], detail=False, url_path='current-user')
    def current_user(self, request):
        try:
            user = request.user
            user_instance = User.objects.get(username=user)
            if request.method.__eq__('GET'):
                return Response(data=LecturerSerializer(user_instance, context={'request': request}).data,
                                status=status.HTTP_200_OK)
            elif request.method.__eq__('PUT'):
                for key, value in request.data.items():
                    setattr(user_instance, key, value)
                user_instance.save()
                return Response(data=LecturerSerializer(user_instance, context={'request': request}).data,
                                status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({'Error': 'Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountViewSet(viewsets.ViewSet):
    queryset = User.objects.all()

    @action(methods=['post'], detail=False, url_path='former/register')
    def former_register(self, request):
        try:
            data = request.data
            res = cloudinary.uploader.upload(data.get('avatar'), folder='avatar_user/')
            # res_cover_photo = cloudinary.uploader.upload('/static/media/default-cover-4.jpeg', folder='cover_photo/')
            new_former = User.objects.create_user(
                username=data.get('username'),
                password=data.get('password'),
                avatar_user=res['secure_url'],
                # cover_photo=res_cover_photo['secure_url'],
                email=data.get('email'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                role=User.Roles.FORMER
            )
            return Response(data=FormerSerializer(new_former, context={'request': request}).data,
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({'Error': 'Error creating user'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post'], detail=False, url_path='lecturer/register')
    def lecturer_register(self, request):
        try:
            data = request.data
            new_lecturer = User.objects.create_user(
                username=data.get('username'),
                password='ou@123',
                email=data.get('email'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                role=User.Roles.LECTURER,
                verified=True
            )
            return Response(data=LecturerSerializer(new_lecturer, context={'request': request}).data,
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({'Error': 'Error creating user'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post'], detail=False, url_path='change-password')
    def change_password(self, request):
        try:
            user = request.user
            if user.is_authenticated:
                old_password = request.data.get('old_password')
                new_password = request.data.get('new_password')
                if user.check_password(old_password):
                    user.set_password(new_password)
                    user.save()
                    return Response({"Password changed successfully"}, status=status.HTTP_200_OK)
                else:
                    print(user)
                    return Response({"Old password incorrect"}, status=status.HTTP_200_OK)
            else:
                return Response({"Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({'Error': 'Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post'], detail=False, url_path='reset-password')
    def reset_password(self, request):
        try:
            email = request.data.get('email')
            new_password = request.data.get('new_password')
            if email and new_password:
                user = User.objects.filter(email=email).first()
                user.set_password(new_password)
                user.save()
                return Response({"Password reset successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"Email and new password are required"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post'], detail=False, url_path='check-account')
    def check_account(self, request):
        try:
            user = request.date.get('username')
            email = request.data.get('email')
            if email and user:
                if user == User.objects.filter(username=user).first():
                    return JsonResponse({'message': 'username is already exists', 'code': '01'})
                if email == User.objects.filter(email=email).first():
                    return JsonResponse({'message': 'email is already exists', 'code': '02'})
                return JsonResponse({'message': 'Information is invalid', 'code': '00'})
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post'], detail=False, url_path='register/sent-otp')
    def sent_otp_new_account(self, request):
        try:
            user = request.data.get('username')
            email = request.data.get('email')
            if email and user:
                otp = random.randint(1000, 9999)
                cache.set(email, str(otp), timeout=60*5)
                send_otp.delay(receiver=email, otp=otp, username=user)
                return Response({}, status=status.HTTP_200_OK)
            else:
                return Response({"Email and username are required"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post'], detail=False, url_path='verify-email')
    def verify_email(self, request):
        try:
            if request.date.get('email') and request.date.get('otp'):
                email = request.data.get('email')
                otp = request.data.get('otp')
                cache_otp = cache.get(email)
                if cache_otp:
                    if cache_otp == otp:
                        return Response({"Email is valid"}, status=status.HTTP_200_OK)
                    else:
                        return Response({"Email is invalid"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"OTP is timeout"}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class PostViewSet(viewsets.ViewSet, generics.ListAPIView, generics.UpdateAPIView,
                  generics.DestroyAPIView):
    queryset = Post.objects.all().order_by('-id')
    serializer_class = PostSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'on_comment']:
            self.permission_classes = [perms.IsOwner]
        return super(PostViewSet, self).get_permissions()



    @action(methods=['POST'], url_path="create_post", detail=False)
    def create_post(self, request):
        try:
            user = request.user
            data = request.data
            content = data.get('content')
            post = Post.objects.create(
                user=user,
                content=content
            )
            media_files = []
            for media_file in request.FILES.getlist('media_file'):
                uploaded_file = cloudinary.uploader.upload_large(media_file)
                media = PostMedia.objects.create(
                    post=post,
                    media_file=uploaded_file['secure_url']
                )
                media_files.append(media)

            # Serialize the post and its associated media files
            post_serializer = PostSerializer(post, context={'request': request})
            media_serializer = PostMediaSerializer(media_files, many=True, context={'request': request})

            response_data = {
                'post': post_serializer.data,
                'media_files': media_serializer.data
            }

            return Response(data=response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({'Error': 'Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk):
        try:
            post = self.get_object()
            for key, value in request.data.items():
                setattr(post, key, value)
            post.save()
            return Response(data=PostSerializer(post, context={'request': request}).data,
                            status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post', 'get', 'delete'], detail=True, url_path='reaction')
    def react_to_post(self, request, pk):
        try:
            user = request.user
            post = self.get_object()
            if request.method == 'POST':
                reacted, react = ReactionPost.objects.update_or_create(
                    post=post,
                    user=user,
                    reaction_type=request.data.get('reaction_type')
                )
                if reacted:
                    reacted.reaction_type = request.data.get('reaction_type')
                    reacted.save()

                return Response(data=ReactionSerializer(reacted).data,
                                status=status.HTTP_201_CREATED)
            elif request.method == 'GET':
                react = ReactionPost.objects.filter(post=post)
                return Response(data=ReactionSerializer(react, many=True).data,
                                status=status.HTTP_200_OK)
            elif request.method == 'DELETE':
                react = ReactionPost.objects.filter(post=post, user=user)
                react.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=["post", "get"], detail=True, url_path='comment')
    def comment_post(self, request, pk):
        try:
            user = request.user
            post = self.get_object()
            print(user)
            if request.method.__eq__("GET"):
                comment = Comment.objects.filter(Q(post=post) & Q(parent_comment__isnull=True))
                return Response(data=CommentSerializer(comment, many=True, context={'request': request}).data,
                                status=status.HTTP_200_OK)
            elif request.method.__eq__("POST"):
                comment = Comment.objects.create(
                    user=user,
                    post=self.get_object(),
                    comment=request.data.get('comment')
                )
                return Response(data=CommentSerializer(comment, context={'request': request}).data,
                                status=status.HTTP_201_CREATED)
            else:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['put'], detail=True, url_path='on_comment')
    def on_comment(self, request, pk):
        try:
            post = self.get_object()
            if post.on_comment == True:
                post.on_comment = False
                post.save()
            else:
                post.on_comment = True
                post.save()
            return Response(data=PostSerializer(post, context={'request': request}).data,
                            status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentViewSet(viewsets.ViewSet, generics.UpdateAPIView, generics.DestroyAPIView):
    queryset = Comment.objects.filter(parent_comment__isnull=True)
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [perms.IsOwner]
        return super(CommentViewSet, self).get_permissions()

    def partial_update(self, request, pk):
        try:
            user = request.user
            comment = Comment.objects.get(pk=pk)
            if user == comment.user:
                comment.comment = request.data.get('comment')
                comment.save()
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)
            return Response(data=CommentSerializer(comment, context={'request': request}).data,
                            status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk):
        try:
            comment = self.get_object()
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post', 'get'], detail=True, url_path='reply')
    def reply(self, request, pk):
        try:
            user = request.user
            parent = Comment.objects.get(pk=pk)
            post = parent.post
            if request.method.__eq__('POST'):
                reply = Comment.objects.create(
                    user=user,
                    post=post,
                    comment=request.data.get('comment'),
                    parent_comment=parent
                )
                return Response(data=CommentSerializer(reply).data, status=status.HTTP_201_CREATED)
            elif request.method.__eq__('GET'):
                reply = Comment.objects.filter(parent_comment=parent)
                return Response(data=CommentSerializer(reply, many=True).data, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StoryViewSet(viewsets.ViewSet,generics.ListAPIView):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    @action(detail=False, methods=['POST'], url_path='create_story')
    def create_story(self, request):
        try:
            user = request.user
            if 'media_files' not in request.FILES or len(request.FILES.getlist('media_files')) == 0:
                return Response({"error": "At least one media file (image or video) is required."},
                                status=status.HTTP_400_BAD_REQUEST)

            story = Story.objects.create(user=user)
            uploaded_files = request.FILES.getlist('media_files')
            for uploaded_file in uploaded_files:
                media_type = 'image' if uploaded_file.content_type.startswith('image') else 'video'

                if media_type == 'video':
                    upload_result = cloudinary.uploader.upload_large(uploaded_file)
                    media_url = upload_result['secure_url']
                else:
                    upload_result = cloudinary.uploader.upload(uploaded_file)
                    media_url = upload_result['secure_url']

                story_media = StoryMedia.objects.create(
                    story=story,
                    media_type=media_type,
                    media_file=media_url
                )

            return Response({"message": "Story created successfully.", "video_url": media_url}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


