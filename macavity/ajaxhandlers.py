from .models import *
import json
from django.http import HttpResponse, JsonResponse
from .forms import *
import urllib.parse
from django.template.loader import render_to_string
from django.db.models import Q
from .mymixins import *
from django.db import transaction

def check_ajax_request_get(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "GET":
        return True
    else:
        return False
        
def handle_get_request_videoplayer(request, slug):
    if request.headers.get('get-requets') == 'user-playlists':
        selected_playlists = Playlist.objects.filter(channel_playlist__pk=request.user.id, algo_playlist=False)
        playlists = render_to_string('macavity/ajax/ajaxplaylists.html', {'object_list':selected_playlists})
        return JsonResponse({"html": playlists})
    
    elif request.headers.get('get-requets') == 'subscribe':
        
        subscribed_at = Video.objects.get(slug = slug).author_channel
        subscriber = request.user

        if subscriber in subscribed_at.sub_system.all(): 
            subscribed_at.sub_system.remove(subscriber)
        else:
            subscribed_at.sub_system.add(subscriber)
        new_sub_num = subscribed_at.sub_system.count()
        return JsonResponse({"sub_num": 'Подписчики: %s' % new_sub_num})
        

def check_ajax_request_post(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "POST":
        return True
    else:
        return False
        
def handle_post_request_videoplayer(request, user, comments_queryset, slug):
        data = json.loads(request.body.decode('UTF-8'))

        if data['request'] == 'add_comment':
            video = Video.objects.get(pk=data['video_comment'])
            text = urllib.parse.unquote(data['comment_text'])
            Comment.objects.create(video_comment=video, channel_comment=user, comment_text=text)

            selected_comments = comments_queryset.filter(video_comment=video)

            comments = render_to_string('macavity/ajax/ajaxcomments.html', {'object_list':selected_comments})
            return JsonResponse({"html": comments})

        elif data['request'] == 'like':
            algo_playlists = list(Playlist.objects.filter(
                Q(playlist_name='liked')|Q(playlist_name='disliked'),
                channel_playlist__id=user.pk, 
                algo_playlist=True,
            ))

            if algo_playlists[1].playlist_name == 'liked':
                liked_playlist, disliked_playlist = algo_playlists[1], algo_playlists[0]
            else:
                liked_playlist, disliked_playlist = algo_playlists[0], algo_playlists[1]

            with transaction.atomic():              
                liked_video = Video.objects.filter(
                    pk=data['video_like'], 
                    playlists=liked_playlist
                ).first()

                if liked_video is None:
                    liked_video = Video.objects.get(pk=data['video_like'])

                    if liked_video in disliked_playlist.included_video.all():

                        disliked_playlist.included_video.remove(liked_video)
                        liked_playlist.included_video.add(liked_video)
                        liked_video.dislikes-=1
                        liked_video.likes += 1
                        liked_video.save()

                        new_dislikes = liked_video.dislikes
                        new_likes = liked_video.likes
                        return JsonResponse({"likes": new_likes, "dislikes": new_dislikes})

                    else:
                        liked_playlist.included_video.add(liked_video)
                        liked_video.likes += 1
                        liked_video.save()

                        new_likes = liked_video.likes
                        return JsonResponse({"likes": new_likes})
                
                elif liked_video is not None:
                    liked_playlist.included_video.remove(liked_video)
                    liked_video.likes -=1
                    liked_video.save()
                    
                    new_likes = liked_video.likes
                    return JsonResponse({"likes": new_likes})

        elif data['request'] == 'dislike':
            algo_playlists = list(Playlist.objects.filter(
                Q(playlist_name='liked')|Q(playlist_name='disliked'),
                channel_playlist__id=user.pk, algo_playlist=True,)
            )
            
            if algo_playlists[1].playlist_name == 'liked':
                liked_playlist, disliked_playlist = algo_playlists[1], algo_playlists[0]
            else:
                liked_playlist, disliked_playlist = algo_playlists[0], algo_playlists[1]

            with transaction.atomic():
                disliked_video = Video.objects.filter(
                    pk=data['video_dislike'], 
                    playlists=disliked_playlist
                ).first()

                if disliked_video is None:
                    disliked_video = Video.objects.get(pk=data['video_dislike'])

                    if disliked_video in liked_playlist.included_video.all():
                        disliked_playlist.included_video.add(disliked_video)
                        liked_playlist.included_video.remove(disliked_video)
                        disliked_video.likes-=1
                        disliked_video.dislikes += 1
                        disliked_video.save()

                        new_likes = disliked_video.likes
                        new_dislikes = disliked_video.dislikes
                        return JsonResponse({"dislikes": new_dislikes, "likes": new_likes})

                    else:
                        disliked_playlist.included_video.add(disliked_video)
                        disliked_video.dislikes += 1
                        disliked_video.save()
                        
                        new_dislikes = disliked_video.dislikes
                        return JsonResponse({"dislikes": new_dislikes})
                
                elif disliked_video is not None:
                    disliked_playlist.included_video.remove(disliked_video)
                    disliked_video.dislikes -=1
                    disliked_video.save()

                    new_dislikes = disliked_video.dislikes
                    return JsonResponse({"dislikes": new_dislikes})
        
        elif data['request'] == 'add_video_to_playlist':
            tmp = Playlist.objects.get(pk=data['playlist_pk'])
            tmp.included_video.add(Video.objects.get(slug=slug))
            return HttpResponse('')

        elif data['request'] == 'add_playlist':
            new_playlist_name = urllib.parse.unquote(data['playlist_name'])
            Playlist.objects.create(playlist_name=new_playlist_name, channel_playlist=user)

            selected_playlists = Playlist.objects.filter(channel_playlist__pk=user.id, algo_playlist=False)
            playlists = render_to_string('macavity/ajax/ajaxplaylists.html', {'object_list':selected_playlists})
            return JsonResponse({"html": playlists})
        
        
def check_ajax_request_get_videoplayer(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "GET" and request.headers.get('action') == 'subscribe':
        return True
    else:
        return False

def add_subscriber_channel(slug, user):
    subscribed_at = Channel.objects.get(slug = slug)
    subscriber = user

    if subscriber in subscribed_at.sub_system.all(): 
        subscribed_at.sub_system.remove(subscriber)
    else:
        subscribed_at.sub_system.add(subscriber)
    
    new_sub_num = subscribed_at.sub_system.count()
    #new_sub_num =get_number_of_subs(subscribed_at.pk)
    return JsonResponse({"sub_num": new_sub_num})

def handle_post_request_add_category(request):
    data = json.loads(request.body.decode('UTF-8'))
    if data['request'] == 'add_comment':
        new_cat_name = urllib.parse.unquote(data['cat_name'])

        Category.objects.create(category_name=new_cat_name)
        selected_cats = Category.objects.all()
        cats = render_to_string('macavity/ajax/ajaxcats.html', {'object_list': selected_cats})
        return JsonResponse({"html": cats})
