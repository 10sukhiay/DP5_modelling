"""
Contains

Yazad Sukhia
Feb 2022
"""


import requests

def main():
       response = initialise_API_data()
       print(response.text)
       journey_start = journey_origin()
       journey_end = journey_destination()
       time_minutes = journey_time()
       print("Journey from", journey_start, "to", journey_end, "will take", time_minutes, "minutes")
       distace_km = journey_distance()
       print("Journey from", journey_start, "to", journey_end, "will traverse", distace_km, "km")
       return

def journey_origin():
       journey_start = "Bristol, UK, BS8 2AB"
       return journey_start

def journey_destination():
       journey_end = "Bristol, UK, BS1 2NJ"
       return journey_end

def initialise_API_data():
       API_KEY = 'AIzaSyCsNLYOColvC8uLS7EeNMRi5nK1kr_KSp8'
       journey_start = journey_origin()
       journey_end = journey_destination()
       url = ('https://maps.googleapis.com/maps/api/distancematrix/json'
              + '?language=en-US&units=imperial'
              + '&origins={}'
              + '&destinations={}'
              + '&key={}'
              ).format(journey_start, journey_end, API_KEY)
       payload = {}
       headers = {}
       response = requests.request("GET", url, headers=headers, data=payload)
       # print(response.text)
       return response

def journey_time():
       response = initialise_API_data()
       time_seconds = response.json()["rows"][0]["elements"][0]["duration"]["value"]
       time_minutes = round(time_seconds / 60, 2)
       return time_minutes

def journey_distance():
       response = initialise_API_data()
       distance_metres = response.json()["rows"][0]["elements"][0]["distance"]["value"]
       distance_km = round(distance_metres / 1000, 2)
       return distance_km

# def journey_time_traffic():
#        response = initialise_API_data()
#

if __name__ == "__main__":
    main()

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