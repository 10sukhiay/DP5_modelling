import pandas as pd
import numpy as np
import os
import datetime
import matplotlib.pyplot as plt


def vrg(charge_duration, charge_schedule):
    charge_schedule.loc[: charge_schedule.index.min() + charge_duration, 'Charger_Instruction'] = 1
    return charge_schedule


def v1g(charge_duration, charge_schedule):
    v1g_charge_schedule = charge_schedule[charge_schedule['Charger_Instruction'] == 0].copy()
    # print(v1g_charge_schedule)
    v1g_charge_schedule.loc[:, 'Charger_Instruction'] = 2
    # print(v1g_charge_schedule)
    charge_schedule.loc[charge_schedule['Charger_Instruction'] == 0, :] = v1g_charge_schedule
    # print(charge_schedule)
    return charge_schedule


def calculate_SoC(charge_schedule, SoC_resolution):
    # print(charge_schedule)
    # print(charge_schedule['Charger_Instruction'])
    # print(charge_schedule['Charger_Instruction'].copy().cumsum()*SoC_resolution)
    cumsumSoC = charge_schedule['Charger_Instruction'].copy().cumsum() * SoC_resolution + charge_schedule.loc[charge_schedule.index.min(), 'SoC']
    charge_schedule.iloc[1:, charge_schedule.columns.get_indexer(['SoC'])] = cumsumSoC[:-1]
    # print(charge_schedule)
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
max_battery_cycles = 1500  # for TM3
battery_capacity = 54  # kWh
charger_efficiency = 1  # for charger
plug_in_SoC = 0.1

arrival_time = pd.to_datetime('2019-02-25 19:15:00')
departure_time = pd.to_datetime('2019-02-26 1:00:00')
time_resolution = pd.Timedelta('15 min')

vrg_charge_duration = pd.Timedelta('105 min')
v1g_charge_duration = pd.Timedelta('310 min')
# vrg_charging_intervals = vrg_charge_duration / time_resolution
v1g_charging_intervals = v1g_charge_duration / time_resolution
SoC_resolution = time_resolution / pd.Timedelta(str(battery_capacity / charge_rate) + 'h')

agile_extract = pd.read_excel(os.getcwd()[:-5] + 'Inputs\AgileExtract.xls', parse_dates=[0], index_col=0)
connection_extract = agile_extract[arrival_time: departure_time].resample(time_resolution).pad().iloc[:-1, :]

# print(connection_extract[connection_extract.index.min() : departure_time - pd.Timedelta('40 min')].sum())

# initial_connections_available = connection_extract.copy()
zeros_charge_schedule = connection_extract
zeros_charge_schedule['Charger_Instruction'] = 0
zeros_charge_schedule.loc[zeros_charge_schedule.index.min(), 'SoC'] = plug_in_SoC

vrg_charge_schedule = vrg(vrg_charge_duration,
                          zeros_charge_schedule)
#
# v1g_charge_schedule = v1g(vrg_charge_schedule,
#                           vrg_charge_schedule.copy())

test = calculate_SoC(vrg_charge_schedule, SoC_resolution)

print(test)
# print(vrg_charge_schedule)
# print(vrg_connections_available)
# print(v1g_charge_schedule)
# print(v1g_connections_available)
