"""
Contains inputs needed to work out charge demand requirement for an EV

Yazad Sukhia
Feb 2022
"""


# import googlemaps  # pip install googlemaps (or pycharm installation package)
import json
import requests
import pandas as pd

API_KEY = 'AIzaSyCsNLYOColvC8uLS7EeNMRi5nK1kr_KSp8'
# map_client = googlemaps.Client(API_KEY)

journey_start = "Bristol, UK, BS8 2AB"
journey_end = "Bristol, UK, BS1 2NJ"

# base url
# url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&"
# r = requests.get(url + "origins=" + journey_start + "&destinations=" + journey_end + "&key" + API_KEY)

url = ('https://maps.googleapis.com/maps/api/distancematrix/json'
       + '?language=en-US&units=imperial'
       + '&origins={}'
       + '&destinations={}'
       + '&key={}'
       ).format(journey_start, journey_end, API_KEY)

payload={}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
# # get response
# r = requests.get(url + "origins=" + journey_start + "&destinations=" + journey_end + "&key" + API_KEY)
#
# # return time as text and seconds
# time = r.json()["rows"][0]["elements"][0]["duration"]["text"]
# seconds = r.json()["rows"][0]["elements"][0]["duration"]["value"]
#
# # print what we have so far
# print("the total journey time is", time)

# def define_journey():
#     API_KEY = 'AIzaSyC08mMBGKbKzHBZ2FX7JmUsv3Kh9KPkIPg'
#     map_client = googlemaps.Client(API_KEY)
#     journey_start = "Bristol, UK, BS8 2AB" # This should be read from input file
#     journey_end = "Bristol, UK, BS1 2NJ" # This should be read from input file
#     return API_KEY, map_client, journey_start, journey_end