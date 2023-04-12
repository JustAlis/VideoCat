import os
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, FormView, DeleteView
from django.contrib.auth.decorators import login_required
from .models import *
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, login
from .forms import *
from django.db.models import Prefetch, Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse
from django.db import transaction
#mixins I wrote to reduse amount of code
from .mymixins import *
#handlers for ajax requests here
from .ajaxhandlers import *

#view for user to check videos from channels, he is subscribed at
class Subscribes(VideoDataMixin, LoginRequiredMixin, ListView):
    model = Video
    template_name = 'macavity/subscribes.html'
    context_object_name = 'videos'
    def get_queryset(self):

        #check mixin
        queryset = self.get_video_queryset().filter(
            #filter only published videos of channels, user is subscribed at
            author_channel__in = self.request.user.subscribed_at.all(), 
            published=True
        ).order_by('-publish_date')

        self.queryset =  queryset
        return super().get_queryset()
        
    def get_context_data(self,**kwargs):
        data = super().get_context_data(**kwargs)
        #Get the data of channels, user is subscribed at
        data['subscribed_at'] = Channel.objects.only(
            'username',
            'avatar', 
            'slug'
        ).annotate(
            sub_num=Count('sub_system')
        ).filter(
            id__in=self.request.user.subscribed_at.all()
        ) 

        return data
#just generic home page
class HomePage(VideoDataMixin, ListView):
    model = Video
    template_name = 'macavity/home.html'
    context_object_name = 'videos'
    
    def get_queryset(self):
        #check mixin
        queryset = self.get_video_queryset().all()

        self.queryset =  queryset
        return super().get_queryset()
    
#view to display videos of certain channel
class VideosView(VideoDataMixin, ListView):
    model = Video
    template_name = 'macavity/channel_videos.html'
    context_object_name = 'videos'
    
    def get_queryset(self):
        #check mixin
        queryset = self.get_video_queryset().filter(author_channel__slug=self.kwargs['slug'])
        
        self.queryset =  queryset
        return super().get_queryset()
    
    def get_context_data(self, **kwargs):
        #get the data of this channel. I do understand, that I already have this data, but get it from
        #current queryst is just confusing me, so I decided to get it once more for code to be a bit readable
        data = super().get_context_data(**kwargs)
        data['channel'] = Channel.objects.only(
            'username', 
            'avatar', 
            'slug'
        ).annotate(
            sub_num=Count('sub_system')
        ).get(
            slug=self.kwargs['slug']
        )

        return data

#generic search view
class SearchView(VideoDataMixin, ListView):
    template_name = 'macavity/search.html'
    model = Video
    context_object_name = 'videos'

    def get_queryset(self):
        queryset = self.get_video_queryset().filter(
            #filter for the search input
            video_title__icontains = self.request.GET.get("search_input"),
            published=True
        )

        self.queryset =  queryset
        return super().get_queryset()

#here are two mixins, for videos and for comment
class VideoPlayer(VideoDataMixin, CommentDataMixin, ListView):
    model = Video
    template_name = 'macavity/player.html'
    context_object_name = 'video'

    #I have to overwrite ListViews get and post methods, to be able to handle ajax requests
    #Check static/js/script.js to see requests, send by ajax
    #Check ajaxhandlers to see the logic behind this functions
    def get(self, request, *args, **kwargs):
        if check_ajax_request_get(request=request):
            return handle_get_request_videoplayer(request=request, slug = self.kwargs['slug'])
        
        else:
            return super().get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        #check ajaxhandlers
        if check_ajax_request_post(request=request):
            return handle_post_request_videoplayer(
                request=request,
                user=self.request.user, 
                comments_queryset=self.get_comment_queryset(), 
                slug=self.kwargs['slug'],
            )

    def get_queryset(self):
        #get categories, wich are related to this video
        selected_categories = Category.objects.all()
        #get comment
        selected_comments= self.get_comment_queryset()
        #check mixin
        queryset = self.get_video_queryset().prefetch_related(
            #filter comments and cats via prefetch_related
            Prefetch('cat', queryset=selected_categories),
            Prefetch('video_comments', queryset=selected_comments),
        ).get(
            slug=self.kwargs['slug']
        )
        #add video to watched playlist of user and add view+1 to videos int field 'views'
        if self.request.user.is_authenticated:
            watched_playlist = Playlist.objects.get(
                channel_playlist__id=self.request.user.pk, 
                playlist_name='watched', 
                algo_playlist=True,
            )
            #check if video is already watched                            
            video_in_playlist = Video.objects.filter(
                slug=self.kwargs['slug'], 
                playlists=watched_playlist
            ).only(
                'pk'
            ).first()
            #if it is watched for the first time by this user
            if video_in_playlist is None and self.request.user.slug != queryset.author_channel.slug:
                
                with transaction.atomic():
                    watched_playlist.included_video.add(queryset)
                    queryset.views +=1
                    queryset.save()
            #else just do nithing

        self.queryset =  queryset
        return super().get_queryset()

#view for src video in html, send video by parts
#just a wrapper for dynamic sending video by bytes
#check player.html, tag video, tag src inside video tag
def video_by_chunks(request, slug):
    video = Video.objects.get(slug=slug)
    video_path = video.content.path
    response = FileResponse(open(video_path, 'rb'), content_type='video/mp4')
    response['Content-Disposition'] = f'attachment; filename="{video.video_title}"'
    response['Accept-Ranges'] = 'bytes'
    return response


#view to display data of the channel
class ChannelView(ListView):
    model = Channel
    template_name = 'macavity/channel.html'
    context_object_name = 'channel'
    #I have to overwrite ListViews get method, to be able to handle ajax requests
    #Check static/js/script.js to see requests, send by ajax
    #Check ajaxhandlers to see the logic behind this functions
    def get(self, request, *args, **kwargs):
        #check ajaxhandlers
        if check_ajax_request_get_videoplayer(request):
            return add_subscriber_channel(user=request.user, slug=kwargs['slug'])
        else:
            return super().get(self, request, *args, **kwargs)

    def get_queryset(self):
        #collect videos made by this channel
        selected_videos = Video.objects.only(*video_params)
        #collect playlists
        selected_playlists = Playlist.objects.only(
            'playlist_name', 
            'slug', 
            'playlist_picture', 
            'channel_playlist_id', 
            'algo_playlist', 
            'hidden'
        )
        #get the channel itself
        queryset = Channel.objects.only(
            'username', 
            'hat', 
            'avatar', 
            'description', 
            'pk',
            'slug'
        ).annotate(
            sub_num=Count('sub_system')
        ).prefetch_related(
            #filter playlists and videos
            Prefetch('videos', queryset=selected_videos), 
            Prefetch('playlists', queryset=selected_playlists),
        ).get(slug=self.kwargs['slug']
        )

        self.queryset =  queryset
        return super().get_queryset()
    #add list of channels, selected channel is subscribed at
    def get_context_data(self,**kwargs):
        data = super().get_context_data(**kwargs)
        data['subscribed_at'] = Channel.objects.only(
            'username', 
            'avatar', 
            'slug'
            ).annotate(
                sub_num=Count('sub_system')
            ).filter(
                id__in=self.queryset.subscribed_at.all()
            )
        
        return data
    
#view for the categories
class CategoriesView(VideoDataMixin, ListView):
    model = Category
    template_name = 'macavity/categories.html'
    context_object_name = 'cats'

    def get_queryset(self):
        #get cats
        categories = Category.objects.all()
        #get videos
        selected_videos = self.get_video_queryset().filter(published = True)

        queryset = categories.prefetch_related(
            #filter videos
            Prefetch('videos', queryset=selected_videos)
        )  

        self.queryset =  queryset
        return super().get_queryset()
#view to display all of the playlists of some channel  
class PlaylistsView(VideoDataMixin, ListView):
    model = Playlist
    template_name = 'macavity/playlists.html'
    context_object_name = 'playlists'

    def get_queryset(self):
        #get playlists
        playlists = Playlist.objects.all().filter(channel_playlist__slug=self.kwargs['slug'])
        #get videos
        selected_videos = self.get_video_queryset().filter(published = True)

        queryset = playlists.prefetch_related(
            #filter videos
            Prefetch('included_video', queryset=selected_videos)
        )  

        self.queryset =  queryset
        return super().get_queryset()
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        #get channel info
        data['channel'] = Channel.objects.only(
            'username', 
            'avatar', 
            'slug'
        ).annotate(
            sub_num=Count('sub_system')
        ).get(slug=self.kwargs['slug'])

        return data
    
#view to display all videos if selected category   
class CategoryView(VideoDataMixin,ListView):
    model = Category
    context_object_name = 'cat'
    template_name = 'macavity/category.html'

    def get_queryset(self):
        #get videos
        selected_videos = self.get_video_queryset()
        #get cat
        queryset = Category.objects.prefetch_related(
            #filter videos
            Prefetch('videos', queryset=selected_videos)
        ).get(
            slug=self.kwargs['slug']
        )

        self.queryset =  queryset
        return super().get_queryset()

#view to display all of the videos in some playlist
class PlaylistView(VideoDataMixin, ListView):
    model = Playlist
    context_object_name = 'playlist'
    template_name = 'macavity/playlist.html'

    def get_queryset(self):
        #get videos
        selected_videos = self.get_video_queryset()
        #get playlist data
        queryset = Playlist.objects.select_related(
            'channel_playlist'
        ).only(
            'channel_playlist__username',
            'channel_playlist__slug',
            'channel_playlist__avatar',
            'playlist_name', 
            'slug',
            'algo_playlist',
            'hidden'
        ).prefetch_related(
            #filter videos
            Prefetch('included_video', queryset=selected_videos)
        ).get(
            slug=self.kwargs['slug']
        )

        self.queryset =  queryset
        return super().get_queryset()

class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'macavity/forms/register.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('home')

class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'macavity/forms/login.html'

    def get_success_url(self):
        return reverse_lazy('home')


def logout_user(request):
    logout(request)
    return redirect('login')

#form class for adding videos
class AddVideo(LoginRequiredMixin, CreateView):
    form_class = AddVideoForm
    template_name = 'macavity/forms/addvideo.html'

    #this handler i need to add category, while adding video
    #check ajaxhandlers
    def post(self, request, *args, **kwargs):

        if check_ajax_request_post(request=request):
            return handle_post_request_add_category(request=request)
        
        else:

            return super().post(self, request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author_channel = self.request.user
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('video', kwargs={'slug': self.object.slug})

#form class to create a playlist
class AddPlaylist(LoginRequiredMixin, CreateView):

    form_class = AddPlaylistForm
    template_name = 'macavity/forms/addplaylist.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.channel_playlist = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('playlist', kwargs={'slug': self.object.slug})

#form to change channel data
class ChangeChannel(LoginRequiredMixin, FormView):
    form_class = ChangeChannel
    template_name = 'macavity/forms/changechannel.html'
    
    def get_form(self, form_class=ChangeChannel):
        channel = Channel.objects.get(username=self.request.user.username)
        return form_class(instance=channel, **self.get_form_kwargs())

    def form_valid(self, form):
        #basicly I need this code just no free not used files on the server
        #I don't want to do it in models via signals, becouse that signals woulde
        #be calld every time model is updated. It is not bad with channels, but imagine amount
        #of call on video model, its fields with views, likes, dislikes updates really frequently
        #so it is better to write a bit strange code here, than invoke this logic every time 
        #user likes or watch video

        #I will explain this logic only once, couse it is similar in all of the cases

        #get current model, wicj is going to be changed
        channel = self.request.user

        cleaned_avatar = False
        try:
            #check if user cleared image field from the channel model
            if self.request.POST['avatar-clear'] == 'on':
                cleaned_avatar = True
        except:
            pass
        #get current file name 
        avatar = os.path.basename(channel.avatar.name)
        #get name of new file
        new_avatar = self.request.FILES.get('avatar')
        #clear old file if new file is uploaded or the field is cleared
        if (avatar and avatar != new_avatar and new_avatar is not None) or (cleaned_avatar):
            channel.avatar.delete(save=False)


        #check ChangeChannel form valid for avatar field
        cleaned_hat = False
        try:
            if self.request.POST['hat-clear'] == 'on':
                cleaned_hat = True
        except:
            pass
        hat = os.path.basename(channel.hat.name)
        new_hat = self.request.FILES.get('hat')
        if (hat and hat != new_hat and new_hat is not None) or (cleaned_hat):
            channel.hat.delete(save=False)

        self.object = form.save(commit=True)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('channel', kwargs={'slug': self.request.user.slug})

class ChangePlaylist(LoginRequiredMixin, FormView):
    form_class = Playlist
    template_name = 'macavity/forms/changeplaylist.html'
    
    def get_form(self, form_class=ChangePlaylist):
        playlist = Playlist.objects.get(slug=self.kwargs['slug'])
        if playlist.channel_playlist.username == self.request.user.username:
            return form_class(instance=playlist, **self.get_form_kwargs())
        else: 
            return None

    def form_valid(self, form):
        #check ChangeChannel form valid for avatar field
        playlist = Playlist.objects.get(slug=self.kwargs['slug'])

        playlist_picture =os.path.basename(playlist.playlist_picture.name)
        new_playlist_picture = self.request.FILES.get('playlist_picture')

        cleaned_playlist_picture = False
        try:
            if self.request.POST['playlist_picture-clear'] == 'on':
                cleaned_playlist_picture = True
        except:
            pass

        if (playlist_picture and playlist_picture != new_playlist_picture and new_playlist_picture is not None) or (cleaned_playlist_picture):
            playlist.playlist_picture.delete(save=False)

        self.object = form.save(commit=True)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('playlist', kwargs={'slug': self.kwargs['slug']})

class ChangeVideo(LoginRequiredMixin, FormView):
    form_class = Video
    template_name = 'macavity/forms/changevideo.html'
    
    #hanlder for adding category while adding video
    def post(self, request, *args, **kwargs):
        if check_ajax_request_post(request=request):
            return handle_post_request_add_category(request=request)
        else:
            return super().post(self, request, *args, **kwargs)

    def get_form(self, form_class=ChangeVideo):
        video = Video.objects.get(slug=self.kwargs['slug'])
        if video.author_channel.username == self.request.user.username:
            return form_class(instance=video, **self.get_form_kwargs())
        else: 
            return None

    def form_valid(self, form):
        #check ChangeChannel form valid for avatar field
        video = Video.objects.get(slug=self.kwargs['slug'])
        
        cleaned_preview = False
        try:
            if self.request.POST['preview-clear'] == 'on':
                cleaned_preview = True
        except:
            pass
        preview = os.path.basename(video.preview.name)
        new_preview = self.request.FILES.get('preview')
        if (preview and preview != new_preview and new_preview is not None) or (cleaned_preview):
            video.preview.delete(save=False)

        self.object = form.save(commit=True)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('video', kwargs={'slug': self.kwargs['slug']})


#delete channel
class ChannelDelete(LoginRequiredMixin,DeleteView):
    template_name = 'macavity/forms/deletechannel.html'
    success_url = reverse_lazy('register')
    def get_queryset(self):
        queryset = Channel.objects.filter(pk = self.request.user.pk)
        self.queryset = queryset
        return super().get_queryset()
    
#delete playlist
class PlaylistDelete(LoginRequiredMixin,DeleteView):
    template_name = 'macavity/forms/deleteplaylist.html'
    
    def get_queryset(self):
        queryset = Playlist.objects.filter(slug=self.kwargs['slug'])
        self.queryset =  queryset
        return super().get_queryset()

    def get_success_url(self):
        return reverse_lazy('channel', kwargs={'slug': self.request.user.slug})

#delete video
class VideoDelete(LoginRequiredMixin,DeleteView):
    template_name = 'macavity/forms/deletevideo.html'

    def get_queryset(self):
        queryset = Video.objects.filter(slug=self.kwargs['slug'])
        self.queryset =  queryset
        return super().get_queryset()
    
    def get_success_url(self):
        return reverse_lazy('channel', kwargs={'slug': self.request.user.slug})

#redirect to watched playlist in side bar
@login_required
def redirect_to_watched_playlist(request):
    watched_playlist_slug = Playlist.objects.get(channel_playlist = request.user, algo_playlist =True, playlist_name='watched').slug
    return redirect('playlist', watched_playlist_slug)


#redirect to liked playlist in side bar
@login_required
def redirect_to_liked_playlist(request):
    liked_playlist_slug = Playlist.objects.get(channel_playlist = request.user, algo_playlist =True, playlist_name='liked').slug
    return redirect('playlist',  liked_playlist_slug)