import pandas as pd
import numpy as np
import os
import datetime
import matplotlib.pyplot as plt


def vrg(charge_schedule):
    charge_schedule.loc[: charge_schedule.index.min() + vrg_charge_duration, 'Charger_Instruction'] = 1
    return charge_schedule


def v1g(charge_schedule):
    while charge_schedule['Charger_Instruction'].sum() * time_resolution <= v1g_charge_duration + vrg_charge_duration:
        calculate_soc(charge_schedule)
        virtual_cost(charge_schedule)
        working_charge_schedule = charge_schedule[charge_schedule['Charger_Instruction'] == 0]
        charge_schedule.loc[working_charge_schedule['Virtual_Cost'].idxmin(), 'Charger_Instruction'] = 1
        test = 1
    return charge_schedule


def calculate_soc(charge_schedule):
    cumsum_soc = charge_schedule['Charger_Instruction'].copy().cumsum() * SoC_resolution + \
                 charge_schedule.loc[charge_schedule.index.min(), 'SoC']
    charge_schedule.iloc[1:, charge_schedule.columns.get_indexer(['SoC'])] = cumsum_soc[:-1]
    return charge_schedule


def virtual_cost(charge_schedule, charger_type='V1G'):
    if charger_type == 'V1G':
        charge_schedule['Soc_From_15'] = calculate_soc(charge_schedule)['SoC'] / 3 + 0.30 # to delete
        soc_from_15 = calculate_soc(charge_schedule)['SoC'] / 3 + 0.30
        charge_schedule['charge_held_fraction'] = (departure_time - charge_schedule.index.to_series()) / \
                               (departure_time - arrival_time)
        charge_held_fraction = (departure_time - charge_schedule.index.to_series()) / \
                               (departure_time - arrival_time)
        charge_schedule['Calendar_Ageing'] = cycle_cost_fraction / (1 - soc_from_15 * charge_held_fraction)
        beta = 0

    charge_schedule['Virtual_Cost'] = charge_schedule['Price'] * kWh_resolution / charger_efficiency + \
                                      charge_schedule['Calendar_Ageing'] + beta

    return charge_schedule


# def v1g(charging_intervals, charge_schedule):
#     preloaded_charge = charge_schedule['Charger_Instruction'].sum()
#     while charge_schedule['Charger_Instruction'].sum() < preloaded_charge + charging_intervals:
#         time_to_charge = connections_available['Price'].idxmin()
#         charge_schedule.loc[time_to_charge, 'Charger_Instruction'] = 1
#         connections_available.drop(time_to_charge, inplace=True)
#     return charge_schedule, connections_available


# def update_SoC(charge_schedule, time_resolution, charge_rate, at_time):

charge_rate = 7.4  # kW
max_battery_cycles = 1500 * 1  # for TM3, factored to account for factory rating including lifetime degradation 65/40
battery_capacity = 54  # kWh
charger_efficiency = 1  # for charger
plug_in_SoC = 0.15
battery_cost_per_kWh = 137e2

arrival_time = pd.to_datetime('2019-02-25 19:17:00')
departure_time = pd.to_datetime('2019-02-26 7:12:00')
time_resolution = pd.Timedelta('1 min')
kWh_resolution = charge_rate * time_resolution / pd.Timedelta('60 min')
cycle_cost_fraction = battery_cost_per_kWh * kWh_resolution / max_battery_cycles
SoC_resolution = cycle_cost_fraction * max_battery_cycles / battery_capacity / battery_cost_per_kWh

vrg_charge_duration = pd.Timedelta('40 min')
v1g_charge_duration = pd.Timedelta('300 min')
# vrg_charging_intervals = vrg_charge_duration / time_resolution
v1g_charging_intervals = v1g_charge_duration / time_resolution

agile_extract = pd.read_excel(os.getcwd()[:-5] + 'Inputs\AgileExtract.xls', parse_dates=[0], index_col=0)
connection_extract = agile_extract[arrival_time: departure_time].resample(time_resolution).pad().iloc[:-1, :]

# print(connection_extract[connection_extract.index.min() : departure_time - pd.Timedelta('40 min')].sum())

# initial_connections_available = connection_extract.copy()
zeros_charge_schedule = connection_extract
zeros_charge_schedule['Charger_Instruction'] = 0
zeros_charge_schedule.loc[zeros_charge_schedule.index.min(), 'SoC'] = plug_in_SoC

vrg_charge_schedule = vrg(zeros_charge_schedule)

v1g_charge_schedule = v1g(vrg_charge_schedule)

# test = calculate_soc(vrg_charge_schedule)

# test = virtual_cost(vrg_charge_schedule)

v1g_total_cost = (v1g_charge_schedule['Charger_Instruction'] * v1g_charge_schedule['Virtual_Cost']).sum()
v1g_charge_schedule['Wholesale_Cost'] = v1g_charge_schedule['Price'] * kWh_resolution
v1g_charge_schedule['Cost_Ratio'] = v1g_charge_schedule['Wholesale_Cost'] / v1g_charge_schedule['Virtual_Cost']

print(v1g_total_cost)

plt.subplot(411)
plt.plot(v1g_charge_schedule['Price'])
plt.subplot(412)
plt.plot(v1g_charge_schedule['Calendar_Ageing'])
plt.subplot(413)
plt.plot(v1g_charge_schedule['Virtual_Cost'])
plt.subplot(414)
plt.plot(v1g_charge_schedule['SoC'])
plt.show()

