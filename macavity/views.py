from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, FormView
from .models import *
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, login
from .forms import *
from django.db.models import Prefetch, Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse
#raw sql query for sub system
from .servises import get_channels_subscribed_at
from .mymixins import *
#handlers for ajax requests here
from .ajaxhandlers import *
from django.db import transaction

class Subscribes(VideoDataMixin, LoginRequiredMixin, ListView):
    model = Video
    template_name = 'macavity/subscribes.html'
    context_object_name = 'videos'
    def get_queryset(self):
        #check servises.py to get the raw query
        self.channels_subscribed_at = get_channels_subscribed_at(self.request.user.pk)
        #check mixin
        queryset = self.get_video_queryset().filter(
            author_channel__pk__in = self.channels_subscribed_at, 
            published=True
        ).order_by('-publish_date')

        self.queryset =  queryset
        return super().get_queryset()
        
    def get_context_data(self,**kwargs):
        data = super().get_context_data(**kwargs)
        data['subscribed_at'] = Channel.objects.only(
            'username', 
            'avatar', 
            'slug'
        ).annotate(
            sub_num=Count('sub_system')
        ).filter(
            pk__in = self.channels_subscribed_at
        )

        return data

class HomePage(VideoDataMixin, ListView):
    model = Video
    template_name = 'macavity/home.html'
    context_object_name = 'videos'
    
    def get_queryset(self):
        #check mixin
        queryset = self.get_video_queryset().all()

        self.queryset =  queryset
        return super().get_queryset()

class SearchView(VideoDataMixin, ListView):
    template_name = 'macavity/search.html'
    model = Video
    context_object_name = 'videos'

    def get_queryset(self):
        queryset = self.get_video_queryset().filter(
            video_title__icontains = self.request.GET.get("search_input"),
            published=True
        )

        self.queryset =  queryset
        return super().get_queryset()


class VideoPlayer(VideoDataMixin, CommentDataMixin, ListView):
    model = Video
    template_name = 'macavity/player.html'
    context_object_name = 'video'

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
        selected_categories = Category.objects.all()
        selected_comments= self.get_comment_queryset()
        #check mixin
        queryset = self.get_video_queryset().prefetch_related(
            Prefetch('cat', queryset=selected_categories),
            Prefetch('video_comments', queryset=selected_comments),
        ).get(
            slug=self.kwargs['slug']
        )
        #add video to watched playlist and add view+1
        if self.request.user.is_authenticated:
            watched_playlist = Playlist.objects.get(
                channel_playlist__id=self.request.user.pk, 
                playlist_name='watched', 
                algo_playlist=True,
            )
                                                    
            video_in_playlist = Video.objects.filter(
                slug=self.kwargs['slug'], 
                playlists=watched_playlist
            ).only(
                'pk'
            ).first()
            
            if video_in_playlist is None and self.request.user.slug != queryset.author_channel.slug:
                
                with transaction.atomic():
                    watched_playlist.included_video.add(queryset)
                    queryset.views +=1
                    queryset.save()


        self.queryset =  queryset
        return super().get_queryset()

#view for src video in html, send video by parts
def video_by_chunks(request, slug):
    video = Video.objects.get(slug=slug)
    video_path = video.content.path
    response = FileResponse(open(video_path, 'rb'), content_type='video/mp4')
    response['Content-Disposition'] = f'attachment; filename="{video.video_title}"'
    response['Accept-Ranges'] = 'bytes'
    return response


class ChannelView(ListView):
    model = Channel
    template_name = 'macavity/channel.html'
    context_object_name = 'channel'

    def get(self, request, *args, **kwargs):
        #check ajaxhandlers
        if check_ajax_request_get_videoplayer(request):
            return add_subscriber_channel(username=self.request.user.username, slug=kwargs['slug'])
        else:
            return super().get(self, request, *args, **kwargs)

    def get_queryset(self):
        selected_videos = Video.objects.only(*video_params)

        selected_playlists = Playlist.objects.only(
            'playlist_name', 
            'slug', 
            'playlist_picture', 
            'channel_playlist_id', 
            'algo_playlist', 
            'hidden'
        )

        queryset = Channel.objects.only(
            'username', 
            'hat', 
            'avatar', 
            'description', 
            'pk'
        ).annotate(
            sub_num=Count('sub_system')
        ).prefetch_related(
            Prefetch('videos', queryset=selected_videos), 
            Prefetch('playlists', queryset=selected_playlists),
        ).get(slug=self.kwargs['slug']
        )

        self.queryset =  queryset
        return super().get_queryset()
    
    def get_context_data(self,**kwargs):
        data = super().get_context_data(**kwargs)
        data['subscribed_at'] = Channel.objects.only(
            'username', 
            'avatar', 
            'slug'
            ).annotate(
                sub_num=Count('sub_system')
            ).filter(
                pk__in = get_channels_subscribed_at(self.queryset.pk)
            )
        
        return data

class CategoriesView(VideoDataMixin, ListView):
    model = Category
    template_name = 'macavity/categories.html'
    context_object_name = 'cats'

    def get_queryset(self):
        categories = Category.objects.all()

        selected_videos = self.get_video_queryset().filter(published = True)

        queryset = categories.prefetch_related(
            Prefetch('videos', queryset=selected_videos)
        )  

        self.queryset =  queryset
        return super().get_queryset()
    
class CategoryView(VideoDataMixin,ListView):
    model = Category
    context_object_name = 'cat'
    template_name = 'macavity/category.html'

    def get_queryset(self):
        selected_videos = self.get_video_queryset()

        queryset = Category.objects.prefetch_related(
            Prefetch('videos', queryset=selected_videos)
        ).get(
            slug=self.kwargs['slug']
        )

        self.queryset =  queryset
        return super().get_queryset()

class PlaylistView(VideoDataMixin, ListView):
    model = Playlist
    context_object_name = 'playlist'
    template_name = 'macavity/playlist.html'

    def get_queryset(self):
        selected_videos = self.get_video_queryset()
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

class AddVideo(LoginRequiredMixin, CreateView):
    form_class = AddVideoForm
    template_name = 'macavity/forms/addvideo.html'

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

class AddPlaylist(LoginRequiredMixin, CreateView):
    form_class = AddPlaylistForm
    template_name = 'macavity/forms/addplaylist.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.channel_playlist = self.request.user
        return super().form_valid(form)

class ChangeChannel(LoginRequiredMixin, FormView):
    form_class = ChangeChannel
    template_name = 'macavity/forms/changechannel.html'
    
    def get_form(self, form_class=ChangeChannel):
        channel = Channel.objects.get(username=self.request.user.username)
        return form_class(instance=channel, **self.get_form_kwargs())

    def form_valid(self, form):
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
        self.object = form.save(commit=True)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('playlist', kwargs={'slug': self.kwargs['slug']})

class ChangeVideo(LoginRequiredMixin, FormView):
    form_class = Video
    template_name = 'macavity/forms/changevideo.html'
    
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
        self.object = form.save(commit=True)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('video', kwargs={'slug': self.kwargs['slug']})
