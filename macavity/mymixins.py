from .models import *
from django.db.models import Prefetch, Count

video_params = [
    'author_channel__slug',
    'author_channel__avatar', 
    'author_channel__username', 
    'likes',
    'publish_date', 
    'video_title', 
    'slug', 
    'content', 
    'description', 
    'preview',  
    'dislikes', 
    'views', 
    'blocked_video', 
    'author_channel__id',
    'published'
]
class VideoDataMixin:
    def get_video_queryset(self, **kwargs):
        video_queryset = Video.objects.select_related(
            'author_channel',
        ).annotate(
            sub_num=Count('author_channel__sub_system')
        ).only(*video_params)

        return video_queryset
    
class CommentDataMixin:
    def get_comment_queryset(self, **kwargs):
        comments_queryset = Comment.objects.select_related(
            'channel_comment'
        ).annotate(
            sub_num=Count('channel_comment__sub_system')
        ).only(
            'comment_likes', 
            'comment_dislikes',
            'upload_date_comment',
            'change_date_comment',
            'comment_text',
            'blocked_comment',
            'parent_comment__id',
            'channel_comment__username',
            'channel_comment__avatar',
            'channel_comment__slug',
            'video_comment__id'
        )
        return comments_queryset