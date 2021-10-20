import pandas as pd
import numpy as np
import os
import datetime
import matplotlib.pyplot as plt

arrival_time = pd.to_datetime('2019-02-25 19:15:00')
departure_time = pd.to_datetime('2019-02-26 7:00:00')
time_resolution = '15min'
agile_extract = pd.read_excel(os.getcwd()[:-5] + 'Inputs\AgileExtract.xls', parse_dates=[0], index_col=0)
connection_extract = agile_extract[arrival_time: departure_time].resample(time_resolution).pad().iloc[:-1, :]

initial_connections_available = connection_extract.copy()
zeros_charge_schedule = connection_extract
zeros_charge_schedule['Charge_Rate'] = 0


def v1g(charge_duration, charge_schedule, connections_available):
    while charge_schedule['Charge_Rate'].sum() < charge_duration:
        time_to_charge = connections_available['Price'].idxmin()
        charge_schedule.__getitem__('Charge_Rate').__setitem__(time_to_charge, 1)
        connections_available.drop(time_to_charge, inplace=True)

    return charge_schedule, connections_available


v1g_charge_schedule, v1g_connections_available = v1g(30, zeros_charge_schedule, initial_connections_available)


print(v1g_charge_schedule)
print(v1g_connections_available)

