"""
Calculates the necessary charge requirement to complete a specified journey
Each journey is defined by characteristics which are variable in Inputs_Journey file

Yazad Sukhia
Feb 2022
"""

import time
import pandas as pd
import Inputs_Journey_v2 as inp
import API_tests as API
import os


# test change
# import matplotlib as plt


def main():
    start_time = time.time()
    inputs = pd.read_excel('../Inputs/Yaz_Journey_API_inputs_data.xlsx').iloc[0, :]
    mpg_temp_shift(inputs, False)
    results_journey(inputs, False)
    charge_time = time_charge(inputs, False)
    print(charge_time)
    distance_km = API.journey_distance
    print(distance_km)
    traffic_time = API.journey_time_traffic
    print(traffic_time)
    # display_results()  # this is to be added after display_results() has been formed to graph results
    end_time = time.time()
    print('Completed in {:.4f} seconds'.format(end_time - start_time))
    return charge_time


"""
The following functions are developed specifically to calculate values called by the charge controller that inform 
elements of the charging logic. Individual functions contain descriptions of functionality; while below a brief outline 
of how charging logic is affected by the calculated values is explained 
 
    plug_out        --- defines the time at which the controller must charge to the calculated energy requirement for 
                        each specified journey  
    time_charge     --- defines the minimum amount of time that must be spent charging in order to charge to the 
                        required level for each specified journey 
"""


def plug_out(inputs, reserve_journey):
    """Calculates when the charge controller must stop charging by. This is an estimated plug out time based on the user
    input desired time to arrive at their specified travel destination and the API estimated time for this journey to be
    completed"""
    destination_arrival_time = pd.to_datetime(inputs['Destination Arrival Time'])
    plug_out_time = destination_arrival_time - API.journey_time_traffic(inputs, reserve_journey)
    return plug_out_time


def time_charge(inputs, reserve_journey):
    """Calculates the time that will be needed to charge to the required level for each specified journey, based on the
    required charge calculation and the charge rate of the controller used (outlined in the user inputs)"""
    final_charge_kwh = final_kwh(inputs, reserve_journey)
    charge_time = pd.Timedelta(str(final_charge_kwh / inputs['Charge Rate']) + 'h')
    return charge_time


"""
The following functions are developed to work out the individual effect a range of specified journey characteristics 
have on the total charge requirement of an EV. The effects of defined journey characteristics are variable based 
broadly on two main categories 

    personal variation between users    --- includes the use of HVAC (Heating, Ventilation, Air Conditioning) systems 
                                            driving style (EFFICIENT, MODERATE, AGGRESSIVE)
                                            the use of regenerative braking systems                              
    external environment                --- includes external factors such as weather conditions (precipitation) and 
                                            temperature variation between different journeys 

While personal variation between users is either set up through the input file or as an inferred effect of the external
environment [e.g. HVAC use is dependant on how hot / cold it is outside], the state of the external environment is 
provided by historical data and is read based on a user input for date of journey. Data sources are as follows 
    
    Precipitation                        --- https://www.metoffice.gov.uk/hadobs/hadukp/data/download.html
                                             Met Office Data 
    External Temperature                 --- https://re.jrc.ec.europa.eu/pvg_tools/en/#HR
                                             EU Science Hub Data- Photovoltaic Geographical Information System (PVGIS)
"""


def heating(inputs, reserve_journey):
    """Calculates relative effect that use of heating systems will have on charge requirement. Use of heating is set at
    a threshold level and is assumed to be "ON" when external temperature is below 7°C. This can be changed by adapting
    the IFS conditional statement in the 'Inputs/HomeGen/Temp1.xls' file. Uses input plug_out_time to find external
    temperature at the time of journey"""
    plug_out_time = plug_out(inputs, reserve_journey)
    td = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Temp1.xls', parse_dates=[0], index_col=0)
    heat = td[plug_out_time.replace(year=2019):plug_out_time.replace(year=2019) + pd.Timedelta('1 h')].copy().iloc[0, 1]

    if heat == "ON":
        heat_effect = 0.85
    else:
        heat_effect = 1

    return heat_effect


def cooling(inputs, reserve_journey):
    """Calculates relative effect that use of cooling systems will have on charge requirement. Use of cooling is set at
    a threshold level and is assumed to be "ON" when external temperature is above 20°C. This can be changed by adapting
    the IFS conditional statement in the 'Inputs/HomeGen/Temp1.xls' file. Uses input plug_out_time to find external
    temperature at the time of journey"""
    plug_out_time = plug_out(inputs, reserve_journey)
    td = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Temp1.xls', parse_dates=[0], index_col=0)
    cool = td[plug_out_time.replace(year=2019):plug_out_time.replace(year=2019) + pd.Timedelta('1 h')].copy().iloc[0, 2]

    if cool == "ON":
        cool_effect = 0.83
    else:
        cool_effect = 1

    return cool_effect


def rain(inputs, reserve_journey):
    """Calculates relative effect that levels of precipitation will have on charge requirement. Uses input plug_out_time
    to find precipitation level at the time of journey. Severity is classified in banded groups ranging from NONE,
    LIGHT, MILD, HEAVY"""
    plug_out_time = plug_out(inputs, reserve_journey)
    precipdata = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Precipitation_data_uk_2019.xlsx', parse_dates=[0],
                               index_col=0)
    rain_effect = precipdata[
            plug_out_time.replace(year=2019):plug_out_time.replace(year=2019) + pd.Timedelta('1 day')].copy().iloc[0, 1]
    return rain_effect


def temp(inputs, reserve_journey):
    """Calculates relative effect that the external ambient temperature will have on charge requirement. Uses input
    plug_out_time to find temperature level at the time of journey"""
    plug_out_time = plug_out(inputs, reserve_journey)
    td = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Temp1.xls', parse_dates=[0], index_col=0)
    temperature = \
        td[plug_out_time.replace(year=2019):plug_out_time.replace(year=2019) + pd.Timedelta('1 h')].copy().iloc[0, 0]
    # temp = TempData[plug_out_time:plug_out_time + pd.Timedelta('1 h')].copy().iloc[0, 0]
    # temp = inputs['Temperature']

    if temperature < 23:
        temp_effect = (1 - ((23 - temperature) * 0.0033))
    else:
        temp_effect = 1

    return temp_effect


def range_traffic_shift(inputs, reserve_journey):
    """Assigns a shifted range value to an EV completing the journey specified based on traffic conditions."""
    journey_vel = avg_journey_vel(inputs, reserve_journey)

    if journey_vel <= 50:
        traffic_effect = (1 - ((50 - journey_vel) * 0.0023))  # quantifies reduction in effective range below 50km/h
    elif journey_vel >= 80:
        traffic_effect = (1 - ((journey_vel - 80) * 0.000415))  # quantifies reduction in effective range above 80 km/h
    else:
        traffic_effect = 1  # assumes EV optimal operating range is between 50-80km/h

    return traffic_effect


"""
The following functions are developed to work out the amount of charge that a user-specified journey will require to 
complete. Trip distance is calculated by a google maps API called from the API_tests script and requires an input origin
and destination, while EV characteristics are initially set by manufacture specifications
"""


def charge_p_range(inputs):
    """Defines the initial estimated amount of charge required for the selected EV type to move 1km. This is calculated
    directly from manufacture quoted vehicle characteristics"""
    charge_per_range = float(inputs['Battery Capacity']) / float(inputs['Vehicle Range'])
    return charge_per_range


def init_charge(inputs, reserve_journey):
    """Calculates the initial charge required to complete the specified journey input"""
    trip_distance = API.journey_distance(inputs, reserve_journey)
    charge_per_range = charge_p_range(inputs)
    capacity = inputs['Battery Capacity']
    init_charge_req = ((charge_per_range * trip_distance) / capacity) * 100
    return init_charge_req


def shift_charge(inputs, reserve_journey):
    """Calculates a shifted charge requirement based on the calculated effects of individual journey characteristics"""
    heat_effect = heating(inputs, reserve_journey)
    cool_effect = cooling(inputs, reserve_journey)
    rain_effect = rain(inputs, reserve_journey)
    temp_effect = temp(inputs, reserve_journey)
    traffic_effect = range_traffic_shift(inputs, reserve_journey)
    range_shift = (heat_effect * cool_effect * inputs['Driving Style'] * inputs["Regen Braking"]
                   * rain_effect * temp_effect * traffic_effect)
    # print(inp.rain[1])
    # print(inp.heating[0])
    # print(inp.cooling[0])
    # print(inp.style[0])
    # print(inp.regen[1])
    apply_r_shift = (1 / range_shift)
    init_charge_req = init_charge(inputs, reserve_journey)
    shift_charge_req = init_charge_req * apply_r_shift
    return shift_charge_req


def charge_add(inputs):
    """Calculates an additional energy requirement to complete a journey based on elevation change along the journey"""
    delta_h = inputs['Distance up'] - inputs['Distance down']  # This can be read from the input excel file eventually
    capacity = inputs['Battery Capacity']
    mass = inputs['Vehicle Mass']

    if delta_h > 0:
        energy_j = delta_h * mass * 9.81
        energy_kwh = energy_j / 3600000
        add_charge = ((energy_kwh / capacity) * 100)
    else:
        add_charge = 0

    return add_charge


"""
The following functions are developed to call the group of functions above (or combinations of the functions above that 
lead to useful outputs) and so simplify any requests the charge controller makes for the energy requirement of a journey
"""


def final_charge(inputs, reserve_journey):
    """Calculates the total energy requirement for a given EV journey based on defined journey characteristics as a % of
    the total battery capacity of the vehicle"""
    shift_charge_req = shift_charge(inputs, reserve_journey)
    add_charge = charge_add(inputs)
    charge_final = shift_charge_req + add_charge
    return charge_final


def final_kwh(inputs, reserve_journey):
    """Converts the final charge requirement calculated in final_charge from a percentage into a kWh requirement"""
    final_charge_percent = final_charge(inputs, reserve_journey)
    final_charge_kwh = (final_charge_percent / 100) * inputs['Battery Capacity']
    return final_charge_kwh


def results_journey(inputs, reserve_journey):
    """Presents and prints the final results in the terminal"""
    final_charge_percent = round(final_charge(inputs, reserve_journey), 2)
    print(final_charge_percent, "% of total capacity required to charge")
    final_charge_kwh = round((final_charge_percent / 100) * inputs['Battery Capacity'], 2)
    print("This is equivalent to", final_charge_kwh, "kWh")
    charge_time = round(final_charge_kwh / inputs['Charge Rate'], 2)
    print("Therefore", charge_time, "hours are needed to charge to requirement using a", inputs['Charge Rate'],
          "kW charger")
    pounds_saved = journey_savings(inputs, reserve_journey)
    print('£', pounds_saved, 'on this journey saved with this EV selection')
    return


"""
The following functions are developed to work out the effect of journey characteristics on ICE fuel efficiency. The main
contributing factors are external ambient temperature and traffic conditions along the journey route. Traffic conditions
are evaluated using a GoogleMaps API called from the API_tests script and require an input origin and destination  
"""


def avg_journey_vel(inputs, reserve_journey):
    """Defines the average velocity [in km/h] of travel during the journey. This takes 'optimistic' traffic mode
    estimations (i.e considering the least amount of traffic as possible) and assumes that the vehicle is moving for a
    specified % of this time, as per the moving_ratio- the rest of the time is assumed to be stopped at lights/
    intersections"""
    journey_dist_km = API.journey_distance(inputs, reserve_journey)
    journey_time_opt_hours = round((API.journey_time_optimist(inputs, reserve_journey) / 60), 2)
    moving_ratio = 0.95  # This should really be read from inputs file as is specific to each defined journey
    journey_avg_vel = journey_dist_km / (journey_time_opt_hours * moving_ratio)
    return journey_avg_vel


def trip_length_band(inputs, reserve_journey):
    """Defines if the trip considered is a 'short' or 'long' trip; short trips are considered under 4 miles"""
    short_trip_cutoff = 4 * 1.609  # converts 4 miles into km, below this value is defined as a short trip
    distance_km = API.journey_distance(inputs, reserve_journey)

    if distance_km <= short_trip_cutoff:
        short_trip = 'True'
    else:
        short_trip = 'False'

    return short_trip


def mpg_traffic_shift(inputs, reserve_journey):
    """Assigns a shifted fuel efficiency to an ICE completing the journey specified based on traffic conditions."""
    journey_vel = avg_journey_vel(inputs, reserve_journey)

    if journey_vel <= 60:
        mpg_traffic_effect = (1 - ((60 - journey_vel) * 0.0085))  # quantifies reduction in effective mpg below 60km/h
    elif journey_vel >= 70:
        mpg_traffic_effect = (1 - ((journey_vel - 70) * 0.00031))  # quantifies reduction in effective mpg above 70km/h
    else:
        mpg_traffic_effect = 1  # assumes EV optimal operating range is between 60-70km/h

    return mpg_traffic_effect


def mpg_temp_shift(inputs, reserve_journey):
    """Assigns a shifted fuel efficiency to an ICE completing the journey specified based on external ambient
    temperature. Short trips in colder ambient temperatures have a greater fuel efficiency reduction due to the
    percentage time of the journey required to heat up the engine to optimal operating temperature"""
    plug_out_time = plug_out(inputs, reserve_journey)
    td = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Temp1.xls', parse_dates=[0], index_col=0)
    mpg_temperature = \
        td[plug_out_time.replace(year=2019):plug_out_time.replace(year=2019) + pd.Timedelta('1 h')].copy().iloc[0, 0]
    # mpg_temp = TempData[plug_out_time:plug_out_time + pd.Timedelta('1 h')].copy().iloc[0, 0]
    # mpg_temp = inputs['Temperature']
    short_trips = trip_length_band(inputs, reserve_journey)

    if short_trips == 'False':
        mpg_temp_effect = (1 - ((21.1 - mpg_temperature) * 0.0045))
    else:
        mpg_temp_effect = (1 - ((21.1 - mpg_temperature) * 0.0072))

    return mpg_temp_effect


def mpg_ice(inputs, reserve_journey):
    """Calculates a shifted fuel efficiency based on the calculated effects of individual journey characteristics"""
    initial_mpg = inputs['MPG']
    temp_effect_mpg = mpg_temp_shift(inputs, reserve_journey)
    traffic_effect_mpg = mpg_traffic_shift(inputs, reserve_journey)
    shifted_mpg = initial_mpg * temp_effect_mpg * inputs['Driving Style'] * traffic_effect_mpg
    return shifted_mpg


"""
The following functions are developed to evaluate the cost of individual journeys in terms of both:

    Financial Cost (£)          ---   
    Carbon Cost (Kg Co2)        ---  
    
Petrol cost data throughout is sourced from         --- https://www.gov.uk/government/statistics/weekly-road-fuel-prices
"""


def petrol_cost(inputs, reserve_journey):
    """Determines what the cost of fuel would be for the duration of the specified journey assuming an ICE is used"""
    plug_out_time = plug_out(inputs, reserve_journey)
    petrol_price_data = pd.read_excel(os.getcwd()[:-5] + 'Inputs/2019_data_petrol_price.xlsx', parse_dates=[0],
                                      index_col=0)
    p_per_litre = petrol_price_data[
                  plug_out_time.replace(year=2019):plug_out_time.replace(year=2019) + pd.Timedelta(days=7)
                  ].copy().iloc[0, 1]
    mpg = mpg_ice(inputs, reserve_journey)
    l_per_km = (2.35215 / mpg)  # in litres per km
    petrol_consump_rate = l_per_km
    petrol_costs = p_per_litre  # CAN USE inputs['p per litre'] INSTEAD FROM INPUT FILE
    petrol_p_per_km = petrol_consump_rate * petrol_costs
    journey_petrol_price = API.journey_distance(inputs, reserve_journey) * petrol_p_per_km
    return journey_petrol_price


def journey_carbon_cost(inputs, reserve_journey):
    """Determines the Co2 used (in kg) during the specified journey based on the mass of fuel required to complete the
    journey assuming an ICE is used"""
    mpg = mpg_ice(inputs, reserve_journey)
    l_per_km = (2.35215 / mpg)  # in litres per km
    petrol_consump_rate = l_per_km
    kg_carbon_per_litre = inputs['Carbon Kg per litre Fuel']
    petrol_co2_per_km = petrol_consump_rate * kg_carbon_per_litre
    journey_co2_price = round(API.journey_distance(inputs, reserve_journey) * petrol_co2_per_km, 2)
    return journey_co2_price


def journey_cost(inputs, reserve_journey):
    """Determines the cost of any journey specified; toggles between vehicle selections; where vehicle_select = 1 & 2
    refers to EVs while = 3 refers to the use of an ICE"""
    journey_price = 0
    vehicle_select = inputs['Vehicle Type']
    petrol_costs = inputs['p per litre']
    mpg = mpg_ice(inputs, reserve_journey)
    l_per_km = (2.35215 / mpg)
    petrol_consump_rate = l_per_km
    elec_cost = inp.kwh_cost

    if vehicle_select == 1 or vehicle_select == 2:
        final_charge_kwh = final_kwh(inputs, reserve_journey)
        journey_price = final_charge_kwh * elec_cost
    elif vehicle_select == 3:
        petrol_p_per_km = petrol_consump_rate * petrol_costs
        journey_price = API.journey_distance(inputs, reserve_journey) * petrol_p_per_km

    return journey_price


def journey_savings(inputs, reserve_journey):
    """Based on the vehicle selected, will calculate a potential cost saving between the selection and an ICE. In the
    case of an ICE being selected for the journey, savings will return £0."""
    trip_cost = journey_cost(inputs, reserve_journey)
    print('In an EV, this trip costs £', (round((trip_cost / 100), 2)))
    journey_petrol_price = petrol_cost(inputs, reserve_journey)
    print('In an ICE, this trip costs £', (round((journey_petrol_price / 100), 2)))
    trip_savings = round(((journey_petrol_price - trip_cost) / 100), 2)
    return trip_savings


# def display_results():
# TO COMPLETE LATER- USE WHEN DISPLAYING RESULTS FOR INDIVIDUAL SECTION


if __name__ == "__main__":
    main()
