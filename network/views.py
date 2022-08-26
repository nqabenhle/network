import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .forms import *


def index(request):
    return render(request, "network/index.html")


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


def posts(request):
    if request.method == "GET":
        all_posts = list(Post.objects.order_by("timestamp").all().values())

        # k = all_posts["data"]

        for e in all_posts:
            e["username"] = User.objects.get(id=e["user_id"]).username
        
        return JsonResponse({
            "data": all_posts
        })

def profile(request, username):
    user = User.objects.get(username=username)
    followers = Connections.objects.filter(user=user).count()
    following = Connections.objects.filter(follower=user).count()

    if request.user.is_authenticated:
        con = Connections.objects.filter(user=request.user, follower=user)
        f = Connections.objects.filter(user=user, follower=request.user)

    posts = Post.objects.filter(user=user)

    return render(request, "network/profile.html", {
        "followers": followers,
        "following": following,
        "user_profile": request.user == user,
        "follows_you": len(con) == 1 if request.user.is_authenticated else False,
        "already_following": len(f) == 1 if request.user.is_authenticated else False,
        "posts": posts
    })