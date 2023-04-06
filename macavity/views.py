import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, FormView
from django.views.generic.edit import FormMixin
from .models import *
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, login
from .forms import *
from django.db.models import Prefetch, Count
from django.contrib.auth.mixins import LoginRequiredMixin
import urllib.parse
from django.template.loader import render_to_string
from django.http import FileResponse
from django.db.models import Q
from .servises import raw_dislikes_into_likes, raw_likes_into_dislikes, subscribe, get_channels_subscribed_at, remove_subscription, remove_all_subscriptions, check_if_subscribed, get_number_of_subs

class Subscribes(ListView, LoginRequiredMixin):
    model = Video
    template_name = 'macavity/subscribes.html'
    context_object_name = 'videos'

    def get_queryset(self):
        self.new_context = get_channels_subscribed_at(self.request.user.pk)
        queryset = Video.objects.select_related('author_channel',
                                                ).annotate(sub_num=Count('author_channel__sub_system')
                                                           ).only('author_channel__slug', 'author_channel__avatar', 
                                                                    'author_channel__username', 'likes',
                                                                    'publish_date', 'video_title', 'slug', 'content',
                                                                    'description', 'preview',  'dislikes', 'views',
                                                                    'blocked_video', 'author_channel__id'
                                                                    ).filter(author_channel__pk__in = self.new_context, published=True
                                                                             )
        
        self.queryset =  queryset
        return super().get_queryset()
        
    def get_context_data(self,**kwargs):
        data = super().get_context_data(**kwargs)
        data['subscribed_at'] = Channel.objects.only('username', 'avatar', 'slug'
                                                     ).annotate(sub_num=Count('sub_system')
                                                                ).filter(pk__in = self.new_context)
        return data

class HomePage(ListView):
    model = Video
    template_name = 'macavity/home.html'
    context_object_name = 'videos'
    def get_queryset(self):
        queryset = Video.objects.select_related('author_channel',
                                        ).annotate(sub_num=Count('author_channel__sub_system')
                                                    ).only('author_channel__slug', 'author_channel__avatar', 
                                                            'author_channel__username', 'likes',
                                                            'publish_date', 'video_title', 'slug', 'content',
                                                            'description', 'preview',  'dislikes', 'views',
                                                            'blocked_video', 'author_channel__id'
                                                            ).all()
        self.queryset =  queryset
        return super().get_queryset()

class SearchView(ListView):
    template_name = 'macavity/search.html'
    model = Video
    context_object_name = 'videos'

    def get_queryset(self):
        queryset = Video.objects.select_related('author_channel'
                                                ).annotate(sub_num=Count('author_channel__sub_system')
                                                           ).only('publish_date', 'video_title', 'preview',  'slug', 'author_channel__username',
                                                                    'author_channel__avatar', 'author_channel__slug', 'likes', 'dislikes', 'views'
                                                                    ).filter(video_title__icontains = self.request.GET.get("search_input"),
                                                                             published=True
                                                                             )
        self.queryset =  queryset
        return super().get_queryset()


class VideoPlayer(ListView):
    model = Video
    template_name = 'macavity/player.html'
    context_object_name = 'video'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "GET" and request.headers.get('get-requets') == 'user-playlists':
            selected_playlists = Playlist.objects.filter(channel_playlist__pk=request.user.id, algo_playlist=False)
            playlists = render_to_string('macavity/ajaxplaylists.html', {'object_list':selected_playlists})
            return JsonResponse({"html": playlists})
        else:
            return super().get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "POST":
            data = json.loads(request.body.decode('UTF-8'))

            if data['request'] == 'add_video_to_playlist':
                tmp = Playlist.objects.get(pk=data['playlist_pk'])
                tmp.included_video.add(Video.objects.get(slug=self.kwargs['slug']))
                return HttpResponse('')

            elif data['request'] == 'add_playlist':
                new_playlist_name = urllib.parse.unquote(data['playlist_name'])
                Playlist.objects.create(playlist_name=new_playlist_name, channel_playlist=self.request.user)

                selected_playlists = Playlist.objects.filter(channel_playlist__pk=request.user.id, algo_playlist=False)
                playlists = render_to_string('macavity/ajaxplaylists.html', {'object_list':selected_playlists})
                return JsonResponse({"html": playlists})

            elif data['request'] == 'add_comment':
                video = Video.objects.get(pk=data['video_comment'])
                text = urllib.parse.unquote(data['comment_text'])
                Comment.objects.create(video_comment=video, channel_comment=self.request.user, comment_text=text)
                selected_comments = Comment.objects.select_related('channel_comment').annotate(sub_num=Count('channel_comment__sub_system')
                                                                                ).only('comment_likes', 
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
                                                                                    ).filter(video_comment=video)

                comments = render_to_string('macavity/ajaxcomments.html', {'object_list':selected_comments})
                return JsonResponse({"html": comments})

            elif data['request'] == 'like':
                algo_playlists = list(Playlist.objects.filter(Q(playlist_name='liked')|Q(playlist_name='disliked'),
                                                               channel_playlist__id=request.user.pk, algo_playlist=True,))
                if algo_playlists[1].playlist_name == 'liked':
                    liked_playlist, disliked_playlist = algo_playlists[1], algo_playlists[0]
                else:
                    liked_playlist, disliked_playlist = algo_playlists[0], algo_playlists[1]

                liked_video = Video.objects.filter(pk=data['video_like'], 
                                                     playlists=liked_playlist).first()
                
                if liked_video is None:
                    liked_video = Video.objects.get(pk=data['video_like'])
                    
                    new_dislikes = str(liked_video.dislikes)
                    x = 0
                    if liked_video in disliked_playlist.included_video.all():
                        x = 1
                        liked_video.dislikes-=1
                        new_dislikes = str(liked_video.dislikes)

                    if x == 1:
                        raw_dislikes_into_likes(disliked_playlist.pk, liked_video.pk, liked_playlist.pk)
                    else:
                        liked_playlist.included_video.add(liked_video)

                    liked_video.likes += 1
                    liked_video.save()
                    new_likes = str(liked_video.likes)
                    return JsonResponse({"likes": new_likes, "dislikes": new_dislikes})
                
                elif liked_video is not None:
                    liked_playlist.included_video.remove(liked_video)
                    liked_video.likes -=1
                    liked_video.save()
                    new_likes = str(liked_video.likes)
                    return JsonResponse({"likes": new_likes})

            elif data['request'] == 'dislike':
                algo_playlists = list(Playlist.objects.filter(Q(playlist_name='liked')|Q(playlist_name='disliked'),
                                                               channel_playlist__id=request.user.pk, algo_playlist=True,))
                
                if algo_playlists[1].playlist_name == 'liked':
                    liked_playlist, disliked_playlist = algo_playlists[1], algo_playlists[0]
                else:
                    liked_playlist, disliked_playlist = algo_playlists[0], algo_playlists[1]

                disliked_video = Video.objects.filter(pk=data['video_dislike'], 
                                                     playlists=disliked_playlist).first()
                if disliked_video is None:
                    disliked_video = Video.objects.get(pk=data['video_dislike'])

                    new_likes = str(disliked_video.likes)
                    x = 1
                    if disliked_video in liked_playlist.included_video.all():
                        x = 0
                        disliked_video.likes-=1
                        new_likes = str(disliked_video.likes)

                    if x == 0:
                         raw_likes_into_dislikes(disliked_playlist.pk, disliked_video.pk, liked_playlist.pk)
                    else:
                        disliked_playlist.included_video.add(disliked_video)

                    disliked_video.dislikes += 1
                    disliked_video.save()
                    new_dislikes = str(disliked_video.dislikes)
                    return JsonResponse({"dislikes": new_dislikes, "likes": new_likes})
                
                elif disliked_video is not None:
                    disliked_playlist.included_video.remove(disliked_video)
                    disliked_video.dislikes -=1
                    disliked_video.save()
                    new_dislikes = str(disliked_video.dislikes)
                    return JsonResponse({"dislikes": new_dislikes})

    def get_queryset(self):
        selected_categories = Category.objects.all()
        selected_comments= Comment.objects.select_related('channel_comment').annotate(sub_num=Count('channel_comment__sub_system')
                                                                                      ).only('comment_likes', 
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
        
        queryset = Video.objects.select_related('author_channel',
                                                ).annotate(sub_num=Count('author_channel__sub_system')
                                                           ).only('author_channel__slug', 'author_channel__avatar', 
                                                                    'author_channel__username', 'likes',
                                                                    'publish_date', 'video_title', 'slug', 'content',
                                                                    'description', 'preview',  'dislikes', 'views',
                                                                    'published', 'blocked_video'
                                                                    ).prefetch_related(Prefetch('cat', queryset=selected_categories),
                                                                                        Prefetch('video_comments', queryset=selected_comments),
                                                                    ).get(slug=self.kwargs['slug'])
        
        if self.request.user.is_authenticated:
            watched_playlist = Playlist.objects.get(channel_playlist__id=self.request.user.pk, playlist_name='watched', algo_playlist=True,)
            video_in_playlist = Video.objects.filter(slug=self.kwargs['slug'], 
                                                     playlists=watched_playlist).only('pk').first()
            if video_in_playlist is None and self.request.user.slug != queryset.author_channel.slug:
                queryset.views +=1
                queryset.save()
                watched_playlist.included_video.add(queryset)

        self.queryset =  queryset
        return super().get_queryset()
        
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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "GET" and request.headers.get('action') == 'subscribe':
            channels = list(Channel.objects.filter(Q(username=self.request.user.username)|Q(slug=kwargs['slug'])))
            
            if channels[1] == self.request.user.username:
                subscriber, subscribed_at = channels[1], channels[0]
            else:
                subscriber, subscribed_at = channels[0], channels[1]

            if check_if_subscribed(subscriber_id=subscriber.pk, subscribed_at_id=subscribed_at.pk):
                remove_subscription(subscriber_id=subscriber.pk, subscribed_at_id=subscribed_at.pk)
            else:
                subscribe(subscriber_id=subscriber.pk, subscribed_at_id=subscribed_at.pk)

            new_sub_num =get_number_of_subs(subscribed_at.pk)
            return JsonResponse({"sub_num": new_sub_num})
        else:
            return super().get(self, request, *args, **kwargs)

    def get_queryset(self):
        selected_videos = Video.objects.only('slug', 'preview', 'likes', 'dislikes', 'views', 'video_title', 'publish_date', 'author_channel_id', 'published')
        selected_playlists = Playlist.objects.only('playlist_name', 'slug', 'playlist_picture', 'channel_playlist_id', 'algo_playlist', 'hidden')
        queryset = Channel.objects.only('username', 'hat', 'avatar', 'description', 'pk'
                                        ).annotate(sub_num=Count('sub_system')
                                        ).prefetch_related(Prefetch('videos', queryset=selected_videos), 
                                                            Prefetch('playlists', queryset=selected_playlists),
                                                            ).get(slug=self.kwargs['slug']
                                                                  )

        self.queryset =  queryset
        return super().get_queryset()
    
    def get_context_data(self,**kwargs):
        data = super().get_context_data(**kwargs)
        data['subscribed_at'] = Channel.objects.only('username', 'avatar', 'slug'
                                                     ).annotate(sub_num=Count('sub_system')
                                                                ).filter(pk__in = get_channels_subscribed_at(self.queryset.pk))
        return data
    

class CategoriesView(ListView):
    model = Category
    template_name = 'macavity/categories.html'
    context_object_name = 'cats'

    def get_queryset(self):
        categories = Category.objects.all()
        selected_videos = Video.objects.select_related('author_channel').annotate(sub_num=Count('author_channel__sub_system')
                                                                                  ).only('publish_date', 'video_title',
                                                                                        'preview','author_channel__username',
                                                                                        'author_channel__slug',
                                                                                        'author_channel__avatar',
                                                                                        'slug', 'likes', 'dislikes',
                                                                                        ).filter(published = True)
        queryset = categories.prefetch_related(
            Prefetch('videos', queryset=selected_videos)
        )  
        self.queryset =  queryset
        return super().get_queryset()
    
class CategoryView(ListView):
    model = Category
    context_object_name = 'cat'
    template_name = 'macavity/category.html'

    def get_queryset(self):
        selected_videos = Video.objects.select_related('author_channel'
                                                       ).annotate(sub_num=Count('author_channel__sub_system')
                                                        ).only('publish_date', 'video_title',
                                                                'preview','author_channel__username',
                                                                'author_channel__slug',
                                                                'author_channel__avatar',
                                                                'slug', 'likes', 'dislikes'
                                                                )
        queryset = Category.objects.prefetch_related(
            Prefetch('videos', queryset=selected_videos)
        ).get(slug=self.kwargs['slug'])
        self.queryset =  queryset
        return super().get_queryset()

class PlaylistView(ListView):
    model = Playlist
    context_object_name = 'playlist'
    template_name = 'macavity/playlist.html'

    def get_queryset(self):
        selected_videos = Video.objects.select_related('author_channel'
                                                       ).annotate(sub_num=Count('author_channel__sub_system')
                                                        ).only('publish_date', 'video_title',
                                                        'preview','author_channel__username',
                                                        'author_channel__slug',
                                                        'author_channel__avatar',
                                                        'slug', 'likes', 'dislikes'
                                                        )
        queryset = Playlist.objects.select_related('channel_playlist').only('channel_playlist__username',
                                                                            'channel_playlist__slug',
                                                                            'channel_playlist__avatar',
                                                                            'playlist_name', 'slug',
                                                                            'algo_playlist'
                                                                            ).prefetch_related(Prefetch('included_video', queryset=selected_videos)
                                                                            ).get(slug=self.kwargs['slug'])
        self.queryset =  queryset
        return super().get_queryset()

class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'macavity/register.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('home')

class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'macavity/login.html'

    def get_success_url(self):
        return reverse_lazy('home')


def logout_user(request):
    logout(request)
    return redirect('login')

class AddVideo(LoginRequiredMixin, CreateView):
    form_class = AddVideoForm
    template_name = 'macavity/addvideo.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author_channel = self.request.user
        return super().form_valid(form)

class AddPlaylist(LoginRequiredMixin, CreateView):
    form_class = AddPlaylistForm
    template_name = 'macavity/addplaylist.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.channel_playlist = self.request.user
        return super().form_valid(form)

class ChangeChannel(LoginRequiredMixin, FormView):
    form_class = ChangeChannel
    template_name = 'macavity/changechannel.html'
    
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
    template_name = 'macavity/changeplaylist.html'
    
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
    template_name = 'macavity/changevideo.html'
    
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
