"""
Script contains function which enable links to the googlemaps API service, allowing the
distance and tie of a journey to be calculated based on two addresses; defining a journey
origin and final destination

These two inputs should be changed in the separate input file and read into this script

Yazad Sukhia
Feb 2022
"""

import requests

def main():
       response = initialise_api_data()
       print(response.text)
       journey_start = journey_origin()
       journey_end = journey_destination()
       time_minutes = journey_time()
       print("Journey from", journey_start, "to", journey_end, "will take", time_minutes, "minutes")
       ttime_minutes = journey_time_traffic()
       print("Journey from", journey_start, "to", journey_end, "will take", ttime_minutes, "minutes in traffic")
       distace_km = journey_distance()
       print("Journey from", journey_start, "to", journey_end, "will traverse", distace_km, "km")
       return

def journey_origin():
       journey_start = "Bristol, UK, BS8 2AB"  # This should be read from the input file
       return journey_start

def journey_destination():
       journey_end = "Bristol, UK, BS1 2NJ"  # This should be read from the input file
       return journey_end

def initialise_api_data():
       API_KEY = 'AIzaSyCsNLYOColvC8uLS7EeNMRi5nK1kr_KSp8'
       journey_start = journey_origin()
       journey_end = journey_destination()
       departure_time = 'now'
       traffic_model = 'pessimistic'
       url = ('https://maps.googleapis.com/maps/api/distancematrix/json'
              + '?language=en-US&units=imperial'
              + '&origins={}'
              + '&destinations={}'
              + '&key={}'
              + '&departure_time={}'
              + '&traffic_model={}'
              ).format(journey_start, journey_end, API_KEY, departure_time, traffic_model)
       payload = {}
       headers = {}
       response = requests.request("GET", url, headers=headers, data=payload)
       # print(response.text)
       return response

def journey_time():
       response = initialise_api_data()
       time_seconds = response.json()["rows"][0]["elements"][0]["duration"]["value"]
       time_minutes = round(time_seconds / 60, 2)
       return time_minutes

def journey_distance():
       response = initialise_api_data()
       distance_metres = response.json()["rows"][0]["elements"][0]["distance"]["value"]
       distance_km = round(distance_metres / 1000, 2)
       return distance_km

def journey_time_traffic():
       response = initialise_api_data()
       ttime_seconds = response.json()["rows"][0]["elements"][0]["duration_in_traffic"]["value"]
       ttime_minutes = round((ttime_seconds / 60), 2)
       return ttime_minutes

if __name__ == "__main__":
    main()