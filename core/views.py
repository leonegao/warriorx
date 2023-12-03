from email.mime import image
from itertools import chain
import os
import random
from django.contrib import messages
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.models import User,auth # type: ignore
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import CommentForm
from .models import Profile,Post,LikePost,FollowersCount
import magic
import cv2
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import speech_recognition as sr
import moviepy.editor as mp

def validationFiles(file):
    accept = ['video/mp4']
    flag = True
    fileType = magic.from_buffer(file.read(1024), mime=True)

    # Check if the file type is accepted
    if fileType not in accept:
        flag = False
    return flag

@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    user_post=Post.objects.all()

    user_following_list = []
    feed = []
    all_user_object=[user_post]

    user_following = FollowersCount.objects.filter(follower=request.user.username)

    for users in user_following:
        user_following_list.append(users.user)

    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user=usernames)
        feed.append(feed_lists)

    feed_list = list(chain(*feed))

    # user suggestion starts
    all_users = User.objects.all()
    user_following_all = []

    for user in user_following:
        user_list = User.objects.get(username=user.user)
        user_following_all.append(user_list)

    new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    current_user = User.objects.filter(username=request.user.username)
    final_suggestions_list = [x for x in list(new_suggestions_list) if ( x not in list(current_user))]
    random.shuffle(final_suggestions_list)

    username_profile = []
    username_profile_list = []

    for users in final_suggestions_list:
        username_profile.append(users.id) # type: ignore
    for ids in username_profile:
        profile_lists = Profile.objects.filter(id_user=ids)
        username_profile_list.append(profile_lists)
    suggestions_username_profile_list = list(chain(*username_profile_list))
    return render(request, 'index.html', {'user_profile': user_profile, 'posts':feed_list, 'suggestions_username_profile_list': suggestions_username_profile_list[:10],'all_user_object':all_user_object})

def signup(request):
    if request.method =='POST':
        username= request.POST['username']
        password= request.POST['password']
        firstname= request.POST['firstname']
        lastname=request.POST['lastname']
        confirmPassword= request.POST['confirmPassword']
        email= request.POST['email']
        if password != confirmPassword:
            messages.info(request,'Password do not match ')
            return redirect('signup')
        elif User.objects.filter(email=email).exists():
            messages.info(request,'Please try other email ')
            return redirect('signup')
        elif User.objects.filter(email=username).exists():
            messages.info(request,'Please try other username ')
            return redirect('signup')
        elif firstname == "" and lastname == "" and username ==""  and password== "" and email =="":
            messages.info(request,'Do not leave any fields empty')
            return redirect('signup')

        else:
            user=User.objects.create_user(username=username,email=email,password=password)
            user.save()
            userlogin=auth.authenticate(username=username,password=password)
            auth.login(request,userlogin)
            #create a new profile object to the user
            user_model= User.objects.get(username=username)
            new_profile = Profile.objects.create(user=user_model,id_user= user_model.id)
            new_profile.save()
            return redirect('settings')


    else:
        return render(request, 'signup.html')

def signin(request):
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']
        user=auth.authenticate(username=username,password=password)
        if user is not None:
            auth.login(request,user)
            return redirect('/')
        else:
            messages.info(request,'Wrong credentials')
            return redirect('signin')
    else:
        return render(request,'signin.html')

@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')
@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        if request.FILES.get('image')==None:
            image=user_profile.profileimg
            bio=request.POST['bio']
            location=request.POST['location']

            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        if request.FILES.get('image') != None:
            image = request.FILES.get('image')
            bio = request.POST['bio']
            location = request.POST['location']

            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        else:
            return redirect('/')

        return redirect('/')
    return render(request,'setting.html',{'user_profile': user_profile})

@login_required(login_url='signin')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        video= image.name
        caption = request.POST['caption']
        if validationFiles(image):
            new_post = Post.objects.create(user=user, image=image, caption=caption)
            new_post.save()
            return redirect('/')
        else:
            return redirect('/')
    else:
        return redirect('/')

@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()
    #check if the user like the post
    if like_filter == None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes +=1
        post.save()
        return redirect('/')
    else:
        like_filter.delete()
        post.no_of_likes -=1
        post.save()
        return redirect('/')

@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = len(user_posts)
    follower = request.user.username
    user = pk


    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    user_followers = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))
    #create a dictionary for the user page
    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,
    }
    return render(request, 'profile.html', context)

@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect('/profile/'+user)
        else:
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect('/profile/'+user)
    else:
        return redirect('/')


@login_required(login_url='signin')
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        username_profile_list = []

        for users in username_object:
            username_profile.append(users.id) # type: ignore

        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)

        username_profile_list = list(chain(*username_profile_list))
    return render(request, 'search.html', {'user_profile': user_profile, 'username_profile_list': username_profile_list})



    # Get the current user object and profile
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    # Get all the posts and order them by creation date
    posts = Post.objects.all().order_by('-created_at')
    # Create a comment form for each post
    comment_forms = {}
    for post in posts:
        comment_forms[post.id] = CommentForm()
    # Handle the comment submission
    if request.method == 'POST':
        # Get the post id and the comment form from the request
        post_id = request.POST.get('post_id')
        comment_form = CommentForm(request.POST)
        # Validate the comment form
        if comment_form.is_valid():
            # Save the comment to the database
            comment = comment_form.save(commit=False)
            comment.post = Post.objects.get(id=post_id)
            comment.user = request.user
            comment.save()
            # Redirect to the index page
            return redirect('allVideosComments')
    # Render the index template with the context variables
    return render(request, 'delete.html', {
        'user_profile': user_profile,
        'posts': posts,
        'comment_forms': comment_forms
    })

@login_required(login_url='signin')
def allVideos(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile=Profile.objects.get(user=user_object)
    posts= Post.objects.all()

    return render(request,'allVideos.html',{'user_profile':user_profile, 'posts': posts})


@login_required
def delete_post(request, uuid):
    # Get the post object by its UUID or return a 404 error if not found
    post = get_object_or_404(Post, id=uuid)
    # Check if the user is the owner of the post or an admin
    if request.user == post.user or request.user.is_staff:
        # Delete the post object from the database
        post.delete()
        # Redirect to the home page or any other page you want
        return redirect('/')
    else:
        # Return a 403 error or a custom message if the user is not authorized
        return HttpResponseForbidden('You are not allowed to delete this post.')


def test(request):
    return render(request,'delete.html')
def mylogin(request):
  return render(request, 'mylogin.html')