"""
Contains API functionality that links to googlemaps_API in order to calculate the distance between
an origin location and desired destination. Returns the time taken to travel between each point.

Yazad Sukhia
Feb 2022
"""


import googlemaps  # pip install googlemaps (or pycharm installation package)

API_KEY = 'AIzaSyCsNLYOColvC8uLS7EeNMRi5nK1kr_KSp8'
map_client = googlemaps.Client(API_KEY)

journey_start = "Bristol, UK, BS8 2AB"
journey_end = "Bristol, UK, BS1 2NJ"

