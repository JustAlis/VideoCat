from django.urls import path
from .views import *

urlpatterns = [
    path('', HomePage.as_view(), name='home'),
    path('video/<slug:slug>/', VideoPlayer.as_view(), name='video'),
    path('channel/<slug:slug>/', ChannelView.as_view(), name='channel'),
    path('categories/', CategoriesView.as_view(), name='categories'),
    path('search/', SearchView.as_view(), name='search'),
    path('category/<slug:slug>/', CategoryView.as_view(), name='category'),
    path('playlist/<slug:slug>/', PlaylistView.as_view(), name='playlist'),
    path('login/', LoginUser.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('addvideo/', AddVideo.as_view(), name = 'addvideo'),
    path('changechannel/', ChangeChannel.as_view(), name = 'changechannel'),
    path('changeplaylist/<slug:slug>/', ChangePlaylist.as_view(), name = 'changeplaylist'),
    path('changevideo/<slug:slug>/', ChangeVideo.as_view(), name = 'changevideo'),
    path('addplaylist/', AddPlaylist.as_view(), name = 'addplaylist'),
    path('chunks/<slug:slug>/', video_by_chunks, name='chunks'),
    path('subscribes/', Subscribes.as_view(), name = 'subscribes'),
    path('playlists/<slug:slug>/', PlaylistsView.as_view(), name='playlists'),
    path('videos/<slug:slug>/', VideosView.as_view(), name='videos'),
    path('channeldelete/<slug:slug>/', ChannelDelete.as_view(), name='channeldelete'),
    path('playlistdelete/<slug:slug>/', PlaylistDelete.as_view(), name='playlistdelete'),
    path('videodelete/<slug:slug>/', VideoDelete.as_view(), name='videodelete'),
    path('watched/', redirect_to_watched_playlist, name='watched'),
    path('liked/', redirect_to_liked_playlist, name='liked'),
]

