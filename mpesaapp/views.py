from requests import request
from django.http import HttpResponse, JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
from requests.auth import HTTPBasicAuth
import json
from django.shortcuts import render, redirect
import os

from dotenv import load_dotenv
from mpesaapp.models import *

from coreapp.views import *

#from mpesa.mpesa_credentials import LipanaMpesaPassword, MpesaAccessToken

from mpesaapp.mpesa_credentials import *

def fetch_user_data(username):
    users_response = requests.get('https://jsonplaceholder.typicode.com/users')
    users_data = users_response.json()

    for user_data in users_data:
        if user_data['username'] == username:
            return user_data

    return None

def getAccessToken(request):
    consumer_key = 'qgyjqgIwdfa8g6ujHD7Eqe52HqYcFahY' #os.environ.get('CONSUMER_KEY')
    consumer_secret = 'Lq2qcMgnN9qSOMuj' #os.environ.get('CONSUMER_SECRET')
    api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    if r.status_code == 200:
        mpesa_access_token = json.loads(r.text)
        validated_mpesa_access_token = mpesa_access_token['access_token']
        return HttpResponse(validated_mpesa_access_token)
    else:
        return HttpResponse("Failed to generate access token")


def lipa_na_mpesa_online(request):
    if not request.user.is_authenticated:
        return redirect('coreapp:home')
               
    phone_number = request.user.phone   

    access_token = MpesaAccessToken.validated_mpesa_access_token
    api_URL = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {"Authorization": "Bearer %s" % access_token}
    mpesa_request = {
        "BusinessShortCode" : LipanaMpesaPassword.business_short_code, 
        "Password" : LipanaMpesaPassword.decode_password, 
        "Timestamp": LipanaMpesaPassword.lipa_time, 
        "TransactionType": "CustomerPayBillOnline", 
        "Amount" :  1,
        "PartyA": 'phone',
        "PartyB" : LipanaMpesaPassword.business_short_code, 
        "PhoneNumber" : 'phone', 
        "CallBackURL" : "https://sandbox.safaricom.co.ke/mpesa/", 
        "AccountReference" : "ElewaChatApp Premium", 
        "TransactionDesc" : "Making Payment for ElewaChatApp premium"
    }
    response = requests.post(api_URL, json=mpesa_request, headers=headers)
    context = {'access_token': access_token, 'api_URL':api_URL, 'headers':headers, 'request': request}
    if response.status_code == 200:        
        return render(request, 'password_prompt.html' )
    else:
        error_message = response.json()['errorMessage']
        print(error_message)
        
        return HttpResponse("The payment was Unsuccessful")


@csrf_exempt
def register_urls(request):
    access_token = MpesaAccessToken.validated_mpesa_access_token
    api_URL = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
    headers = {"Authorization": "Bearer %s" % access_token}
    options = {
        "ShortCode" : "LipanaMpesaPassword.business_short_code",
        "ResponseType" : "Completed/Cancelled", 
        "ConfirmationURL" : "https://595b-41-72-198-62.ngrok-free.app/api/v1/c2b/confirmation",
        "ValidationURL": "https://595b-41-72-198-62.ngrok-free.app/api/v1/c2b/validation" 
    }

    response = requests.post(api_URL, json = options, headers= headers)
    return HttpResponse(response.text) 


@csrf_exempt
def call_back(request):
    pass


@csrf_exempt
def validation(request):
    context = {
        "ResultCode" : 0, 
        "ResultDesc" : "Accepted"
    }
    return  JsonResponse(dict(context))


@csrf_exempt
def confirmation(request):
    mpesa_body = request.body.decode('utf-8')
    mpesa_payment = json.loads(mpesa_body)
    payment = MpesaPayment(
        first_name = mpesa_payment['FirstName'],
        middle_name = mpesa_payment['MiddleName'],
        last_name = mpesa_payment['LastName'], 
        description = mpesa_payment['TransID'],
        phone_number = mpesa_payment['MSISDN'], 
        amount = mpesa_payment['TransAmount'],
        reference = mpesa_payment['BillRefNumber'], 
        organization_balance = mpesa_payment['OrgAccountBalance'], 
        type = mpesa_payment['TransactionType'], 
    )
    payment.save()
    context = {
        "ResultCode" : 0, 
        "ResultDesc" : "Accepted"
    }
    #return JsonResponse(dict(context))
    if mpesa_payment['ResultCode'] == 0:
        return render(request, 'payment_success.html')
    else:
        return redirect(request, 'payment_unsuccessful.html')
