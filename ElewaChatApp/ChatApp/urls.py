from django.urls import path
from ChatApp import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('allfeed/', views.usersFeed, name='all_feed'), 
    path('login/', views.loginPage, name='login'), 
    path('logout/', views.logoutPage, name='logout'), 
    path('post/<int:post_id>/', views.postDetail, name='post_detail'),
    path('myposts/', views.userPosts, name='my_posts'), 
    path('myfeed/', views.myFeedData, name='my_feed'),
    path('profile/', views.profile, name='profile'),  


]