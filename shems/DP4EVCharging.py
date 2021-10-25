import pandas as pd
import os
import matplotlib.pyplot as plt


def vrg(charge_schedule):
    charge_schedule.loc[: charge_schedule.index.min() + vrg_charge_duration, 'Charger_Instruction'] = 1
    return charge_schedule


def v1g(charge_schedule):
    while charge_schedule['Charger_Instruction'].sum() * time_resolution <= v1g_charge_duration + vrg_charge_duration:
        calculate_soc(charge_schedule)
        virtual_cost(charge_schedule, 'v1g')
        working_charge_schedule = charge_schedule[charge_schedule['Charger_Instruction'] == 0]
        charge_schedule.loc[working_charge_schedule['Virtual_Cost'].idxmin(), 'Charger_Instruction'] = 1
    return charge_schedule


def v2g(charge_schedule):
    charge_schedule['Checked'] = charge_schedule['Charger_Instruction'].copy()
    v2g_total_cost = (charge_schedule['Charger_Instruction'] * v1g_charge_schedule['Virtual_Cost']).sum()
    while charge_schedule['Checked'].sum() < charge_schedule.shape[0]:
        calculate_soc(charge_schedule)

        working_charge_schedule = charge_schedule[charge_schedule['Checked'] == 0].copy()
        discharge_time = working_charge_schedule['Price'].idxmax()
        discharge_time_mask = charge_schedule.index.to_series().isin(working_charge_schedule.index.to_series().values)
        charge_schedule.loc[discharge_time_mask, 'Discharge_Time'] = discharge_time
        virtual_cost(charge_schedule, 'v2g')
        charge_schedule.loc[discharge_time, 'Checked'] = 1
        working_charge_schedule = charge_schedule[charge_schedule['Checked'] == 0].copy()
        # test = working_charge_schedule['Virtual_Cost'].min()

        if working_charge_schedule['Virtual_Net'].min() < 0:
            charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Charger_Instruction'] = 1
            charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Checked'] = 1
            charge_schedule.loc[working_charge_schedule['Price'].idxmax(), 'Charger_Instruction'] = -1
            # v2g_total_cost += working_charge_schedule['Virtual_Cost'].min()

    return charge_schedule, v2g_total_cost


def calculate_soc(charge_schedule):
    cumsum_soc = charge_schedule['Charger_Instruction'].copy().cumsum() * SoC_resolution + \
                 charge_schedule.loc[charge_schedule.index.min(), 'SoC']
    charge_schedule.iloc[1:, charge_schedule.columns.get_indexer(['SoC'])] = cumsum_soc[:-1]
    return charge_schedule


def virtual_cost(charge_schedule, charger_type='v1g'):
    if charger_type == 'vrg':  # not used
        soc_from_15 = calculate_soc(charge_schedule)['SoC'] / 3 + 0.30
        charge_schedule['Discharge_Time'] = charge_schedule.index.max()
        charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / \
                               (departure_time - arrival_time)
        battery_ageing_cost = cycle_cost_fraction / (1 - soc_from_15 * charge_held_fraction)
        charge_schedule['Virtual_Revenue'] = 0
    elif charger_type == 'v1g':
        # charge_schedule['Soc_From_15'] = calculate_soc(charge_schedule)['SoC'] / 3 + 0.30  # to delete
        soc_from_15 = calculate_soc(charge_schedule)['SoC'] / 3 + 0.30
        charge_schedule['Discharge_Time'] = charge_schedule.index.max()
        # charge_schedule['charge_held_fraction'] = (departure_time - charge_schedule.index.to_series()) / \
        #                                           (departure_time - arrival_time)
        charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / \
                               (departure_time - arrival_time)
        battery_ageing_cost = cycle_cost_fraction / (1 - soc_from_15 * charge_held_fraction)
        charge_schedule['Virtual_Revenue'] = 0
    elif charger_type == 'v2g':
        soc_from_15 = calculate_soc(charge_schedule)['SoC'] / 3 + 0.30
        charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / \
                               (departure_time - arrival_time)
        battery_ageing_cost = cycle_cost_fraction / (1 - soc_from_15 * charge_held_fraction)
        # link_discharge_price = charge_schedule['Discharge_Time'] == charge_schedule.index.to_series()
        # test2 = charge_schedule[test1].copy()
        # test3 = test2.loc[test2.index.min(), 'Price']
        test4 = charge_schedule.loc[charge_schedule['Discharge_Time'].copy(), 'Price'].values
        test5 = test4 * kWh_resolution * charger_efficiency
        charge_schedule['Virtual_Revenue'] = maker_taker_cost - test5
        charge_schedule.loc[charge_schedule.index.max(), 'Virtual_Revenue'] = 0

    charge_schedule['Virtual_Cost'] = charge_schedule['Price'] * kWh_resolution / charger_efficiency + \
                                      battery_ageing_cost
    charge_schedule['Virtual_Net'] = charge_schedule['Virtual_Cost'] + charge_schedule['Virtual_Revenue']

    return charge_schedule


charge_rate = 7.4  # kW
max_battery_cycles = 1500 * 1.625  # for TM3, factored to account for factory rating including lifetime degradation 65/40
battery_capacity = 54  # kWh
charger_efficiency = 1  # for charger
plug_in_SoC = 0.15
battery_cost_per_kWh = 137e2
maker_taker_cost = 4

arrival_time = pd.to_datetime('2019-02-25 19:17:00')
departure_time = pd.to_datetime('2019-02-26 19:12:00')
time_resolution = pd.Timedelta('30 min')
kWh_resolution = charge_rate * time_resolution / pd.Timedelta('60 min')
cycle_cost_fraction = battery_cost_per_kWh * kWh_resolution / max_battery_cycles
SoC_resolution = cycle_cost_fraction * max_battery_cycles / battery_capacity / battery_cost_per_kWh

vrg_charge_duration = pd.Timedelta('40 min')
v1g_charge_duration = pd.Timedelta('50 min')
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
vrg_charge_schedule_max = vrg(zeros_charge_schedule.copy())

v1g_charge_schedule = v1g(vrg_charge_schedule.copy())

v2g_charge_schedule, v2g_total_cost = v2g(v1g_charge_schedule.copy())

plt.plot(v2g_charge_schedule['SoC'])
plt.show()

# test = calculate_soc(vrg_charge_schedule)

# test = virtual_cost(vrg_charge_schedule)

v1g_total_cost = (v1g_charge_schedule['Charger_Instruction'] * v1g_charge_schedule['Virtual_Cost']).sum()
# v1g_charge_schedule['Wholesale_Cost'] = v1g_charge_schedule['Price'] * kWh_resolution
# v1g_charge_schedule['Cost_Ratio'] = v1g_charge_schedule['Wholesale_Cost'] / v1g_charge_schedule['Virtual_Cost']
v2g_total_cost_check = (
        v2g_charge_schedule['Charger_Instruction'] * v2g_charge_schedule['Price'] * kWh_resolution).sum()

print(v1g_total_cost)
print(v2g_total_cost)
print(v2g_total_cost_check)
#
# plt.subplot(311)
# # plt.plot(v1g_charge_schedule['Wholesale_Cost'], label='Wholesale_Cost')
# # plt.plot(v1g_charge_schedule['Battery_Ageing_Cost'], label='Battery_Ageing_Cost')
# plt.plot(v1g_charge_schedule['Virtual_Cost'], label='Virtual_Cost')
# plt.grid()
# plt.legend()
#
# plt.subplot(313)
# plt.plot(v1g_charge_schedule['SoC'], label='v1g_SoC')
# plt.plot(vrg_charge_schedule['SoC'], label='vrg_SoC')
# plt.grid()
# plt.legend()
#
# plt.show()
