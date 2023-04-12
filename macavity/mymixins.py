from .models import *
from django.db.models import Prefetch, Count
#all parametrs for video I need to get for queries
#sometimes it is 'overkill', but this is for the reason of standartisation and to make code looking better 
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
#all video I need to get for queries
class VideoDataMixin:
    def get_video_queryset(self, **kwargs):
        video_queryset = Video.objects.select_related(
            'author_channel',
        ).annotate(
            sub_num=Count('author_channel__sub_system')
        ).only(*video_params)

        return video_queryset
    
#all comments with all params I need to get for queries  
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