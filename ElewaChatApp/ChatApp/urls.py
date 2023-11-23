from django.urls import path
from ChatApp import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('login/', views.loginPage, name='login'), 
    path('logout/', views.logoutPage, name='logout'), 
    path('post/<int:post_id>/', views.postDetail, name='post_detail'),
    path('myposts/', views.userPosts, name='myposts') 

]