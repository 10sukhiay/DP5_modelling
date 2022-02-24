"""
Calculates the necessary charge requirement to complete a specified journey
Each journey is defined by characteristics which are variable in Inputs_Journey file

Yazad Sukhia
Feb 2022
"""

# import required packages for use
import pandas as pd
import Inputs_Journey_v2 as inp
import API_tests as API
import os
# import numpy as np
# import matplotlib as plt

# temp = TempData.index.get_loc(nearest_time, method='nearest')
# print(temp)

# test_yaz = journey.main(inputs_table.loc[1, :])
# print(test_yaz)

def main(inputs, reserve_journey):
    results_journey(inputs, reserve_journey)
    charge_time = time_charge(inputs, reserve_journey)
    # print(charge_time)
    # display_results() # this is added after display_results() has been formed
    return charge_time

# Defines the relationship between ambient temperature and range
"""Ambient temperature selection can be made in the Inputs_Journey file """
def temp(inputs, reserve_journey):
    plug_out_time = plug_out(inputs, reserve_journey)
    TempData = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Temp1.xls', parse_dates=[0], index_col=0)
    temp = TempData[plug_out_time.replace(year=2019):plug_out_time.replace(year=2019) + pd.Timedelta('1 h')].copy().iloc[0,0]
    # temp = inputs['Temperature']
    if temp < 23:
        temp_effect = (1-((23-temp) * 0.0033))
    else:
        temp_effect = 1
    return temp_effect

def plug_out(inputs, reserve_journey):
    destination_arrival_time = pd.to_datetime(inputs['Destination Arrival Time'])
    plug_out_time = destination_arrival_time - API.journey_time_traffic(inputs, reserve_journey)
    return plug_out_time

# Defines the inital estimated amount of charge required for the selected EV type to move 1km
def charge_p_range(inputs):
    charge_per_range = float(inputs['Battery Capacity']) / float(inputs['Vehicle Range'])
    return charge_per_range

# Calculates the intial charge requirement to complete the specified journey input
def init_charge(inputs, reserve_journey):
    trip_distance = API.journey_distance(inputs, reserve_journey)
    charge_per_range = charge_p_range(inputs)
    capacity = inputs['Battery Capacity']
    init_charge_req = ((charge_per_range * trip_distance)/ capacity) * 100
    return init_charge_req

# Calculates the new charge requirement after the influence of external variables has been considered
def shift_charge(inputs, reserve_journey):
    temp_effect = temp(inputs, reserve_journey)
    range_shift = (temp_effect * inputs['Rain'] * inputs['Heating'] * inputs['Cooling'] * inputs['Driving Style'] * inputs['Regen Braking'])
    # print(inp.rain[1])
    # print(inp.heating[0])
    # print(inp.cooling[0])
    # print(inp.style[0])
    # print(inp.regen[1])
    apply_r_shift = (1/range_shift)
    init_charge_req = init_charge(inputs, reserve_journey)
    shift_charge_req = init_charge_req * apply_r_shift
    return shift_charge_req

# Calculates the additional energy required to complete a journey based on elevation change
"""Changes in elevation over journey covered selection can be made in the Inputs_Journey file """
def charge_add(inputs):
    delta_h = inputs['Distance up'] - inputs['Distance down']  # This can be read from the input excel file eventually
    capacity = inputs['Battery Capacity']
    mass = inputs['Vehicle Mass']
    if delta_h > 0:
        energy_J = delta_h * mass * 9.81
        energy_kWh = energy_J / 3600000
        add_charge = ((energy_kWh / capacity) * 100)
    else:
        add_charge = 0
    return add_charge

# Calculates the final charge requirement (as a %) with the additional elevation
def final_charge(inputs, reserve_journey):
    shift_charge_req = shift_charge(inputs, reserve_journey)
    add_charge = charge_add(inputs)
    charge_final = shift_charge_req + add_charge
    return charge_final

def final_kwh(inputs, reserve_journey):
    final_charge_percent = final_charge(inputs, reserve_journey)
    final_charge_kWh = (final_charge_percent / 100) * inputs['Battery Capacity']
    return final_charge_kWh

def time_charge(inputs, reserve_journey):
    final_charge_kWh = final_kwh(inputs, reserve_journey)
    charge_time = pd.Timedelta(str(final_charge_kWh / inputs['Charge Rate']) + 'h')
    return charge_time

def results_journey(inputs, reserve_journey):
    final_charge_percent = round(final_charge(inputs, reserve_journey), 2)
    print(final_charge_percent, "% of total capacity required to charge")
    final_charge_kWh = round((final_charge_percent / 100) * inputs['Battery Capacity'], 2)
    print("This is equivalent to", final_charge_kWh, "kWh")
    charge_time = round(final_charge_kWh / inputs['Charge Rate'], 2)
    print("Therefore", charge_time, "hours are needed to charge to requirement using a", inputs['Charge Rate'], "kW charger")
    pounds_saved = joruney_savings(inputs, reserve_journey)
    print('£', pounds_saved, 'on this journey saved with this EV selection')
    return

def journey_cost(inputs, reserve_journey):
    journey_price = 0
    vehicle_select = inputs['Vehicle Type']
    petrol_cost = inputs['p per litre']
    l_per_km = (2.35215 / inputs['MPG'])
    petrol_consump_rate = l_per_km
    elec_cost = inp.kwh_cost
    if vehicle_select == 1 or vehicle_select == 2:
        final_charge_kWh = final_kwh(inputs, reserve_journey)
        journey_price = final_charge_kWh * elec_cost
    elif vehicle_select == 3:
        petrol_p_per_km = petrol_consump_rate * petrol_cost
        journey_price = API.journey_distance(inputs, reserve_journey) * petrol_p_per_km
    return journey_price

def joruney_savings(inputs, reserve_journey):
    l_per_km = (2.35215 / inputs['MPG'])
    petrol_consump_rate = l_per_km
    petrol_cost = inputs['p per litre']
    trip_cost = journey_cost(inputs, reserve_journey)
    petrol_p_per_km = petrol_consump_rate * petrol_cost
    journey_petrol_price = API.journey_distance(inputs, reserve_journey) * petrol_p_per_km
    trip_savings = round(((journey_petrol_price - trip_cost) / 100), 2)
    return trip_savings

def petrol_cost(inputs, reserve_journey):
    l_per_km = (2.35215 / inputs['MPG'])
    petrol_consump_rate = l_per_km # in litres per km
    petrol_cost = inputs['p per litre']
    petrol_p_per_km = petrol_consump_rate * petrol_cost
    journey_petrol_price = API.journey_distance(inputs, reserve_journey) * petrol_p_per_km
    return journey_petrol_price

# def display_results():
# TO COMPLETE LATER- USE WHEN DISPLAYING RESULTS FOR INDIVIDUAL SECTION

if __name__ == "__main__":
    main()

