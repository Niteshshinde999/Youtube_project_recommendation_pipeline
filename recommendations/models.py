from django.db import models
from django.contrib.auth.models import User
# Create your models here.

  

class CategoriesAndSubcategories(models.Model):  
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories_and_subcategories')
    category = models.CharField(max_length=250)
    sub_category = models.TextField()

    
class Playlist(models.Model):
    id = models.AutoField(primary_key=True)
    playlist_id = models.TextField()
    playlist_name = models.TextField(max_length=500)
    total_videos = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')

    def __str__(self):
        return f"{self.playlist_name} (ID: {self.id})"

class Videos(models.Model):
    id = models.AutoField(primary_key=True)
    video_id = models.TextField()
    video_name = models.CharField(max_length=500)
    total_video_length = models.TextField()
    video_view_length = models.TextField(default=0)
    playlist = models.TextField()
    channel_id = models.TextField()
    category = models.CharField(max_length=250)
    video_thumbnail = models.TextField()
    playlist_thumbnail = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Videos')

    def __str__(self):
        return f"{self.video_name} (ID: {self.id})"
    

    
class c_playlist(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='r_playlist')
    category = models.CharField(max_length=250)
    Playlist_id = models.TextField()
    thumbnail = models.TextField()

    def __str__(self):
        return f"Playlist ID: {self.Playlist_id} (User: {self.user.username})"
    
class c_videos(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='r_videos')
    category = models.CharField(max_length=250)
    video_id = models.TextField()
    thumbnail = models.TextField()

    
    def __str__(self):
        return f"Video ID: {self.video_id} (User: {self.user.username})"

class Custom_course(models.Model):
    id = models.AutoField(primary_key= True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='u_course')
    course_name = models.CharField(max_length=250)
    video_id = models.ManyToManyField(c_videos, related_name='c_video')
    Playlist_id = models.ManyToManyField(c_playlist, related_name='c_playlist')

    def __str__(self):
        return f"{self.id}"
    
class r_playlists(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=250)
    playlist_id = models.TextField()
    thumbnail = models.TextField()
    user_id = models.IntegerField()

    def __str__(self):
        return f"{self.id}"
    
class r_videos(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=250)
    video_id = models.TextField()
    thumbnail = models.TextField()
    user_id = models.IntegerField()

    def __str__(self):
        return f"{self.id}"