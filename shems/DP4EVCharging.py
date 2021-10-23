import pandas as pd
import numpy as np
import os
import datetime
import matplotlib.pyplot as plt


def vrg(charge_duration, charge_schedule):
    # print(charge_schedule.iloc[1,0])
    # print(charge_schedule.loc[: pd.to_datetime('2019-02-26 20:00:00'), 'Charge_Rate'])
    charge_schedule.loc[: charge_schedule.index.min() + charge_duration, 'Charge_Rate'] = 1
    # charge_schedule.iloc[0 : vrg_charging_intervals, 1] = 1
    # charge_schedule.first(vrg_charge_duration)['Charge_Rate'] = 1
    return charge_schedule


def v1g(charging_intervals, charge_schedule, connections_available):
    preloaded_charge = charge_schedule['Charge_Rate'].sum()
    while charge_schedule['Charge_Rate'].sum() < preloaded_charge + charging_intervals:
        time_to_charge = connections_available['Price'].idxmin()
        charge_schedule.loc[time_to_charge, 'Charge_Rate'] = 1
        connections_available.drop(time_to_charge, inplace=True)
    return charge_schedule, connections_available


# def update_SoC(charge_schedule, time_resolution, charge_rate, at_time):

charge_rate = 7.4  # kW
max_battery_cycles = 1500  # for TM3
charger_efficiency = 1  # for charger

arrival_time = pd.to_datetime('2019-02-25 19:15:00')
departure_time = pd.to_datetime('2019-02-26 1:00:00')
time_resolution = '15 min'

vrg_charge_duration = pd.Timedelta('105 min')
v1g_charge_duration = pd.Timedelta('310 min')
vrg_charging_intervals = vrg_charge_duration / time_resolution
v1g_charging_intervals = v1g_charge_duration / time_resolution

agile_extract = pd.read_excel(os.getcwd()[:-5] + 'Inputs\AgileExtract.xls', parse_dates=[0], index_col=0)
connection_extract = agile_extract[arrival_time : departure_time].resample(time_resolution).pad().iloc[:-1, :]

# print(connection_extract[connection_extract.index.min() : departure_time - pd.Timedelta('40 min')].sum())

initial_connections_available = connection_extract.copy()
zeros_charge_schedule = connection_extract
zeros_charge_schedule['Charge_Rate'] = 0

vrg_charge_schedule = vrg(vrg_charge_duration,
                          zeros_charge_schedule)

# v1g_charge_schedule, v1g_connections_available = v1g(vrg_charging_intervals,
#                                                      vrg_charge_schedule.copy(),
#                                                      vrg_connections_available.copy())

print(vrg_charge_schedule)
# print(vrg_connections_available)
# print(v1g_charge_schedule)
# print(v1g_connections_available)
