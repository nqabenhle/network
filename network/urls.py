
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("following", views.following, name="following"),
    path("post/new", views.post, name="new_post"),
    path("post/edit/<int:post_id>", views.edit, name="edit"),
    path("<str:username>", views.profile, name="profile"),
    path("post/like/<int:post_id>", views.likes, name="like_post")
]
