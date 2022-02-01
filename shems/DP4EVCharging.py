import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import ApplianceDemand


def vrg(charge_schedule):
    """Populates charge schedule such that the vrg charging is done all upon connection"""
    charge_schedule.loc[: charge_schedule.index.min() + vrg_charge_duration, 'Charge_In_Interval'] = 1
    return charge_schedule


def vrg_max(charge_schedule):
    """Populates charge schedule such that the vrg and v1g charging is done all upon connection"""
    charge_schedule.loc[: charge_schedule.index.min() + vrg_charge_duration + v1g_charge_duration,
    'Charge_In_Interval'] = 1
    return charge_schedule


def v1g(charge_schedule):
    """Populates charge schedule with charge commands at intervals at which the virtual cost is lowest"""
    while charge_schedule['Charge_In_Interval'].sum() * time_resolution <= v1g_charge_duration + vrg_charge_duration:
        virtual_cost(charge_schedule, 'v1g')  # calculate virtual cost of charging in
        working_charge_schedule = charge_schedule[charge_schedule['Charge_In_Interval'] == 0].iloc[:-1,
                                  :]  # select interval from those that are not already designated as charging. Last row omitted as disconnect time (cannot charge during interval)
        charge_schedule.loc[working_charge_schedule[
                                'Virtual_Cost'].idxmin(), 'Charge_In_Interval'] = 1  # select cheapest available interval to charge
    calculate_soc(charge_schedule)  # update SoC after last charge command added
    return charge_schedule


def v2g(charge_schedule):
    """Populates charge schedule with charge and discharge commands, at intervals which result in a net profit. Works
    by selecting the maximum price interval for discharging, calculating the virtual net profit for charging (to
    enable discharging) in all other intervals, and adding charge/discharge interval pairs if profitable. Also
    ensures SoC limits are not exceeded (reserve charge TO DO, maximum SoC)."""

    charge_schedule['Checked'] = charge_schedule['Charge_In_Interval'].copy()  # initialise checked column from v1g
    while charge_schedule['Checked'].sum() < charge_schedule.shape[0] - 1:
        """Check all intervals for v2g suitability. TO DO: maybe stop after virtual net > 0"""
        # print(charge_schedule['Checked'].sum(), '/', charge_schedule.shape[0] - 1, ' connection intervals checked')

        working_charge_schedule = charge_schedule[charge_schedule['Checked'] == 0].iloc[:-1,:]  # select interval from those that are not already designated as charging. Last row omitted as disconnect time (cannot charge during interval)
        discharge_time = working_charge_schedule['Price'].idxmax()  # virtual revenue directly proportional to interval price

        # Mask system used as .loc difficult to use in this application: ideally would put working_charge_schedule in place of discharge_time_mask
        discharge_time_mask = charge_schedule.index.to_series().isin(working_charge_schedule.index.to_series().values)
        charge_schedule.loc[discharge_time_mask, 'Discharge_Time'] = discharge_time  # records the time at which the charge added during a charging interval will be discharged. Necessary to calculate the lifetime battery ageing cost
        charge_schedule.loc[discharge_time, 'Checked'] = 1  # most discharge intervals work before SoC check
        virtual_cost(charge_schedule, 'v2g')  # calculate virtual net profit for all available intervals charging to discharge in the discharge interval. V2G argument indicates to calculate discharge revenue
        working_charge_schedule = charge_schedule[charge_schedule['Checked'] == 0].iloc[:-1, :]  # reduce charge schedule to intervals available

        if working_charge_schedule['Virtual_Net'].min() < 0:  # if profitable
            add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time, 1)  # update schedule to charge and discharge at intervals
            calculate_soc(charge_schedule)  # test new charge/dischareg pair do not push SoC out of limits
            if charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:, 'SoC'].min() < 0.15 or \
                    charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:, 'SoC'].max() > 0.9:  # try new charge interval with same discharge interval, as SoC limit will be either before or after discharge interval and profitable charge intervals may still exist in the other direction
                add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time,
                                          -1)  # update schedule to NOT charge and discharge at intervals
                charge_schedule.loc[discharge_time, 'Checked'] = 0  # discharge interval unchecked, to be tested again
                charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Checked'] = 1  # charge interval checked, to be left uncharged

    return charge_schedule


def v2h(charge_schedule):
    charge_schedule['Checked'] = charge_schedule['Charge_In_Interval'].copy().abs()
    while charge_schedule['Checked'].sum() < charge_schedule.shape[0] - 1:
        working_charge_schedule = charge_schedule[charge_schedule['Checked'] == 0].iloc[:-1, :]
        discharge_time = working_charge_schedule['Appliance_Power'].idxmax()

        discharge_time_mask = charge_schedule.index.to_series().isin(working_charge_schedule.index.to_series().values)
        charge_schedule.loc[discharge_time_mask, 'Discharge_Time'] = discharge_time  # records the time at which the charge added during a charging interval will be discharged. Necessary to calculate the lifetime battery ageing cost
        charge_schedule.loc[discharge_time, 'Checked'] = 1  # most discharge intervals work before SoC check
        virtual_cost(charge_schedule,'v2h')  # calculate virtual net profit for all available intervals charging to discharge in the discharge interval. V2G argument indicates to calculate discharge revenue
        working_charge_schedule = charge_schedule[charge_schedule['Checked'] == 0].iloc[:-1, :]  # reduce charge schedule to intervals available

        if working_charge_schedule['Virtual_Net'].min() < 0:  # if profitable
            # update schedule to charge and discharge at intervals
            # test4 = charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin()]
            charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Charge_In_Interval'] += charge_schedule.loc[discharge_time, 'Appliance_Power'] / charge_rate
            # test3 = charge_schedule.loc[discharge_time]
            test4 = charge_schedule.loc[discharge_time, 'Appliance_Power'] / charge_rate
            charge_schedule.loc[discharge_time, 'Charge_In_Interval'] -= charge_schedule.loc[discharge_time, 'Appliance_Power'] / charge_rate
            test1 = charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Charge_In_Interval']
            test2 = charge_schedule.loc[discharge_time, 'Charge_In_Interval']
            if test1 >= 1 or test2 <= -1:
                charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Charge_In_Interval'] -= charge_schedule.loc[discharge_time, 'Appliance_Power'] / charge_rate
                charge_schedule.loc[discharge_time, 'Charge_In_Interval'] += charge_schedule.loc[discharge_time, 'Appliance_Power'] / charge_rate
                charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Checked'] = 1

            calculate_soc(charge_schedule)  # test new charge/dischareg pair do not push SoC out of limits
            if charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:, 'SoC'].min() < 0.15 or \
                    charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:, 'SoC'].max() > 0.9:  # try new charge interval with same discharge interval, as SoC limit will be either before or after discharge interval and profitable charge intervals may still exist in the other direction
                charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Charge_In_Interval'] -= charge_schedule.loc[discharge_time, 'Appliance_Power'] / charge_rate
                charge_schedule.loc[discharge_time, 'Charge_In_Interval'] += charge_schedule.loc[discharge_time, 'Appliance_Power'] / charge_rate
                charge_schedule.loc[discharge_time, 'Checked'] = 0  # discharge interval unchecked, to be tested again
                charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Checked'] = 1  # charge interval checked, to be left uncharged

    return charge_schedule


def calculate_running_cost(charge_schedule):
    """Split charge indication column into boolean columns, to enable cumulative summation of charging cost and
    discharging revenue through the connection period separately."""
    real_cost_indicator = ((charge_schedule['Charge_In_Interval'] + 1) / 2).apply(np.floor)
    real_appliance_cost_indicator = ((charge_schedule['Charge_In_Interval'] + 1) / 2).apply(np.ceil)
    real_revenue_indicator = charge_schedule['Charge_In_Interval'].abs() - real_cost_indicator
    change_in_cost = real_cost_indicator * charge_schedule['Virtual_Cost'] - real_revenue_indicator * charge_schedule['Virtual_Revenue'] #+ real_appliance_cost_indicator * charge_schedule['Appliance_Cost']
    cumsum_cost = change_in_cost.cumsum()  # cumulatively sum cost and revenue from each interval
    charge_schedule['Running_Cost'] = 0  # initialise column
    charge_schedule.iloc[1:, charge_schedule.columns.get_indexer(['Running_Cost'])] = cumsum_cost[
                                                                                      :-1]  # offset to calculate payment after charging occurred


def add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time, value):
    """Minimise repetition in adding/removing charge/discharge interval pairs to charge schedule."""
    charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Charge_In_Interval'] += value
    charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Checked'] += value
    charge_schedule.loc[discharge_time, 'Charge_In_Interval'] -= value


def calculate_soc(charge_schedule):
    """Convert charge indication column into a SoC time series. Necessary to detect SoC in bounds and plot time vs SoC"""
    SoC_resolution = charge_rate * time_resolution / pd.Timedelta('60 min') / battery_capacity
    cumsum_soc = charge_schedule['Charge_In_Interval'].copy().cumsum() * SoC_resolution + \
                 charge_schedule.loc[charge_schedule.index.min(), 'SoC']
    charge_schedule.iloc[1:, charge_schedule.columns.get_indexer(['SoC'])] = cumsum_soc[:-1]
    return charge_schedule


def virtual_cost(charge_schedule, charger_type):
    """Calculates the virtual cost and revenue of charger action, depending on the logic used. Factors accounted for
    include:
        - Wholesale electricity price
        - Cycle battery ageing (cost of battery wear due to charging and discharging)
        - Lifetime battery ageing (cost of battery wear due to holding charge further from 0.15 SoC for longer periods)
        - Charger efficiency (cost of energy lost buying and selling from the grid)
        - Maker taker fee (difference between wholesale electricity price when buying vs selling)

    Factors unaccounted for include:
        - Temperature battery ageing (cost of battery wear due to temperature unquantified)
        - Charge rate battery ageing (cost of battery wear due to charge rate variance found to be minimal
        and therefore is omitted)

    Factors TO BE ADDED: - Home generation revenue (home generation used rather than sold saves the maker taker cost)
    - Home demand cost savings reduce the maker taker fee from V2G discharge by the ratio of the demand power vs the
    controller charge rate. N.b. only a power shower could exceed the rating
    """
    kWh_resolution = charge_rate * time_resolution / pd.Timedelta('60 min')  # change in charge (kWh) after an interval of charging
    discharge_power_frac = 1

    calculate_soc(charge_schedule)  # calculate SoC profile to enable lifetime battery ageing calcs
    soc_from_15 = charge_schedule['SoC'] / 3 + 0.30  # linear formula derived from empirical study, to enable lifetime battery ageing calcs


    # charge_schedule['Appliance_Cost'] = charge_schedule['Appliance_Cost'] * charge_schedule['Price']

    if charger_type == 'v1g':
        charge_schedule[
            'Discharge_Time'] = charge_schedule.index.max()  # charge held for v1g until disconnection. IDEA: could add discharge gradient representative of journey
        charge_schedule[
            'Virtual_Revenue'] = 0  # IDEA: PV_kWh_resolution * charge_schedule['Price'] * charger_efficiency
    elif charger_type == 'v2g':
        discharge_price = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Price'].values * charger_efficiency
        discharge_home_frac = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Appliance_Power'].values / charge_rate
        adjusted_maker_taker = (1 - discharge_home_frac) * maker_taker_cost
        charge_schedule['Virtual_Revenue'] = ((discharge_price - adjusted_maker_taker.transpose()) * kWh_resolution).transpose()
        charge_schedule['Virtual_Revenue_old'] = ((discharge_price - maker_taker_cost) * kWh_resolution)
    elif charger_type == 'v2h':
        discharge_price = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Price'].values * charger_efficiency
        discharge_power_frac = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Appliance_Power'].values / charge_rate
        charge_schedule['Virtual_Revenue'] = (discharge_price * discharge_power_frac * kWh_resolution).transpose()

    charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / (departure_time - arrival_time)
    cycle_cost_fraction = battery_cost_per_kWh * kWh_resolution * discharge_power_frac / max_battery_cycles  # cost of battery wear due to charging and discharging
    battery_ageing_cost = cycle_cost_fraction / (1 - soc_from_15 * charge_held_fraction * lifetime_ageing_factor)

    charge_schedule['Virtual_Cost'] = charge_schedule['Price'] * kWh_resolution * discharge_power_frac / charger_efficiency + battery_ageing_cost
    charge_schedule['Virtual_Net'] = charge_schedule['Virtual_Cost'] - charge_schedule['Virtual_Revenue']

    return charge_schedule


def plot_vr12g(charge_schedule_vrg, charge_schedule_v1g, charge_schedule_v2g, charge_schedule_v2h, app_demand_series_frac):
    """Plot DP4 equivalent figures"""
    plt.subplot(411)
    plt.plot(charge_schedule_v2h['Charge_In_Interval'] * charge_rate, label='Charging Demand')
    plt.plot(app_demand_series_frac, label='Appliance Demand')
    plt.grid()
    plt.legend()

    plt.subplot(412)
    plt.plot(charge_schedule_vrg['Price'], label='Price')
    plt.grid()
    plt.legend()

    plt.subplot(413)
    plt.plot(charge_schedule_vrg['SoC'], label='vrg SoC')
    plt.plot(charge_schedule_v1g['SoC'], label='v1g SoC')
    plt.plot(charge_schedule_v2g['SoC'], label='v2g SoC')
    plt.plot(charge_schedule_v2h['SoC'], label='v2h SoC')
    plt.grid()
    plt.legend()

    plt.subplot(414)
    plt.plot(charge_schedule_vrg['Running_Cost'], label='vrg Running_Cost')
    plt.plot(charge_schedule_v1g['Running_Cost'], label='v1g Running_Cost')
    plt.plot(charge_schedule_v2g['Running_Cost'], label='v2g Running_Cost')
    plt.grid()
    plt.legend()

    figManager = plt.get_current_fig_manager()
    figManager.window.state('zoomed')

    plt.show()


def initialise_charge_schedule(appliance_forecast=True):
    agile_extract = pd.read_excel(os.getcwd()[:-5] + tariff_data, parse_dates=[0], index_col=0)
    connection_extract = agile_extract[arrival_time: departure_time].resample(time_resolution).pad()  # .iloc[:-1, :]
    connection_extract_mean_price = connection_extract['Price'].mean()
    connection_extract['Price'] = (connection_extract[
                                       'Price'] - connection_extract_mean_price) * price_volatility_factor + connection_extract_mean_price
    connection_extract.loc[
        connection_extract.index.max(), 'Price'] = maker_taker_cost / charger_efficiency  # offset v1g and vrg revenue to 0 - this is kind of a hack
    connection_extract['Charge_In_Interval'] = 0
    connection_extract.loc[connection_extract.index.min(), 'SoC'] = plug_in_SoC

    if appliance_forecast:
        connection_extract['Appliance_Power'] = ApplianceDemand.main(arrival_time, departure_time).resample(time_resolution).mean()[1:]
    else:
        connection_extract['Appliance_Power'] = connection_extract['Price'] * 0  # BODGE

    return connection_extract


"""Inputs from researched data. IDEA: make readable as .txt batch files"""
charge_rate = 7.4  # kW
battery_capacity = 54  # kWh
charger_efficiency = 0.9  # 0.9 for charger
plug_in_SoC = 0.055
battery_cost_per_kWh = 137e2  # 137e2
maker_taker_cost = 4  # 4
lifetime_ageing_factor = 1  # 1
max_battery_cycles = 1500 * 1.625  # * (1 + 0.625 * lifetime_ageing_factor)  # for TM3, factored to account for
# factory rating including lifetime degradation 65/40
price_volatility_factor = 1.4  # 1
tariff_data = 'Inputs\AgileExtract.xls'
arrival_time = pd.to_datetime('2019-02-25 19:15:00')
departure_time = pd.to_datetime('2019-02-27 7:00:00')
time_resolution = pd.Timedelta('15 min')
vrg_charge_duration = pd.Timedelta('1.61 h')  # TO be provided by Yaz's algo to calculate energy from distance
v1g_charge_duration = pd.Timedelta('2 h')  # TO be provided by Yaz's algo to calculate energy from distance

app_demand_series = ApplianceDemand.main(arrival_time, departure_time)
app_demand_series_frac = app_demand_series.resample(time_resolution).mean()
# app_demand_series_frac = app_demand_series_frac/charge_rate

# plt.plot(app_demand_series)
# plt.plot(app_demand_series_avg)
# plt.show()

"""Main body of code"""
zeros_charge_schedule = initialise_charge_schedule()
vrg_charge_schedule = vrg(zeros_charge_schedule)
vrg_charge_schedule_max = virtual_cost(calculate_soc(vrg_max(zeros_charge_schedule.copy())), 'v1g')
v1g_charge_schedule = v1g(vrg_charge_schedule.copy())
v2g_charge_schedule = v2g(v1g_charge_schedule.copy())
v2h_charge_schedule = v2h(v2g_charge_schedule.copy())

calculate_running_cost(vrg_charge_schedule_max)
calculate_running_cost(v1g_charge_schedule)
calculate_running_cost(v2g_charge_schedule)

print('VRG virtual cost of connection period: ', vrg_charge_schedule_max['Running_Cost'].iloc[-1])
print('V1G virtual cost of connection period: ', v1g_charge_schedule['Running_Cost'].iloc[-1])
print('V2G virtual cost of connection period: ', v2g_charge_schedule['Running_Cost'].iloc[-1])

plot_vr12g(vrg_charge_schedule_max, v1g_charge_schedule, v2g_charge_schedule, v2h_charge_schedule, app_demand_series_frac)
