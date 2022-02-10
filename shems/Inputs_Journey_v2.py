"""
Contains inputs needed to work out charge demand requirment for an EV

Yazad Sukhia
Feb 2022
"""
import pandas as pd

# initialising data files
Temp_2019 = pd.read_csv('temp_data_2019.csv')  # Temperature Data
Journey = pd.read_csv('Sample_Week_Trip.csv')  # Journey Data
# print Temp_2019
print(Journey)

distance = 130
charge_rate = 7.4  # kW [THIS IS AN EXAMPLE- VALUE SHOULD BE PROVIDED BY ADAM'S CODE]

# Temperature
temp = 9  # celcius

# vehicle = 1
# # Vehicle 1 - Tesla Model 3
# r_v1 = 355 # km
# c_v1 = 55 # kWh
# m_v1 = 1684 # kg
#
# # Vehicle 2 - Nissan Leaf
# r_v2 = 240 # km
# c_v2 = 40 # kWh
# m_v2 = 1580 # kg

# Vehicle Characteristics
v_range = [355, 240]  # km
capacity = [55, 40]  # kWh
mass = [1684, 1580]  # kg

# Precipitation
"""Rain severity increases: none, light, mild, heavy; index in Journey_charge_v2 as 0, 1, 2, 3"""
rain = [1, 0.91, 0.89, 0.85]  # This can be read from input excel file eventually
# rain_none = 1
# rain_light = 0.91
# rain_mild = 0.89
# rain_heavy = 0.85

# Heating
"""Heating is set as ON or OFF, index in Journey_charge_v2 as 0, 1"""
heating = [0.85, 1]  # This can be read from input excel file eventually
# heating_on = 0.85
# heating_off = 1

# Cooling
"""Cooling is set as ON or OFF, index in Journey_charge_v2 as 0, 1"""
cooling = [0.83, 1]  # This can be read from input excel file eventually
# cooling_on = 0.83
# cooling_off = 1

# Driving Style
"""Driving style is set as EFFICIENT, MODERATE, AGGRESSIVE, index in Journey_charge_v2 as 0, 1, 2"""
style = [1, 0.84, 0.67]
# ds_efficient = 1
# ds_moderate = 0.84
# ds_aggressive = 0.67

# Regen
"""Regenerative Braking is set as ON or OFF, index in Journey_charge_v2 as 0, 1"""
regen = [1.28, 1]
# regen_on = 1.28
# regen_off = 1

# Elevation change
dist_up = 150
dist_down = 50