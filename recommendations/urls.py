from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('index/', views.search_content, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('playlist/<str:playlist_id>/', views.playlist, name='playlist'),
    path('video/<str:video_id>/', views.videos, name='video'),
    path("create_course", views.create_course, name='create_course'),
    path("save_course",views.save_course, name='save_course'),
    path("custom_playlist/<str:playlist_id>/", views.custom_playlist, name='custom_playlist'),
    path("custom_video/<str:video_id>/", views.custom_videos, name='custom_video'),
    path("user_course", views.usercreated_course, name='user_course'),
    path('save_course', views.save_course, name='save_course'),
    path('c_playlist_video/<str:playlist_id>/', views.c_playlist_video, name='c_playlist_video'),
    
]