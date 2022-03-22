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


def main():
    inputs = pd.read_excel('../Inputs/Yaz_Journey_API_inputs_data.xlsx').iloc[0, :]
    # response = initialise_api_data(inputs, reserve_journey)
    # print(response.text)
    journey_start = journey_origin(inputs)
    journey_end = journey_destination(inputs, False)
    time_optimistic = journey_time_optimist(inputs, False)
    print("Journey from", journey_start, "to", journey_end, "will take", time_optimistic, "minutes optimistically")
    time_minutes = journey_time(inputs, False)
    print("Journey from", journey_start, "to", journey_end, "will take", time_minutes, "minutes")
    ttime_minutes = journey_time_traffic(inputs, False)
    print("Journey from", journey_start, "to", journey_end, "will take", ttime_minutes, "minutes in traffic")
    distance_km = journey_distance(inputs, False)
    print("Journey from", journey_start, "to", journey_end, "will traverse", distance_km, "km")
    return


"""
The following functions are called to initialise the journey profile, based on an initial origin and final destination. 
These locations are read from the developed Inputs Schedule and entered as an address/ postcode 
"""


def journey_origin(inputs):
    """Defines the journey origin- read from Inputs Schedule. This value should always be set to the Home Address"""
    journey_start = inputs['Origin']  # This should be read from the input file
    return journey_start


def journey_destination(inputs, reserve_journey):
    """Defines the journey destination- read from Inputs Schedule. The set destination toggles dependant on the journey
    definition as a reserve journey; TRUE or FALSE. The reserve journey is a set user input, a destination for which the
    charge controller always prioritises to charge to- an emergency destination such as the nearest hospital or the
    owners' child's school"""
    if reserve_journey:
        journey_end = inputs['Reserve Destination']
    else:
        journey_end = inputs['Journey Destination']
    return journey_end


"""
The following function is called to initialise the google maps API. 
The API key is specific to a single developer/ project; 
    https://console.cloud.google.com/home/dashboard?project=buoyant-silicon-340911&authuser=0&supportedpurview=project
The input departure time must be specified as an integer value in seconds after 1970-01-01 00:00:00 and must always be 
a specified time in the FUTURE 
Traffic mode if not specified assumes driving, while the traffic model used can be one of:
    optimistic 
    best _guess 
    pessimistic 
In order to ensure that the charge controller always charges up to the required charge level before the journey takes 
place, in the API initialisation the departure time is always set to a time near rush hour and the returned journey time
taken is calculated using a 'pessimistic' traffic model.  
"""


def initialise_api_data(inputs, reserve_journey):
    """Function is called whenever the API is required, establishes link between the script and the google maps API"""
    api_key = 'AIzaSyCsNLYOColvC8uLS7EeNMRi5nK1kr_KSp8'
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
           ).format(journey_start, journey_end, api_key, departure_time_s, traffic_model)
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    # print(response.text)
    return response


"""
The following functions are called by separate modules and summarise the use of the API in order to determine useful 
outputs
    Journey Distance                     --- Called by "Journey_charge_v2"; distance is used to calculate the charge 
                                             requirement for the journey 
    Journey Time                         --- Not called anymore; deemed too optimistic an estimate 
    Journey Time Traffic                 --- Called as a replacement to Journey Time; used to work out plug_out_time
                                             by subtracting the journey traffic time from the desired destination 
                                             arrival time  
"""


def journey_distance(inputs, reserve_journey):
    """"Uses the generated API response from the input journey to calculate and return the distance along the generated
     google maps driving route"""
    response = initialise_api_data(inputs, reserve_journey)
    distance_metres = response.json()["rows"][0]["elements"][0]["distance"]["value"]
    distance_km = round(distance_metres / 1000, 2)
    return distance_km


def journey_time(inputs, reserve_journey):
    """"Uses the generated API response from the input journey to calculate and return the time taken to travel along
    the generated google maps driving route discounting the inclusion of traffic along the route"""
    response = initialise_api_data(inputs, reserve_journey)
    time_seconds = response.json()["rows"][0]["elements"][0]["duration"]["value"]
    time_minutes = round(time_seconds / 60, 2)
    return time_minutes


def journey_time_traffic(inputs, reserve_journey):
    """"Uses the generated API response from the input journey to calculate and return the time taken to travel along
    the generated google maps driving route taking into consideration the inclusion of traffic along the route modelled
    either as optimistic, best_guess, or pessimistic as defined in the initialise_api_data function"""
    response = initialise_api_data(inputs, reserve_journey)
    traffic_time = pd.Timedelta(str(response.json()["rows"][0]["elements"][0]["duration_in_traffic"]["value"]) + 's')
    # traffic_time_minutes = round((traffic_time / 60), 2)
    return traffic_time


"""
The following functions are only to be used to calculate route optimistic travel times- they are not called by the 
charge controller and are specific to the traffic condition simulation under the journey module used in the caclulation 
in the shifted charge and mpg values for EVs and ICEs respectively 
"""


def initialise_api_data_optimistic(inputs, reserve_journey):  # Only to be used in the optimistic case
    """Function is called whenever the API is required, establishes link between the script and the google maps API"""
    api_key = 'AIzaSyCsNLYOColvC8uLS7EeNMRi5nK1kr_KSp8'
    journey_start = journey_origin(inputs)
    journey_end = journey_destination(inputs, reserve_journey)
    departure_time = pd.to_datetime('2022-04-29 17:00:00')
    datum_time = pd.to_datetime('1970-01-01 00:00:00')
    one_s = pd.Timedelta("1 s")
    departure_time_s = int((departure_time - datum_time) / one_s)
    traffic_model = 'optimistic'
    url = ('https://maps.googleapis.com/maps/api/distancematrix/json'
           + '?language=en-US&units=imperial'
           + '&origins={}'
           + '&destinations={}'
           + '&key={}'
           + '&departure_time={}'
           + '&traffic_model={}'
           ).format(journey_start, journey_end, api_key, departure_time_s, traffic_model)
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    # print(response.text)
    return response


def journey_time_optimist(inputs, reserve_journey):
    """"Uses the generated API response from the input journey to calculate and return the time taken to travel along
    the generated google maps driving route discounting the inclusion of traffic along the route"""
    response = initialise_api_data_optimistic(inputs, reserve_journey)
    time_seconds_opt = response.json()["rows"][0]["elements"][0]["duration"]["value"]
    time_minutes_opt = round(time_seconds_opt / 60, 2)
    return time_minutes_opt


if __name__ == "__main__":
    main()
