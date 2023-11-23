from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
import requests
from rest_framework.response import Response
from rest_framework import status
import asyncio
import aiohttp
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

## Getting user data for rendering
user_data_cache = {}


async def get_user_data(session, user_id):
    user_data_url = f"https://jsonplaceholder.typicode.com/users/{user_id}"
    async with session.get(user_data_url) as response:
        if response.status == 200:
            user_data = await response.json()
            user_data_cache[user_id] = user_data

        else:
            return JsonResponse(
                {"error": "The API was unable to fetch User Data"},
                status=status.HTTP_404_NOT_FOUND,
            )


## Getting Posts Details


async def get_posts_data():
    posts_data_url = f"https://jsonplaceholder.typicode.com/posts"
    async with aiohttp.ClientSession() as session:
        async with session.get(posts_data_url) as response:
            if response.status == 200:
                posts = await response.json()

                user_details = [
                    get_user_data(session, post["userId"]) for post in posts
                ]
                await asyncio.gather(*user_details)

                for post in posts:
                    post["user"] = user_data_cache.get(post["userId"])

                return posts

            else:
                return JsonResponse(
                    {"error": "Unable to get Posts Data"},
                    status=status.HTTP_404_NOT_FOUND,
                )


## Getting Posts and User Data to the Home Page
def home(request):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    posts = loop.run_until_complete(get_posts_data())

    if posts is not None:
        context = {"posts": posts}
        return render(request, "index.html", context)
    else:
        return JsonResponse(
            {"message": "Unable to get Posts, Check Later"},
            status=status.HTTP_404_NOT_FOUND,
        )


##User Login Page
@csrf_exempt
def loginPage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user_list_url = "https://jsonplaceholder.typicode.com/users"
        response = requests.get(user_list_url)

        if response.status_code != 200:
            return JsonResponse(
                {"error": "Failed to fetch user data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        users_data = response.json()

        authenticated_user = None
        for user in users_data:
            if user["username"] == username and user["address"]["zipcode"] == password:
                authenticated_user = user
                break

        if authenticated_user:
            # Only include necessary user information in the response
            user_data = {
                "username": authenticated_user["username"],
                "email": authenticated_user["email"],
                # Add other necessary fields
            }
            return JsonResponse({"user": user_data})

        else:
            return JsonResponse(
                {"error": "Incorrect Username or Password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    return render(request, "login.html")


##Logging out an Authenticated User
def logoutPage(request):
    return redirect("home")


## Getting Details on the Posts
import requests
from django.shortcuts import render


def postDetail(request, post_id):
    user_comments_url = f"https://jsonplaceholder.typicode.com/posts/{post_id}/comments"
    response = requests.get(user_comments_url)

    if response.status_code != 200:
        return JsonResponse({
            'error': 'The Data was not Fetched. Check Later'
        }, status=status.HTTP_404_NOT_FOUND)

    user_comments = response.json()

    # Fetch the post related to the first comment (assuming there's at least one comment)
    if user_comments:
        first_comment = user_comments[0]
        post_url = (
            f'https://jsonplaceholder.typicode.com/posts/{first_comment["postId"]}'
        )
        response = requests.get(post_url)

        if response.status_code == 200:
            post = response.json()
            comment_count = len(user_comments)
            context = {
                "user_comments": user_comments,
                "comment_count": comment_count,
                "title": post["title"],
                "body": post["body"],
            }
            return render(request, "post_detail.html", context)
        else:
            return JsonResponse(
                {"error": "Failed to fetch post details"},
                status=status.HTTP_404_NOT_FOUND,
            )

    else:
        return JsonResponse(
            {"error": "No comments found for the post"},
            status=status.HTTP_404_NOT_FOUND,
        )


## Getting All User Posts for a specific user

import aiohttp
import asyncio
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status


async def get_posts():
    posts_url = "https://jsonplaceholder.typicode.com/posts"
    async with aiohttp.ClientSession() as session:
        async with session.get(posts_url) as response:
            try:
                response.raise_for_status()  # Raise an exception for bad responses
                posts = await response.json()
                return posts
            except aiohttp.ClientResponseError as e:
                return None


async def get_user_data(session, user_id):
    user_data_url = f"https://jsonplaceholder.typicode.com/users/{user_id}"
    async with session.get(user_data_url) as response:
        try:
            response.raise_for_status()
            user_data = await response.json()
            return user_data
        except aiohttp.ClientResponseError as e:
            return None


async def userPosts(request):
    user_posts = await get_posts()

    if user_posts is not None:
        user_ids = {post["userId"] for post in user_posts}
        async with aiohttp.ClientSession() as session:
            user_tasks = [get_user_data(session, user_id) for user_id in user_ids]
            user_responses = await asyncio.gather(*user_tasks)

            user_details = {
                user["id"]: user for user in user_responses if user is not None
            }

            # Use a more specific condition for filtering posts, e.g., checking for a specific username
            filtered_posts = [
                post
                for post in user_posts
                if user_details.get(post["userId"], {}).get("username") == "Antonette"
            ]

            context = {"filtered_posts": filtered_posts}
            return render(request, "myposts.html", context)

    else:
        return JsonResponse(
            {"error": "Unable to fetch data for user"}, status=status.HTTP_404_NOT_FOUND
        )


## Getting All Posts by all Users
def usersFeed(usernames):
    feeds_response = requests.get("https://jsonplaceholder.typicode.com/posts")

    if feeds_response.status_code != 200:
        return JsonResponse(
            {"error": "Failed to fetch feeds data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    feeds_data = feeds_response.json()

    user_ids = {feed_data["userId"] for feed_data in feeds_data}
    users_response = requests.get(
        f"https://jsonplaceholder.typicode.com/users?{ '&'.join(f'id={user_id}' for user_id in user_ids)}"
    )

    if users_response.status_code != 200:
        return JsonResponse(
            {"error": "Failed to fetch users data"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    users_data = users_response.json()
    user_data_dict = {user["id"]: user for user in users_data}

    feed = [
        {
            "owner_username": user_data_dict[feed_data["userId"]]["username"],
            "title": feed_data["title"],
            "content": feed_data["body"],
            "id": feed_data["id"],
        }
        for feed_data in feeds_data
        if user_data_dict.get(feed_data["userId"], {}).get("username") in usernames
    ]

    return feed

## Getting User Profile

def get_user_data(username):
    users_response = requests.get('https://jsonplaceholder.typicode.com/users')
    users_data = users_response.json()

    for user_data in users_data:
        if user_data['username'] == username:
            return user_data

    return None

@login_required
def profile(request):
    # Assuming you have a custom user model, you can access the username like this
    logged_in_username = request.user.username

    # If you have a custom user model with additional fields, you may want to use user_id
    # logged_in_user_id = request.user.id

    profile_data = get_user_data(logged_in_username)

    if profile_data is not None:
        return render(request, 'profile.html', {'profile_data': profile_data})
    else:
        return JsonResponse({'error': 'User not found'}, status=404)
    
@login_required
def myFeedData(request):
    interested_usernames = ['Maxime_Nienow', 'Leopoldo_Corkery', 'Kamren', 'Delphine']
    feed = usersFeed(interested_usernames)
    context = {'feed': feed}
    return render(request, 'myfeed.html', context)


