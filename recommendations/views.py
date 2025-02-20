import requests
import json
from django.shortcuts import render, redirect, get_list_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Videos, Playlist, CategoriesAndSubcategories, Custom_course, c_playlist, c_videos , r_playlists, r_videos
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

# Create your views here.

#HOME
def home(request):
    return render(request, 'home.html')

#SIGNUP
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form':form, 'error':form.errors})

#LOGIN
def login_view(request):
    if request.method == 'POST':
        P_username = request.POST.get('username')
        P_password = request.POST.get("password")
        user = authenticate(request, username = P_username, password = P_password)
        if user:
            auth_login(request, user)
            return redirect('index')
        else:
            return render(request, 'login.html', {'error' : 'invalid username and password'})
    return render(request, 'login.html')

#LOGOUT
def logout_view(request):
    auth_logout(request)
    return redirect('login')

#YOUTUBE DATA
YOUTUBE_API_KEY = "AIzaSyBVb3q_P7yALzBMJKSXuHtPygS3uHKSRPw"
def get_youtube_data(query):
    youtube_search_url = "https://www.googleapis.com/youtube/v3/search"
    parameters = {
        "part" : 'snippet',
        "q" : query,
        "key" : YOUTUBE_API_KEY,
        "maxResults" : 10,
        "type" : "playlist"
    }

    response = requests.get(youtube_search_url, params=parameters)
    response_data = response.json()

    data = {
        'playlists' : [],
        'videos' : [],
        'channels' : []
    }

    for item in response_data.get("items", []):
        item_id = item.get("id", {})

        if item_id.get("kind") == "youtube#playlist":

            data["playlists"].append({
                "id" : item_id.get("playlistId"),
                "title" : item['snippet']['title'],
                "description": item['snippet']['description'],
                "channel_title": item['snippet']['channelTitle'],
                "thumbnail" : item['snippet']['thumbnails']['medium']['url']
            })
    return data

#Playlist title and thumbnail
def playlist_title(playlist_id):
    youtube_palylist_details_url =  "https://www.googleapis.com/youtube/v3/playlists"
    
    parameters = {
        "part":"snippet",
        "id":playlist_id,
        "key":YOUTUBE_API_KEY,

    }

    playlist_response = requests.get(youtube_palylist_details_url, params=parameters)
    playlist_response_data = playlist_response.json()
    if(playlist_response_data):
        playlist_title = playlist_response_data['items']
        p_title = playlist_title[0]['snippet']['title']
        p_thumbnail = playlist_title[0]['snippet']['thumbnails']['medium']['url']

    data = {
        'p_title':p_title,
        'p_thumbnail':p_thumbnail
    }
    return data

#PLAYLISTS
@login_required
def playlist(request, playlist_id):
    youtube_palylist_url =  "https://www.googleapis.com/youtube/v3/playlistItems"

    parameters = {
        "part" : "snippet",
        "playlistId" : playlist_id,
        "key":YOUTUBE_API_KEY,
        "maxResults":100
    }
    playlist_videos = []

    response = requests.get(youtube_palylist_url, params=parameters)
    response_data = response.json()

    for item in response_data.get("items", []):
        video={
            "id":item['snippet']['resourceId']['videoId'],
            "title":item['snippet']['title'],
            "channel_title":item['snippet']['channelTitle'],
            "thumbnail":item['snippet']['thumbnails']['medium']['url']
        }
        playlist_videos.append(video)
    
    total_video = len(playlist_videos)
    playlist_name_thumbnail = playlist_title(playlist_id)

    user_view = request.session.get("current_view_data")
    user_view['playlist length'] = total_video
    user_view['playlist_id'] = playlist_id
    user_view['playlist title'] = playlist_name_thumbnail['p_title']
    user_view['playlist thumbnail'] = playlist_name_thumbnail['p_thumbnail']
    request.session['current_view_data'] = user_view

    return render(request, 'playlist_videos.html', {'playlist_videos' : playlist_videos})

#video durations
def video_durations(yt_duration):
    h = m = s = 0
    yt_duration = yt_duration.replace("PT", "")

    if "H" in yt_duration:
        h, yt_duration = yt_duration.split("H")
        h = int(h)
    if "M" in yt_duration:
        m, yt_duration = yt_duration.split("M")
        m = int(m)
    if "S" in yt_duration:
        s = int(yt_duration.replace("S", ""))
    return f"{h:02}:{m:02}:{s:2}"

#QUESTION GENERATION
def generate_question(topic):
    import sys 
    from .chatGPT import getData

    # Extract arguments
    # num_questions = sys.argv[1]  # Number of questions
    # topic = " ".join(sys.argv[2:])  # Topic name

    # Construct the prompt
    prompt_text = f"Generate 5 interview questions of on {topic}. Separate each question with a semicolon ;."


    payload = {
    "model": "gpt-4-turbo",
    "temperature" : 1,
    "messages" : [
        {"role": "system", "content": "Generate interview questions for Job."},
        {"role": "user", "content": prompt_text}
    ]
    }

    content = getData(payload)

    # all = content.split('\"')

    # all = re.findall(r'"(.*?)(?<!\\)"', content)

    if content:
        res = content
    else:
        res = {}

    # print(res)
    return res; 

#videos
@login_required
def videos(request, video_id):
    youtube_video_url = "https://www.googleapis.com/youtube/v3/videos"

    parameters = {
        "part":"snippet, contentDetails, statistics",
        "id" : video_id,
        "key" : YOUTUBE_API_KEY
    }
    videos = []
    response = requests.get(youtube_video_url, params=parameters)
    response_data = response.json()
    if response_data:
        video_title = response_data['items']
        v_title = video_title[0]['snippet']['title']
        v_duration = video_title[0]['contentDetails']['duration']
        v_time = video_durations(v_duration)
        v_channel = video_title[0]['snippet']['channelId']
        v_thumbnail = video_title[0]['snippet']['thumbnails']['medium']['url']
    
    user_view = request.session.get("current_view_data")
    user_view['video_id'] = video_id
    user_view['video title'] = v_title
    user_view['video length'] = v_time
    user_view['channel id'] = v_channel
    user_view['video thumbnail'] = v_thumbnail
    request.session['current_view_data']=user_view

    playlist_instance = Playlist.objects.create(
        user_id = request.user.id,
        playlist_id = request.session.get("current_view_data")['playlist_id'],
        playlist_name = request.session.get("current_view_data")['playlist title'],
        total_videos = request.session.get("current_view_data")['playlist length']
    )

    Videos.objects.create(
        user_id = request.user.id,
        video_id = request.session.get('current_view_data')['video_id'],
        video_name = request.session.get('current_view_data')['video title'],
        total_video_length = request.session.get('current_view_data')['video length'],
        playlist = request.session.get("current_view_data")['playlist_id'],
        channel_id = request.session.get("current_view_data")['channel id'],
        category = request.session.get("current_view_data")['category'],
        video_thumbnail = request.session.get("current_view_data")['video thumbnail'],
        playlist_thumbnail = request.session.get("current_view_data")['playlist thumbnail']
    )

    v_t = request.session.get('current_view_data')['video title']
    q_a_data = generate_question(v_t)

    data = json.loads(q_a_data)
    question = [q.strip() for q in data['message'].split(";") if q.strip()]
    return render(request, 'video.html', {'video':response_data, 'questions':question})

#recommendations    
def c_recommendation(request):
    categories = CategoriesAndSubcategories.objects.filter(user=request.user)

    recommended_courses = {}

    for category in categories:
        category_name = category.category

        playlists = r_playlists.objects.filter(category=category_name)
        videos = r_videos.objects.filter(category=category_name)\
        
        playlist_data = [(p.playlist_id, p.thumbnail) for p in playlists]
        video_data = [(v.video_id, v.thumbnail) for v in videos]

        recommended_courses[category_name] = {
            'playlists': playlist_data,
            'videos': video_data
        }
    return recommended_courses

#Search content
@login_required
def search_content(request):
    youtube_data = None
    if request.method == "POST":
        P_category = request.POST.get('category')
        P_sub_category = request.POST.get("search_topic")
        if P_category:
            query = f"{P_sub_category} in {P_category}"
            youtube_data = get_youtube_data(query)

            CategoriesAndSubcategories.objects.create(
                user_id = request.user.id,
                category = P_category,
                sub_category = P_sub_category
            )

            request.session['current_view_data']={
                'user_id':request.user.id,
                'category' : P_category,
                'subcategory' : P_sub_category,
                'playlist_id' : '',
                'playlist length' : '',
                'playlist title' : '',
                'playlist thumbnail' : '',
                'video_id' : '',
                'video title': '',
                'video thumbnail' :'',
                'video view length' : '',
                'channel id' : ''
            }
            return render(request, "playlist.html", {'youtube_data':youtube_data})
    recommendation = c_recommendation(request)
    return render(request, 'index.html', {'recommendation_courses' : recommendation})
    
#create course
@login_required
def create_course(request):
    if request.method == 'POST':
        customcourse = request.session.get('custom_course', {})
        P_category = customcourse.get('category') or request.POST.get('category', '')
        P_sub_category = customcourse.get("subCategory") or request.POST.get('search_topic', '')
        P_coursename = customcourse.get('course_name') or request.POST.get('course_name', '')
        P_playlist = customcourse.get('playlist', [])
        P_videos = customcourse.get('videos', [])

        youtube_data = []

        request.session['custom_course'] = {
            'category' : P_category,
            'subCategory' : P_sub_category,
            'course_name' : P_coursename,
            'userId' : request.user.id,
            'playlist' : P_playlist,
            'videos' : P_videos 
        }

        if P_category:
            query = f"{P_sub_category} in {P_category}"
            youtube_data = get_youtube_data(query)

            P_playlist = request.POST.getlist("playlists") or P_playlist
            customcourse['playlist'] = P_playlist
            request.session['custom_course']['playlist'] = P_playlist

            # customcourse['playlist'] = list(set(customcourse['playlist'] + P_playlist))

            # request.session['custom_course'] = customcourse
            # # request.session.modified = True

        selectedPlaylistData = customcourse.get('playlist', [])
        selectedPlaylist = []
        if selectedPlaylistData:
            for i in selectedPlaylistData:
                pData = i.split(':&:')
                selectedPlaylist.append(pData[0])
        return render(request, 'custom_playlist.html', {'youtube_data' : youtube_data, 'selctedPlaylist':selectedPlaylist})
    
    else:
        request.session['custom_course'] = {
            'category': '',
            'subcategory': '',
            'course_name' : '',
            'userId' : request.user.id,
            'playlist':[],
            'videos':[],
        }
        return render(request, "custom_course.html")

#custom playlist
@login_required
def custom_playlist(request, playlist_id):
    youtube_palylist_url =  "https://www.googleapis.com/youtube/v3/playlistItems"

    parameters= {
        "part":"snippet",
        "playlistId":playlist_id,
        "key" : YOUTUBE_API_KEY,
        "maxResults":100
    }

    playlist_videos = []

    response = requests.get(youtube_palylist_url, params=parameters)
    response_data = response.json()
    for item in response_data.get("items", []):
        video = {
            "id":item['snippet']['resourceId']['videoId'],
            "title":item['snippet']['title'],
            "channel_title" : item['snippet']['channelTitle'],
            "thumbnail" : item['snippet']['thumbnails']['medium']['url']
        }
        playlist_videos.append(video)
    
    customcourse = request.session.get("custom_course")

    if request.method == "POST":
        videos = request.POST.getlist("video_choice")
        if "custom_course" not in request.session:
            request.session['custom_course'] = {'videos': []}
        
        customcourse['videos'] = list(set(customcourse['videos'] + videos))

        request.session['custom_course'] = customcourse
        request.session.modified = True

    selectedvideoData = customcourse.get('videos', [])
    selectedvideo = []
    if selectedvideoData:
        for i in selectedvideoData:
            pData = i.split(":&:")
            selectedvideo.append(pData[0])
    return render(request, 'custom_playlist_video.html', {'selectedvideo':selectedvideo, 'playlist_videos': playlist_videos})

#course playlist videos
@login_required
def c_playlist_video(request,playlist_id):
    
    youtube_palylist_url =  "https://www.googleapis.com/youtube/v3/playlistItems"

    parameters = {
        "part": "snippet",
        "playlistId":playlist_id,
        "key":YOUTUBE_API_KEY,
        "maxResults":100
    }

    playlist_videos =[]

    response = requests.get(youtube_palylist_url, params=parameters)
    response_data = response.json()
    for item in response_data.get("items", []):
        video={
            "id":item["snippet"]['resourceId']["videoId"],
            "title":item["snippet"]["title"],
            "channel_title":item['snippet']['channelTitle'],
            'thumbnail':item['snippet']['thumbnails']['medium']['url']
        }
        playlist_videos.append(video)
    return render(request, 'c_playlist_video.html', {'playlist_videos': playlist_videos})

#custom_video
@login_required
def custom_videos(request,video_id):
    youtube_video_url = "https://www.googleapis.com/youtube/v3/videos"
    
    parameters = {
        "part":"snippet,contentDetails,statistics",
        "id":video_id,
        "key":YOUTUBE_API_KEY
    }
    videos=[]
    response = requests.get(youtube_video_url, params=parameters)
    response_data = response.json()
    
    print(response_data)
    video_data = response_data['items']
    video_t = video_data[0]['snippet']['title']
    q_a_data = generate_question(video_t)
    data = json.loads(q_a_data)
    questions = [q.strip() for q in data["message"].split(";") if q.strip()]

    return render(request, 'custom_video.html', {'video': response_data, 'questions':questions})

#save course
@login_required
def save_course(request):
    customcourse = request.session.get("custom_course")
    if request.method == 'POST':
        course_playlists = []
        course_videos = []

        if customcourse['playlist'] != None:
            for i in customcourse['playlist']:
                pData = i.split(':&:')
                course_playlist = c_playlist.objects.create(
                    user_id = request.user.id,
                    Playlist_id = pData[0],
                    thumbnail = pData[1],
                    category = request.session.get('custom_course')['category']
                )
                course_playlists.append(course_playlist)

        if customcourse['videos'] != None:
            for j in customcourse['videos']:
                vData = j.split(':&:')
                course_video = c_videos.objects.create(
                    user_id = request.user.id,
                    video_id = vData[0],
                    thumbnail = vData[1],
                    category = request.session.get('custom_course')['category']
                )
                course_videos.append(course_video)

        if customcourse['playlist'] or customcourse['videos']:
            c_course = Custom_course.objects.create(
                user_id = request.user.id,
                course_name = request.session.get('custom_course')['course_name']
            )
            c_course.video_id.set(course_videos)
            c_course.Playlist_id.set(course_playlists)

        return redirect('/user_course')
    
    course_data = {
            'course_name': '',
            'videos': [],
            'playlists': []
        }

    if customcourse:
        course_data['course_name'] = customcourse.get('course_name', '')

        if customcourse.get('playlist'):
            course_data['playlists'] = [
                {'id': i.split(':&:')[0], 'thumbnail': i.split(':&:')[1]}
                for i in customcourse['playlist']
            ]

        if customcourse.get('videos'):
            course_data['videos'] = [
                {'id': j.split(':&:')[0], 'thumbnail': j.split(':&:')[1]}
                for j in customcourse['videos']
            ]

    return render(request, 'save_course.html', {'course': course_data})

#user created course
@login_required
def usercreated_course(request): 
    customcourses = Custom_course.objects.filter(user=request.user)  # QuerySet of courses
    
    courses_list = []  # Store multiple courses

    for course in customcourses:
        p = list(course.Playlist_id.values_list('Playlist_id', 'thumbnail'))  # Get playlist IDs
        v = list(course.video_id.values_list('video_id', 'thumbnail'))  # Get video IDs

        courses_list.append({
            'course_name': course.course_name,  # Get course name
            'video_id': [{'id': vid, 'thumbnail': thumb} for vid, thumb in v],  # List of videos with thumbnails
            'playlist_id': [{'id': pid, 'thumbnail': thumb} for pid, thumb in p],  # List of playlists with thumbnail 
        })

    return render(request, 'user_course.html', {'courses':courses_list})