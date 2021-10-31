import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np


def vrg(charge_schedule):
    charge_schedule.loc[: charge_schedule.index.min() + vrg_charge_duration, 'Charge_In_Interval'] = 1
    return charge_schedule


def vrg_max(charge_schedule):
    charge_schedule.loc[: charge_schedule.index.min() + vrg_charge_duration + v1g_charge_duration,
    'Charge_In_Interval'] = 1
    return charge_schedule


def v1g(charge_schedule):
    while charge_schedule['Charge_In_Interval'].sum() * time_resolution <= v1g_charge_duration + vrg_charge_duration:
        calculate_soc(charge_schedule)
        virtual_cost(charge_schedule, 'v1g')
        working_charge_schedule = charge_schedule[charge_schedule['Charge_In_Interval'] == 0].iloc[:-1, :]
        charge_schedule.loc[working_charge_schedule['Virtual_Cost'].idxmin(), 'Charge_In_Interval'] = 1
    calculate_soc(charge_schedule)
    return charge_schedule


def v2g(charge_schedule):
    charge_schedule['Checked'] = charge_schedule['Charge_In_Interval'].copy()
    # v2g_total_cost = (charge_schedule['Charge_In_Interval'] * v1g_charge_schedule['Virtual_Cost']).sum()
    calculate_soc(charge_schedule)
    while charge_schedule['Checked'].sum() < charge_schedule.shape[0] - 1:
        # print(charge_schedule['Checked'].sum(), '/', charge_schedule.shape[0] - 1, ' connection intervals checked')

        working_charge_schedule = charge_schedule[charge_schedule['Checked'] == 0].iloc[:-1, :]
        discharge_time = working_charge_schedule['Price'].idxmax()

        discharge_time_mask = charge_schedule.index.to_series().isin(working_charge_schedule.index.to_series().values)
        charge_schedule.loc[discharge_time_mask, 'Discharge_Time'] = discharge_time
        charge_schedule.loc[discharge_time, 'Checked'] = 1
        virtual_cost(charge_schedule, 'v2g')
        working_charge_schedule = charge_schedule[charge_schedule['Checked'] == 0].iloc[:-1, :]

        if working_charge_schedule['Virtual_Net'].min() < 0:
            add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time, 1)
            # v2g_total_cost += working_charge_schedule['Virtual_Cost'].min()
            calculate_soc(charge_schedule)
            # x = charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:, 'SoC'].min()
            # calculate_soc(charge_schedule)
            if charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:, 'SoC'].min() < 0.15 or \
                    charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:, 'SoC'].max() > 0.9:
                add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time, 0)
                charge_schedule.loc[discharge_time, 'Checked'] = 0
                charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Checked'] = 1

    return charge_schedule


def calculate_running_cost(charge_schedule):
    real_cost_indicator = ((charge_schedule['Charge_In_Interval'] + 1) / 2).apply(np.floor)
    real_revenue_indicator = charge_schedule['Charge_In_Interval'].abs() - real_cost_indicator
    change_in_cost = real_cost_indicator * charge_schedule['Virtual_Cost'] - real_revenue_indicator * \
                     charge_schedule['Virtual_Revenue']
    cumsum_cost = (charge_schedule['Charge_In_Interval'].abs() * change_in_cost).cumsum()
    charge_schedule['Running_Cost'] = 0
    charge_schedule.iloc[1:, charge_schedule.columns.get_indexer(['Running_Cost'])] = cumsum_cost[:-1]
    # charge_schedule['Running_Cost'] = (charge_schedule['Charge_In_Interval'].abs() * change_in_cost).cumsum()
    # charge_schedule.itterows()
    # # for row, column in charge_schedule:
    # #     x = row
    # t = 'test'
    # # charge_schedule['Virtual_Cost'] =
    # # charge_schedule['sumcum_Cost'] =


def add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time, value):
    charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Charge_In_Interval'] = value
    charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Checked'] = value
    charge_schedule.loc[discharge_time, 'Charge_In_Interval'] = -value


def calculate_soc(charge_schedule):
    cumsum_soc = charge_schedule['Charge_In_Interval'].copy().cumsum() * SoC_resolution + \
                 charge_schedule.loc[charge_schedule.index.min(), 'SoC']
    charge_schedule.iloc[1:, charge_schedule.columns.get_indexer(['SoC'])] = cumsum_soc[:-1]
    return charge_schedule


def virtual_cost(charge_schedule, charger_type):
    soc_from_15 = calculate_soc(charge_schedule)['SoC'] / 3 + 0.30

    if charger_type == 'v1g':
        charge_schedule['Discharge_Time'] = charge_schedule.index.max()
        charge_schedule['Virtual_Revenue'] = 0
    elif charger_type == 'v2g':
        discharge_revenue = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Price'].values * charger_efficiency
        charge_schedule['Virtual_Revenue'] = (discharge_revenue - maker_taker_cost) * kWh_resolution

    charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / \
                           (departure_time - arrival_time)
    battery_ageing_cost = cycle_cost_fraction / (1 - soc_from_15 * charge_held_fraction * lifetime_ageing_factor)

    charge_schedule['Virtual_Cost'] = charge_schedule[
                                          'Price'] * kWh_resolution / charger_efficiency + battery_ageing_cost
    charge_schedule['Virtual_Net'] = charge_schedule['Virtual_Cost'] - charge_schedule['Virtual_Revenue']

    return charge_schedule


charge_rate = 7.4  # kW
battery_capacity = 54  # kWh
charger_efficiency = 0.9  # 0.9 for charger
plug_in_SoC = 0.055
battery_cost_per_kWh = 137e2  # 137e2
maker_taker_cost = 4  # 4
lifetime_ageing_factor = 1  # 1
max_battery_cycles = 1500 * 1.625  # * (1 + 0.625 * lifetime_ageing_factor)  # for TM3, factored to account for factory rating including lifetime degradation 65/40
price_volatility_factor = 1
tarriff_data = 'Inputs\AgileExtract.xls'


arrival_time = pd.to_datetime('2019-02-25 19:15:00')
departure_time = pd.to_datetime('2019-02-27 7:00:00')
time_resolution = pd.Timedelta('15 min')
kWh_resolution = charge_rate * time_resolution / pd.Timedelta('60 min')
cycle_cost_fraction = battery_cost_per_kWh * kWh_resolution / max_battery_cycles
SoC_resolution = cycle_cost_fraction * max_battery_cycles / battery_capacity / battery_cost_per_kWh

vrg_charge_duration = pd.Timedelta('1.61 h')
v1g_charge_duration = pd.Timedelta('2 h')

agile_extract = pd.read_excel(os.getcwd()[:-5] + tarriff_data, parse_dates=[0], index_col=0)
connection_extract = agile_extract[arrival_time: departure_time].resample(time_resolution).pad()  # .iloc[:-1, :]
connection_extract_mean_price = connection_extract['Price'].mean()
connection_extract['Price'] = (connection_extract['Price'] - connection_extract_mean_price) * price_volatility_factor + connection_extract_mean_price
connection_extract.loc[
    connection_extract.index.max(), 'Price'] = maker_taker_cost / charger_efficiency  # offset v1g and vrg revenue to 0 - this is kind of a hack

zeros_charge_schedule = connection_extract
zeros_charge_schedule['Charge_In_Interval'] = 0
zeros_charge_schedule.loc[zeros_charge_schedule.index.min(), 'SoC'] = plug_in_SoC

vrg_charge_schedule = vrg(zeros_charge_schedule)
vrg_charge_schedule_max = virtual_cost(calculate_soc(vrg_max(zeros_charge_schedule.copy())), 'v1g')
v1g_charge_schedule = v1g(vrg_charge_schedule.copy())
v2g_charge_schedule = v2g(v1g_charge_schedule.copy())

# plt.plot(v2g_charge_schedule['SoC'])
# plt.show()

# test = calculate_soc(vrg_charge_schedule)

# test = virtual_cost(vrg_charge_schedule)

v1g_total_cost = (v1g_charge_schedule['Charge_In_Interval'] * v1g_charge_schedule['Virtual_Cost']).sum()
# v1g_charge_schedule['Wholesale_Cost'] = v1g_charge_schedule['Price'] * kWh_resolution
# v1g_charge_schedule['Cost_Ratio'] = v1g_charge_schedule['Wholesale_Cost'] / v1g_charge_schedule['Virtual_Cost']
# v2g_total_cost_check = (
#         v2g_charge_schedule['Charge_In_Interval'] * v2g_charge_schedule['Price'] * kWh_resolution).sum()

calculate_running_cost(vrg_charge_schedule_max)
calculate_running_cost(v1g_charge_schedule)
calculate_running_cost(v2g_charge_schedule)

print('VRG virtual cost of connection period: ', vrg_charge_schedule_max['Running_Cost'].iloc[-1])
print('V1G virtual cost of connection period: ', v1g_charge_schedule['Running_Cost'].iloc[-1])
print('V2G virtual cost of connection period: ', v2g_charge_schedule['Running_Cost'].iloc[-1])

plt.subplot(311)
plt.plot(v2g_charge_schedule['Price'], label='Price')
# plt.plot(v2g_charge_schedule['Virtual_Cost'], label='Virtual_Cost')
# plt.plot(v2g_charge_schedule['Virtual_Revenue'], label='Virtual_Revenue')
plt.grid()
plt.legend()

plt.subplot(312)
plt.plot(vrg_charge_schedule_max['SoC'], label='vrg SoC')
plt.plot(v1g_charge_schedule['SoC'], label='v1g SoC')
plt.plot(v2g_charge_schedule['SoC'], label='v2g SoC')
plt.grid()
plt.legend()

plt.subplot(313)
plt.plot(vrg_charge_schedule_max['Running_Cost'], label='vrg Running_Cost')
plt.plot(v1g_charge_schedule['Running_Cost'], label='v1g Running_Cost')
plt.plot(v2g_charge_schedule['Running_Cost'], label='v2g Running_Cost')
plt.grid()
plt.legend()

figManager = plt.get_current_fig_manager()
figManager.window.state('zoomed')

plt.show()
