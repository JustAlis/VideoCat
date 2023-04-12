from django.contrib import admin
from .models import *
from django.utils.safestring import mark_safe
#just models registration.
#it is not good, but i do not need admin panel, becouse of how the cite works,
#so I didn't change it since the very begining of this project
#I do not recoment to use admin panel at all becouse of not optimised sql queries
#it is better to implent some moderation buttons in templates for superusers
class VideoAdmin(admin.ModelAdmin):
    list_display = ('views','likes','dislikes','video_title','description','get_preview', 'get_video','published', 'blocked_video')
    list_display_links = ('video_title', 'get_preview')
    list_editable = ('blocked_video',)
    search_fields = ('video_title',)

    def get_preview(self, object):
        if object.preview:
            return mark_safe(f"<img src='{object.preview.url}' width=50>")
        
    def get_video(self, object):
        if object.content:
            return mark_safe(f'<video width="320" height="240" controls><source src="{object.content.url}" type="video/mp4"></video>')
 
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('username', 'date_of_birth', 'email', 'get_avatar', 'first_name', 'last_name')
    list_display_links = ('username', )
    search_fields = ('username',)

    def get_avatar(self, object):
        if object.avatar:
            return mark_safe(f"<img src='{object.avatar.url}' width=50>")
        
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('playlist_name', 'get_playlist_picture', 'hidden')
    list_display_links = ('playlist_name',)
    list_editable = ('hidden',)
    def get_playlist_picture(self, object):
        if object.preview:
            return mark_safe(f"<img src='{object.playlist_picture.url}' width=50>")

class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment_text', 'blocked_comment')
    list_editable = ('blocked_comment',)
    search_fields = ('comment_text',) 

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name',)
    list_display_links = ('category_name',)
    search_fields = ('category_name', )

admin.site.register(Channel, ChannelAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Playlist, PlaylistAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Comment, CommentAdmin)
