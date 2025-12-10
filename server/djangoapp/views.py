# Uncomment the required imports before adding the code

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from datetime import datetime

from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from .populate import initiate
from .restapis import get_request, analyze_review_sentiments
from .models import CarMake, CarModel

def get_cars(request):
    count = CarMake.objects.filter().count()
    print(count)
    if(count == 0):
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append({"CarModel": car_model.name, "CarMake": car_model.car_make.name})
    return JsonResponse({"CarModels":cars})

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.

# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    # Get username and password from request.POST dictionary
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    # Try to check if provide credential can be authenticated
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        # If user is valid, call login method to login current user
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)

# Create a `logout_request` view to handle sign out request
@csrf_exempt
def logout_user(request):    
    logout(request) # Terminate user session
    data = {"userName":""} # Return empty username
    return JsonResponse(data)
# def logout_request(request):
# ...

# Create a `registration` view to handle sign up request
# @csrf_exempt
# def registration(request):
# ...
@csrf_exempt
def registration(request):
    context = {}

    # read JSON data sent from the frontend
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']

    username_exist = False

    # check if username already exists
    try:
        User.objects.get(username=username)
        username_exist = True
    except User.DoesNotExist:
        # new user, just log info
        logger.debug("%s is a new user", username)

    # if it’s a new user
    if not username_exist:
        # create user in auth_user table
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        # log the user in
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    else:
        # optional: tell frontend that the user exists
        data = {"userName": username, "status": "UserAlreadyExists"}

    return JsonResponse(data)

# # Update the `get_dealerships` view to render the index page with
# a list of dealerships
# def get_dealerships(request):
# ...
#Update the `get_dealerships` render list of dealerships all by default, particular state if state is passed
def get_dealerships(request, state="All"):
    if(state == "All"):
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/"+state
    dealerships = get_request(endpoint)
    return JsonResponse({"status":200,"dealers":dealerships})
# Create a `get_dealer_reviews` view to render the reviews of a dealer
# def get_dealer_reviews(request,dealer_id):
# ...
# 🔹 Step 2 – get a single dealer's details
def get_dealer_details(request, dealer_id):
    # build endpoint for this dealer
    endpoint = f"/fetchDealer/{dealer_id}"
    dealer_detail = get_request(endpoint)
    return JsonResponse({"status": 200, "dealer": dealer_detail})


# 🔹 Step 3 – get reviews for a dealer + call sentiment microservice
def get_dealer_reviews(request, dealer_id):
    # 1) fetch reviews from your Node/Mongo microservice
    endpoint = f"/fetchReviews/dealer/{dealer_id}"
    reviews = get_request(endpoint)

    # 2) for each review, call sentiment analyzer and attach sentiment
    for review in reviews:
        text = review.get("review", "")
        if not text:
            review["sentiment"] = "neutral"
            continue

        sentiment_result = analyze_review_sentiments(text)

        # try to extract sentiment string from the JSON returned
        sentiment = None
        if isinstance(sentiment_result, dict):
            # depending on your microservice it may be "sentiment" or "label"
            sentiment = (
                sentiment_result.get("sentiment")
                or sentiment_result.get("label")
            )
        else:
            # if it returns a plain string
            sentiment = str(sentiment_result)

        review["sentiment"] = sentiment or "neutral"

    # 3) return JSON with all reviews + sentiments
    return JsonResponse({"status": 200, "reviews": reviews})
# Create a `get_dealer_details` view to render the dealer details
# def get_dealer_details(request, dealer_id):
# ...

# Create a `add_review` view to submit a review
def add_review(request):
    if(request.user.is_anonymous == False):
        data = json.loads(request.body)
        try:
            response = post_review(data)
            return JsonResponse({"status":200})
        except:
            return JsonResponse({"status":401,"message":"Error in posting review"})
    else:
        return JsonResponse({"status":403,"message":"Unauthorized"})
# def add_review(request):
# ...
