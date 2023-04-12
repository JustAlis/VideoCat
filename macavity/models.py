from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from .utils import unique_slugify
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.db.models.signals import pre_save, post_delete, post_save

#generate unique path fo channel avatar
def path_to_avatars(instance, filename):
    return 'avatars/{}/{}'.format(instance.username, filename)
#generate unique path fo channel hat
def path_to_hats(instance, filename):
    return 'hats/{}/{}'.format(instance.username, filename)

#There is nothing to talk about here, just models and fields, but there is something to discribe aout signals
#Check bottom with signals
#names of fields speaks for themselves
sex_choises = (
('M', 'Male'),
('F', 'Female'),
('O', 'Other'),
('N', 'Not staded')
)

class Channel(AbstractUser):

    sex = models.CharField(max_length=1, choices=sex_choises, verbose_name = 'sex', blank=True, null=True)

    sub_system = models.ManyToManyField('self', symmetrical=False, related_name='subscribed_at')

    date_of_birth = models.DateField(verbose_name = 'date_of_birth', blank=True, null=True)

    avatar = models.ImageField(upload_to=path_to_avatars, blank=True, verbose_name = 'avatar', null=True,
                                validators=[FileExtensionValidator(allowed_extensions=['jpg'])])

    hat = models.ImageField(upload_to=path_to_hats, blank=True, verbose_name = 'hat', null=True,
                             validators=[FileExtensionValidator(allowed_extensions=['jpg'])])

    slug = models.SlugField(null=True, blank=True, unique=True, verbose_name='channel_url')
    
    description = models.TextField(max_length=255, default='Channel description:\n', verbose_name = 'description')

    def __str__(self):
        return self.username
    
    def get_absolute_url(self):
        return reverse('channel', kwargs={'channel_slug': self.slug})


class Video(models.Model):

    author_channel = models.ForeignKey('Channel', on_delete=models.CASCADE, verbose_name = 'author_channel', 
                                       related_name='videos', blank=True, null=True)
    cat = models.ManyToManyField('Category', verbose_name="categories", related_name='videos')

    video_title = models.CharField(max_length=100, verbose_name = 'title', db_index=True)
    description = models.TextField(max_length=255, default='Description:\n', verbose_name = 'description')
    upload_date = models.DateTimeField(auto_now_add=True,verbose_name = 'upload_date')
    publish_date = models.DateTimeField(verbose_name = 'publish_date', blank=True, null=True)
    published = models.BooleanField(default=True, verbose_name = 'published', blank=True,)

    blocked_video = models.BooleanField(default=False, verbose_name = 'blocked_video', blank=True,)
    slug = models.SlugField(null=True, blank=True, unique=True, verbose_name='video_url')

    content = models.FileField(upload_to='videos/%Y/%m/%d', verbose_name = 'content', 
                               validators=[FileExtensionValidator(allowed_extensions=['mp4'])])
    
    preview = models.ImageField(upload_to='previews/%Y/%m/%d', blank=True, null=True, verbose_name = 'preview', 
                                validators=[FileExtensionValidator(allowed_extensions=['jpg'])])
    
    likes = models.IntegerField(default=0, verbose_name="likes",)
    dislikes = models.IntegerField(default=0, verbose_name="dislikes",)
    views = models.IntegerField(default=0, verbose_name="views",)

    def __str__(self):
        return self.video_title

    def get_absolute_url(self):
        return reverse('video', kwargs={'slug': self.slug})
    
    class Meta:
        ordering = ['views']

class Playlist(models.Model):
    channel_playlist = models.ForeignKey('Channel', on_delete=models.CASCADE, verbose_name = 'channel_playlist', related_name='playlists')
    included_video = models.ManyToManyField('Video', verbose_name = 'included_video', related_name='playlists')

    playlist_name = models.CharField(max_length=100, verbose_name="playlist_name", db_index=True)
    slug = models.SlugField(null=True, blank=True, unique=True, verbose_name="playlist_url")

    playlist_picture = models.ImageField(upload_to='playlists/%Y/%m/%d', blank=True, null=True, verbose_name = 'playlist_picture', 
                                         validators=[FileExtensionValidator(allowed_extensions=['jpg'])])
    hidden = models.BooleanField(default=False, verbose_name = 'published')
    #mark for special playlist (watched, liked, disliked)
    algo_playlist = models.BooleanField(default=False, verbose_name = 'algo_playlist')

    creation_date = models.DateTimeField(auto_now_add=True,verbose_name = 'creation_date')
    change_date = models.DateTimeField(auto_now=True,verbose_name = 'creation_date')

    def __str__(self):
        return self.playlist_name
    
    def get_absolute_url(self):
        return reverse('playlist', kwargs={'playlist_slug': self.slug})
    
    class Meta:
        ordering = ['playlist_name'] 

class Category(models.Model):

    category_name = models.CharField(max_length=100, db_index=True, verbose_name="category", unique=True)
    slug = models.SlugField(null=True, blank=True, unique=True, verbose_name="cat_url")

    def __str__(self):
        return self.category_name

    def get_absolute_url(self):
        return reverse('category', kwargs={'category_slug': self.slug})
    
    class Meta:
        ordering = ['category_name']


class Comment(models.Model):

    video_comment = models.ForeignKey('Video', on_delete=models.CASCADE, verbose_name = 'video_comment', related_name='video_comments')
    channel_comment = models.ForeignKey('Channel', on_delete=models.CASCADE, verbose_name = 'channel_comment', related_name='chanel_comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name = 'comment_answer',related_name='comments')

    upload_date_comment = models.DateTimeField(auto_now_add=True, verbose_name = 'upload_date_comment')
    change_date_comment = models.DateTimeField(auto_now=True, blank = True, verbose_name = 'change_date_comment')
    comment_text = models.TextField(max_length=255, verbose_name = 'comment_text')
    comment_likes = models.IntegerField(default=0)
    comment_dislikes = models.IntegerField(default=0)
    blocked_comment = models.BooleanField(default=False, verbose_name = 'blocked_comment')

    def __str__(self):
        return self.comment_text
    
    class Meta:
        ordering = ['comment_likes']

#here are 4 receivers for generating unique slug, when an object is created
#check utils.py to see the code of unique_slugify
@receiver(pre_save, sender=Video)
def slugfy_video(sender, instance, **kwargs):
    if instance.slug is None:
        slug_str ="%s" % instance.video_title
        unique_slugify(instance, slug_str)

@receiver(pre_save, sender=Channel)
def first_save_channel(sender, instance, **kwargs):
    if instance.slug is None:
        slug_str ="%s" % instance.username
        unique_slugify(instance, slug_str)

@receiver(pre_save, sender=Playlist)
def slugify_playlist(sender, instance, **kwargs):
    if instance.slug is None:
        slug_str ="%s" % instance.playlist_name
        unique_slugify(instance, slug_str)

@receiver(pre_save, sender=Category)
def slugify_cat(sender, instance, **kwargs):
    if instance.slug is None:
        slug_str ="%s" % instance.category_name
        unique_slugify(instance, slug_str)
#special receiver, wich triggers after channel obj is created
#I need this to create 3 special playlists
@receiver(post_save, sender=Channel)
def first_save_channel_add_playlists(sender, instance, **kwargs):
        Playlist.objects.get_or_create(channel_playlist__id=instance.pk, playlist_name='liked', algo_playlist=True, channel_playlist = instance)
        Playlist.objects.get_or_create(channel_playlist__id=instance.pk, playlist_name='disliked', algo_playlist=True, channel_playlist = instance)
        Playlist.objects.get_or_create(channel_playlist__id=instance.pk, playlist_name='watched', algo_playlist=True, channel_playlist = instance)

#add proper publish date on video, only once when video gets publiched for the firt time
@receiver(pre_save, sender=Video)
def set_publish_date(sender, instance, **kwargs):
    if instance.published and instance.publish_date is None:
        instance.publish_date = timezone.now()

#there are 3 receivers, to clear the files from the server, when objects get deleted
@receiver(post_delete, sender=Channel)
def slugify_cat(sender, instance, **kwargs):
    if instance.hat:
        instance.hat.delete(save=False)

    if instance.avatar:
        instance.avatar.delete(save=False)

@receiver(post_delete, sender=Video)
def delete_files_video(sender, instance, *args, **kwargs):
    if instance.content:
        instance.content.delete(save=False)

    if instance.preview:
        instance.preview.delete(save=False)
    
@receiver(post_delete, sender=Playlist)
def delete_files_video(sender, instance, *args, **kwargs):
    if instance.playlist_picture:
        instance.playlist_picture.delete(save=False)
