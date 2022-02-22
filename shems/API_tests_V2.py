"""
Contains inputs needed to work out charge demand requirement for an EV

Yazad Sukhia
Feb 2022
"""

import urllib.request
import json

API_KEY = 'AIzaSyCsNLYOColvC8uLS7EeNMRi5nK1kr_KSp8'
#map_client = googlemaps.Client(API_KEY)

origin = '2500+E+Kearney+Springfield+MO+65898'
destination = '405+N+Jefferson+Ave+Springfield+MO+65806'

# url request
url = ('https://maps.googleapis.com/maps/api/distancematrix/json'
       + '?language=en-US&units=imperial'
       + '&origins={}'
       + '&destinations={}'
       + '&key={}'
       ).format(origin, destination, API_KEY)

# base url
# url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&"
# r = requests.get(url + "origins=" + journey_start + "&destinations=" + journey_end + "&key" + API_KEY)

# get response
response = urllib.request.urlopen(url)
response_json = json.loads(response.read())
distance_meters = response_json['rows'][0]['elements'][0]['distance']['value']
distance_minutes = response_json['rows'][0]['elements'][0]['duration']['value'] / 60

print("Origin: %s\nDestination: %s\nDistance (Meters): %s\nDistance (Seconds): %s"
      % (origin, destination, distance_meters, round(distance_minutes, 2)))

# def define_journey():
#     API_KEY = 'AIzaSyC08mMBGKbKzHBZ2FX7JmUsv3Kh9KPkIPg'
#     map_client = googlemaps.Client(API_KEY)
#     journey_start = "Bristol, UK, BS8 2AB" # This should be read from input file
#     journey_end = "Bristol, UK, BS1 2NJ" # This should be read from input file
#     return API_KEY, map_client, journey_start, journey_end