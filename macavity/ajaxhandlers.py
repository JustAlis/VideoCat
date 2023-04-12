from .models import *
import json
from django.http import HttpResponse, JsonResponse
from .forms import *
import urllib.parse
from django.template.loader import render_to_string
from django.db.models import Q
from .mymixins import *
from django.db import transaction
#I do think that some of this code speak for itself, but you have to check
#static/js/script.js to understand this else if 'filters' for requests
#render_to_strin function renders template and queryset to a string, which could be sent in json
#check if request is sent via ajax and it is get method used
def check_ajax_request_get(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "GET":
        return True
    else:
        return False
    
#handling get requests in player.html, videoplayer view
def handle_get_request_videoplayer(request, slug):

    #get user playlists in videoplayer
    if request.headers.get('get-requets') == 'user-playlists':
        selected_playlists = Playlist.objects.filter(channel_playlist__pk=request.user.id, algo_playlist=False)
        playlists = render_to_string('macavity/ajax/ajaxplaylists.html', {'object_list':selected_playlists})
        return JsonResponse({"html": playlists})
    
    #add/remove subscription in videoplayer
    elif request.headers.get('get-requets') == 'subscribe':
        
        subscribed_at = Video.objects.get(slug = slug).author_channel
        subscriber = request.user

        if subscriber in subscribed_at.sub_system.all(): 
            subscribed_at.sub_system.remove(subscriber)
        else:
            subscribed_at.sub_system.add(subscriber)

        new_sub_num = subscribed_at.sub_system.count()
        return JsonResponse({"sub_num": 'Подписчики: %s' % new_sub_num})
        
#check if request is sent via ajax and it is post method used
def check_ajax_request_post(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "POST":
        return True
    else:
        return False

#handling get requests in player.html, videoplayer view
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
            #get liked and disliked playlists
            algo_playlists = list(Playlist.objects.filter(
                Q(playlist_name='liked')|Q(playlist_name='disliked'),
                channel_playlist__id=user.pk, 
                algo_playlist=True,
            ))
            #I don't know which one is liked or disliked. this filter I need to understand that
            if algo_playlists[1].playlist_name == 'liked':
                liked_playlist, disliked_playlist = algo_playlists[1], algo_playlists[0]
            else:
                liked_playlist, disliked_playlist = algo_playlists[0], algo_playlists[1]

            #atomic prevetn bugs and make the ehole process faster
            with transaction.atomic():
                #get video, wich is liked and check f this video is already liked
                liked_video = Video.objects.filter(
                    pk=data['video_like'], 
                    playlists=liked_playlist
                ).first()
                
                if liked_video is None:
                    #get video if it is not already liked
                    liked_video = Video.objects.get(pk=data['video_like'])
                    #check if liked video is currentle disliked by user
                    if liked_video in disliked_playlist.included_video.all():

                        disliked_playlist.included_video.remove(liked_video)
                        liked_playlist.included_video.add(liked_video)
                        liked_video.dislikes-=1
                        liked_video.likes += 1
                        liked_video.save()

                        new_dislikes = liked_video.dislikes
                        new_likes = liked_video.likes
                        return JsonResponse({"likes": new_likes, "dislikes": new_dislikes})
                    #if video is not in disliked playlist there is no need to remove it from disliked playlist
                    #and change int field in video object
                    else:
                        liked_playlist.included_video.add(liked_video)
                        liked_video.likes += 1
                        liked_video.save()

                        new_likes = liked_video.likes
                        return JsonResponse({"likes": new_likes})
                #if video is already liked
                elif liked_video is not None:
                    liked_playlist.included_video.remove(liked_video)
                    liked_video.likes -=1
                    liked_video.save()
                    
                    new_likes = liked_video.likes
                    return JsonResponse({"likes": new_likes})

        #check like logic. it is similar, with minor naming changes
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
            #get playlist
            tmp = Playlist.objects.get(pk=data['playlist_pk'])
            #add video to playlist
            tmp.included_video.add(Video.objects.get(slug=slug))
            return HttpResponse('')

        elif data['request'] == 'add_playlist':
            #get name of playlist
            new_playlist_name = urllib.parse.unquote(data['playlist_name'])
            #created playlist
            Playlist.objects.create(playlist_name=new_playlist_name, channel_playlist=user)
            #get all playlists
            selected_playlists = Playlist.objects.filter(channel_playlist__pk=user.id, algo_playlist=False)
            playlists = render_to_string('macavity/ajax/ajaxplaylists.html', {'object_list':selected_playlists})
            return JsonResponse({"html": playlists})
        
#chek if request is ajax and get in videoplayer and it is from subscribe button      
def check_ajax_request_get_videoplayer(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == "GET" and request.headers.get('action') == 'subscribe':
        return True
    else:
        return False

def add_subscriber_channel(slug, user):
    subscribed_at = Channel.objects.get(slug = slug)
    subscriber = user
    #check if user is already subscribed
    if subscriber in subscribed_at.sub_system.all(): 
        subscribed_at.sub_system.remove(subscriber)
    else:
        subscribed_at.sub_system.add(subscriber)
    
    new_sub_num = subscribed_at.sub_system.count()
    return JsonResponse({"sub_num": new_sub_num})

#handlig post request for adding new category
def handle_post_request_add_category(request):
    data = json.loads(request.body.decode('UTF-8'))
    if data['request'] == 'add_comment':
        #decode name of new category
        new_cat_name = urllib.parse.unquote(data['cat_name'])

        Category.objects.create(category_name=new_cat_name)
        #return all the categories, to refresh the list is choices field in form on the add video form
        selected_cats = Category.objects.all()
        cats = render_to_string('macavity/ajax/ajaxcats.html', {'object_list': selected_cats})
        return JsonResponse({"html": cats})
