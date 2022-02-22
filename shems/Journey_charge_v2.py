"""
Calculates the necessary charge requirement to complete a specified journey
Each journey is defined by characteristics which are variable in Inputs_Journey file

Yazad Sukhia
Feb 2022
"""

# import required packages for use
import Inputs_Journey_v2 as inp
import API_tests as API
# import pandas as pd
# import numpy as np
# import matplotlib as plt

def main():
    results_journey()
    charge_time = time_charge()
    # print(charge_time)
    # display_results() # this is added after display_results() has been formed
    return charge_time

# Defines the relationship between ambient temperature and range
"""Ambient temperature selection can be made in the Inputs_Journey file """
def temp():
    temp = inp.temp # This can be read from the input excel file eventually
    if temp < 23:
        temp_effect = (1-((23-temp) * 0.0033))
    else:
        temp_effect = 1
    return temp_effect

# Defines the inital estimated amount of charge required for the selected EV type to move 1km
def charge_p_range():
    charge_per_range = float(inp.capacity[0]) / float(inp.v_range[0])
    return charge_per_range

# Calculates the intial charge requirement to complete the specified journey input
def init_charge():
    trip_distance = API.journey_distance()
    charge_per_range = charge_p_range()
    capacity = inp.capacity[0]
    init_charge_req = ((charge_per_range * trip_distance)/ capacity) * 100
    return init_charge_req

# Calculates the new charge requirement after the influence of external variables has been considered
def shift_charge():
    temp_effect = temp()
    range_shift = (temp_effect * inp.rain[1] * inp.heating[0] * inp.cooling[0] * inp.style[0] * inp.regen[1])
    # print(inp.rain[1])
    # print(inp.heating[0])
    # print(inp.cooling[0])
    # print(inp.style[0])
    # print(inp.regen[1])
    apply_r_shift = (1/range_shift)
    init_charge_req = init_charge()
    shift_charge_req = init_charge_req * apply_r_shift
    return shift_charge_req

# Calculates the additional energy required to complete a journey based on elevation change
"""Changes in elevation over journey covered selection can be made in the Inputs_Journey file """
def charge_add():
    delta_h = inp.dist_up - inp.dist_down # This can be read from the input excel file eventually
    capacity = inp.capacity[0]
    mass = inp.mass[0]
    if delta_h > 0:
        energy_J = delta_h * mass * 9.81
        energy_kWh = energy_J / 3600000
        add_charge = ((energy_kWh / capacity) * 100)
    else:
        add_charge = 0
    return add_charge

# Calculates the final charge requirement (as a %) with the additional elevation
def final_charge():
    shift_charge_req = shift_charge()
    add_charge = charge_add()
    charge_final = shift_charge_req + add_charge
    return charge_final

def final_kwh():
    final_charge_percent = final_charge()
    final_charge_kWh = (final_charge_percent / 100) * inp.capacity[1]
    return final_charge_kWh

def time_charge():
    final_charge_kWh = final_kwh()
    charge_time = final_charge_kWh / inp.charge_rate
    return charge_time

def results_journey():
    final_charge_percent = round(final_charge(), 2)
    print(final_charge_percent, "% of total capacity required to charge")
    final_charge_kWh = round((final_charge_percent / 100) * inp.capacity[1], 2)
    print("This is equivalent to", final_charge_kWh, "kWh")
    charge_time = round(final_charge_kWh / inp.charge_rate, 2)
    print("Therefore",charge_time, "hours are needed to charge to requirement using a", inp.charge_rate, "kW charger")
    pounds_saved = joruney_savings()
    print('£', pounds_saved, 'on this journey saved with this EV selection')
    return

def journey_cost():
    journey_price = 0
    vehicle_select = inp.vehicle_type
    petrol_cost = inp.p_per_litre
    petrol_consump_rate = inp.l_per_km
    elec_cost = inp.kwh_cost
    if vehicle_select == 1 or vehicle_select == 2:
        final_charge_kWh = final_kwh()
        journey_price = final_charge_kWh * elec_cost
    elif vehicle_select == 3:
        petrol_p_per_km = petrol_consump_rate * petrol_cost
        journey_price = API.journey_distance() * petrol_p_per_km
    return journey_price

def joruney_savings():
    petrol_consump_rate = inp.l_per_km
    petrol_cost = inp.p_per_litre
    trip_cost = journey_cost()
    petrol_p_per_km = petrol_consump_rate * petrol_cost
    journey_petrol_price = API.journey_distance() * petrol_p_per_km
    trip_savings = round(((journey_petrol_price - trip_cost) / 100), 2)
    return trip_savings

def petrol_cost():
    petrol_consump_rate = inp.l_per_km # in litres per km
    petrol_cost = inp.p_per_litre
    petrol_p_per_km = petrol_consump_rate * petrol_cost
    journey_petrol_price = API.journey_distance() * petrol_p_per_km
    return journey_petrol_price

# def display_results():
# TO COMPLETE LATER- USE WHEN DISPLAYING RESULTS FOR INDIVIDUAL SECTION

if __name__ == "__main__":
    main()

