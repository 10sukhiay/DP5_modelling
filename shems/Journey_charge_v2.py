"""
Calculates the necessary charge requirement to complete a specified journey
Each journey is defined by characteristics which are variable in Inputs_Journey file

Yazad Sukhia
Feb 2022
"""

# import required packages for use
import Inputs_Journey_v2 as inp
# import pandas as pd
# import numpy as np
# import matplotlib as plt

def main():
    final_charge_percent = final_charge(inp, shift_charge, charge_add)
    print(final_charge_percent, "% of total capacity required to charge")
    final_charge_kWh = (final_charge_percent / 100) * inp.capacity[1]
    print("This is equivalent to", final_charge_kWh, "kWh")
    charge_time = final_charge_kWh / inp.charge_rate
    print("Therefore", charge_time, "hours are needed to charge to requirement")
    return final_charge_percent, final_charge_kWh, charge_time

# Defines the relationship between ambient temperature and range
"""Ambient temperature selection can be made in the Inputs_Journey file """
def temp(inp):
    temp = inp.temp # This can be read from the input excel file eventually
    if temp < 23:
        temp_effect = (1-((23-temp) * 0.0033))
    else:
        temp_effect = 1
    return temp_effect

# Defines the inital estimated amount of charge required for the selected EV type to move 1km
def charge_p_range(inp):
    charge_per_range = float(inp.capacity[1]) / float(inp.v_range[1])
    return charge_per_range

# Calculates the intial charge requirement to complete the specified journey input
def init_charge(inp, charge_p_range):
    trip_distance = inp.distance
    charge_per_range = charge_p_range(inp)
    capacity = inp.capacity[1]
    init_charge_req = ((charge_per_range * trip_distance)/ capacity) * 100
    return init_charge_req

# Calculates the new charge requirement after the influence of external variables has been considered
def shift_charge(inp, init_charge):
    temp_effect = temp(inp)
    range_shift = (temp_effect * inp.rain[1] * inp.heating[0] * inp.cooling[0] * inp.style[0] * inp.regen[1])
    # print(inp.rain[1])
    # print(inp.heating[0])
    # print(inp.cooling[0])
    # print(inp.style[0])
    # print(inp.regen[1])
    apply_r_shift = (1/range_shift)
    init_charge_req = init_charge(inp, charge_p_range)
    shift_charge_req = init_charge_req * apply_r_shift
    return shift_charge_req

# Calculates the additional energy required to complete a journey based on elevation change
"""Changes in elevation over journey covered selection can be made in the Inputs_Journey file """
def charge_add(inp):
    delta_h = inp.dist_up - inp.dist_down # This can be read from the input excel file eventually
    capacity = inp.capacity[1]
    mass = inp.mass[1]
    if delta_h > 0:
        energy_J = delta_h * mass * 9.81
        energy_kWh = energy_J / 3600000
        add_charge = ((energy_kWh / capacity) * 100)
    else:
        add_charge = 0
    return add_charge

def final_charge(inp, shift_charge, charge_add):
    shift_charge_req = shift_charge(inp, init_charge)
    add_charge = charge_add(inp)
    charge_final = shift_charge_req + add_charge
    return charge_final

if __name__ == "__main__":
    main()

