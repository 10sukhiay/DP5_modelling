"""
Script contains function which enable links to the googlemaps API service, allowing the
distance and tie of a journey to be calculated based on two addresses; defining a journey
origin and final destination

These two inputs should be changed in the separate input file and read into this script

Yazad Sukhia
Feb 2022
"""

import requests
import pandas as pd

def main(inputs, reserve_journey):
       response = initialise_api_data(inputs, reserve_journey)
       print(response.text)
       journey_start = journey_origin(inputs)
       journey_end = journey_destination(inputs, reserve_journey)
       time_minutes = journey_time(inputs, reserve_journey)
       print("Journey from", journey_start, "to", journey_end, "will take", time_minutes, "minutes")
       ttime_minutes = journey_time_traffic(inputs, reserve_journey)
       print("Journey from", journey_start, "to", journey_end, "will take", ttime_minutes, "in traffic")
       distace_km = journey_distance(inputs, reserve_journey)
       print("Journey from", journey_start, "to", journey_end, "will traverse", distace_km, "km")
       return

def journey_origin(inputs):
       journey_start = inputs['Origin']  # This should be read from the input file
       return journey_start

def journey_destination(inputs,reserve_journey):
       if reserve_journey:
              journey_end = inputs['Reserve Destination']
       else:
              journey_end = inputs['Journey Destination']
       return journey_end

def initialise_api_data(inputs, reserve_journey):
       API_KEY = 'AIzaSyCsNLYOColvC8uLS7EeNMRi5nK1kr_KSp8'
       journey_start = journey_origin(inputs)
       journey_end = journey_destination(inputs, reserve_journey)
       departure_time = pd.to_datetime('2022-04-29 17:00:00')
       datum_time = pd.to_datetime('1970-01-01 00:00:00')
       one_s = pd.Timedelta("1 s")
       departure_time_s = int((departure_time - datum_time) / one_s)
       traffic_model = 'pessimistic'
       url = ('https://maps.googleapis.com/maps/api/distancematrix/json'
              + '?language=en-US&units=imperial'
              + '&origins={}'
              + '&destinations={}'
              + '&key={}'
              + '&departure_time={}'
              + '&traffic_model={}'
              ).format(journey_start, journey_end, API_KEY, departure_time_s, traffic_model)
       payload = {}
       headers = {}
       response = requests.request("GET", url, headers=headers, data=payload)
       # print(response.text)
       return response

def journey_time(inputs, reserve_journey):
       response = initialise_api_data(inputs, reserve_journey)
       time_seconds = response.json()["rows"][0]["elements"][0]["duration"]["value"]
       time_minutes = round(time_seconds / 60, 2)
       return time_minutes

def journey_distance(inputs, reserve_journey):
       response = initialise_api_data(inputs, reserve_journey)
       distance_metres = response.json()["rows"][0]["elements"][0]["distance"]["value"]
       distance_km = round(distance_metres / 1000, 2)
       return distance_km

def journey_time_traffic(inputs, reserve_journey):
       response = initialise_api_data(inputs, reserve_journey)
       ttime = pd.Timedelta(str(response.json()["rows"][0]["elements"][0]["duration_in_traffic"]["value"]) + 's')
       # ttime_minutes = round((ttime_seconds / 60), 2)
       return ttime

if __name__ == "__main__":
    main()