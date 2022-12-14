import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator

from .models import *
from .forms import *


def index(request):
    post_list = Post.objects.order_by("-timestamp").all()
    paginator = Paginator(post_list, 10)
    
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "network/index.html", {
        "all_posts": page_obj
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

@csrf_exempt
@login_required(login_url="/login")
def post(request):
    if request.method == "POST":
        data = json.loads(request.body)
        post = Post(user=request.user, content=data.get("post", ""))
        post.save()

        return JsonResponse({"message": "Success"}, status=200)

    return render(request, "network/new_post.html")


@csrf_exempt
@login_required(login_url="/login")
def likes(request, post_id):
    data = json.loads(request.body)
    post = Post.objects.get(pk=post_id)

    if data.get("action", "") == "upvote":
        upvote = Likes(post=post, user=request.user)
        upvote.save()
        post.likes += 1
        post.save()

    else:
        downvote = Likes.objects.get(post=post, user=request.user)
        downvote.delete()
        post.likes -= 1
        post.save()

    return JsonResponse({"message": "success"}, status=200)    

@csrf_exempt
def profile(request, username):
    user = User.objects.get(username=username)

    if request.method == "GET":
        followers = Connections.objects.filter(user=user).count()
        following = Connections.objects.filter(follower=user).count()

        if request.user.is_authenticated:
            con = Connections.objects.filter(user=request.user, follower=user)
            f = Connections.objects.filter(user=user, follower=request.user)

        posts = Post.objects.filter(user=user)
        paginator = Paginator(posts, 10)

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(request, "network/profile.html", {
            "username": username,
            "followers": followers,
            "following": following,
            "user_profile": request.user == user,
            "follows_you": len(con) == 1 if request.user.is_authenticated else False,
            "already_following": len(f) == 1 if request.user.is_authenticated else False,
            "posts": page_obj
        })

    else:
        data = json.loads(request.body)
        if data.get("data", "") == "follow":
            con = Connections(user=user, follower=request.user)
            con.save()
        else:
            con = Connections.objects.get(user=user, follower=request.user)
            con.delete()

        return JsonResponse({"message": "success"}, status=200)


@csrf_exempt
@login_required(login_url="/login")
def edit(request, post_id):
    post = Post.objects.get(pk=post_id)

    if request.method == "POST":
        data = json.loads(request.body)
        post.content = data.get("post", "")
        post.save()

        return JsonResponse({"message": "success"}, status=200)
        
    else:
        if request.user != post.user:
            return HttpResponse("<h1>You are not authorized to open this page.</h1>")

        return render(request, "network/new_post.html", {
            "content": post.content,
            "post_id": post_id
        })

@login_required(login_url="/login")
def following(request):
    connections = Connections.objects.filter(follower=request.user)
    posts = []

    for con in connections:
        user_posts = Post.objects.filter(user=con.user)
        for post in user_posts:
            posts.append(post)

    ordered_posts = sorted(posts, key=lambda d: d.timestamp, reverse=True)
 
    paginator = Paginator(ordered_posts, 10)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "network/index.html", {
        "all_posts": page_obj,
        "followers": True
    })
