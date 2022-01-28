import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

arrival_time = pd.to_datetime('2019-02-25 19:15:00')
departure_time = pd.to_datetime('2019-02-27 7:00:00')
app_data = 'Inputs\Typical_home_demand.xls'
app_demand = pd.read_excel(os.getcwd()[:-5] + app_data)
time_resolution = pd.Timedelta(app_demand['Duration (h)'].min(), 'h')
# app_demand_series = pd.date_range(arrival_time, departure_time, freq=time_resolution)
date_time_index = pd.date_range(arrival_time, departure_time, freq=time_resolution)
app_demand_series = pd.DataFrame(0, index=date_time_index, columns=['Power'])
test2 = list(set(date_time_index.date))
first_row_power = app_demand['Power'][1]
first_row_time = app_demand['Time On'][1]
first_row_duration = pd.Timedelta(app_demand['Duration (h)'][0], 'h')
# test1 = arrival_time + first_row_duration
first_row_datetime = pd.to_datetime(str(test2[1]) + '' + str())
app_demand_series.loc[first_row_datetime : first_row_datetime + first_row_duration, 'Power'] += first_row_power
print(app_demand)