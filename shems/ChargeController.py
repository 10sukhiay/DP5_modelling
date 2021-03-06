import pandas as pd
import matplotlib.pyplot as plt
import ApplianceDemand
import HomeGenerationCode as HomeGen
import IntergratedHeating as Heat
import Journey_charge_v3 as jcharge
import API_update as API
import time
import API_tests
import csv
import math

def vrg(charge_schedule, battery_mode):
    """Populates charge schedule such that the vrg charging is done all upon connection"""
    if battery_mode == 'EV':
        charge_schedule.loc[: charge_schedule.index.min() + vrg_charge_duration, 'Charge_In_Interval'] = 1
    return charge_schedule


def vrg_max(charge_schedule, battery_mode):
    """Populates charge schedule such that the vrg and v1g charging is done all upon connection"""
    if battery_mode == 'EV':
        charge_schedule.loc[: charge_schedule.index.min() + vrg_charge_duration + v1g_charge_duration, 'Charge_In_Interval'] = 1
    return charge_schedule


def v1g(charge_schedule, battery_mode, motivation):  # ADD CO2 motivation
    """Populates charge schedule with charge commands at intervals at which the virtual cost is lowest"""
    virtual_cost(charge_schedule, 'v1g')  # calculate virtual cost of charging in
    virtual_carbon_cost(charge_schedule, 'v1g')

    if battery_mode == 'EV':
        if motivation == 'Price':
            while (charge_schedule['Charge_In_Interval'].sum() * time_resolution <= v1g_charge_duration + vrg_charge_duration) and (charge_schedule['Charge_In_Interval'].sum() < (charge_schedule.shape[0] - 1)):

                working_charge_schedule = charge_schedule[charge_schedule['Charge_In_Interval'] == 0].iloc[:-1, :]  # select interval from those that are not already designated as charging. Last row omitted as disconnect time (cannot charge during interval)
                test = working_charge_schedule.shape[0]
                test2 = charge_schedule['Charge_In_Interval'].sum()
                test3 = (charge_schedule.shape[0] - 1)
                charge_schedule.loc[working_charge_schedule['Virtual_Cost'].idxmin(), 'Charge_In_Interval'] = 1  # select cheapest available interval to charge

            calculate_soc(charge_schedule)  # update SoC after last charge command added
        elif motivation == 'Carbon':
            while charge_schedule['Charge_In_Interval'].sum() * time_resolution <= v1g_charge_duration + vrg_charge_duration or charge_schedule['Charge_In_Interval'].iloc[:-1, :].mean() < 1:

                working_charge_schedule = charge_schedule[charge_schedule['Charge_In_Interval'] == 0].iloc[:-1, :]  # select interval from those that are not already designated as charging. Last row omitted as disconnect time (cannot charge during interval)
                charge_schedule.loc[working_charge_schedule['Virtual_Carbon_Cost'].idxmin(), 'Charge_In_Interval'] = 1  # select cheapest available interval to charge
            calculate_soc(charge_schedule)  # update SoC after last charge command added
    return charge_schedule


def v2(charge_schedule, battery_mode, motivation):
    """Populates charge schedule with charge and discharge commands, at intervals which result in a net profit. Works
    by selecting the maximum price interval for discharging, calculating the virtual net profit for charging (to
    enable discharging) in all other intervals, and adding charge/discharge interval pairs if profitable. Also
    ensures SoC limits are not exceeded (reserve charge TO DO, maximum SoC)."""

    charge_schedule['Checked'] = charge_schedule['Charge_In_Interval'].copy().abs()  # initialise checked column from v1g

    while charge_schedule['Checked'].sum() < charge_schedule.shape[0] - 1:
        """Check all intervals for v2g suitability. TO DO: maybe stop after virtual net > 0"""
        # print(charge_schedule['Checked'].sum(), '/', charge_schedule.shape[0] - 1, ' connection intervals checked')

        working_charge_schedule = charge_schedule[charge_schedule['Checked'] == 0].iloc[:-1, :]

        if battery_mode == 'g':
            discharge_mask_mode = 'v2g'
            discharge_time = working_charge_schedule['Price'].idxmax()  # virtual revenue directly proportional to interval price
            test = 1
        elif battery_mode == 'h':
            discharge_mask_mode = 'v2h'
            discharge_time = working_charge_schedule['Home_Power'].idxmax()
            test = charge_schedule.loc[discharge_time, 'Home_Power'] / charge_rate

        charge_schedule, working_charge_schedule = discharge_mask(charge_schedule, working_charge_schedule, discharge_time, discharge_mask_mode)

        if motivation == 'Price':
            if working_charge_schedule['Virtual_Net'].min() < 0:  # if profitable
                add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time,
                                          test, motivation)  # update schedule to charge and discharge at intervals
                calculate_soc(charge_schedule)  # test new charge/dischareg pair do not push SoC out of limits
                if charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:,
                   'SoC'].min() < battery_v2g_floor or \
                        charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:,
                        'SoC'].max() > battery_v2g_ceil:  # try new charge interval with same discharge interval, as SoC limit will be either before or after discharge interval and profitable charge intervals may still exist in the other direction
                    add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time,
                                              -test, motivation)  # update schedule to NOT charge and discharge at intervals
                    charge_schedule.loc[
                        discharge_time, 'Checked'] = 0  # discharge interval unchecked, to be tested again
                    charge_schedule.loc[working_charge_schedule[
                                            'Virtual_Net'].idxmin(), 'Checked'] = 1  # charge interval checked, to be left uncharged
        elif motivation == 'Carbon':
            if working_charge_schedule['Virtual_Carbon_Net'].min() < 0:  # if profitable
                add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time,
                                          test, motivation)  # update schedule to charge and discharge at intervals
                calculate_soc(charge_schedule)  # test new charge/dischareg pair do not push SoC out of limits
                if charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:,
                   'SoC'].min() < battery_v2g_floor or \
                        charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:,
                        'SoC'].max() > battery_v2g_ceil:  # try new charge interval with same discharge interval, as SoC limit will be either before or after discharge interval and profitable charge intervals may still exist in the other direction
                    add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time,
                                              -test, motivation)  # update schedule to NOT charge and discharge at intervals
                    charge_schedule.loc[
                        discharge_time, 'Checked'] = 0  # discharge interval unchecked, to be tested again
                    charge_schedule.loc[working_charge_schedule[
                                            'Virtual_Carbon_Net'].idxmin(), 'Checked'] = 1  # charge interval checked, to be left uncharged

        # charge_schedule, working_charge_schedule = discharge_mask(charge_schedule, working_charge_schedule, discharge_time, battery_mode)

        # if working_charge_schedule['Virtual_Net'].min() < 0:  # if profitable
        #     add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time, test)  # update schedule to charge and discharge at intervals
        #     calculate_soc(charge_schedule)  # test new charge/dischareg pair do not push SoC out of limits
        #     if charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:, 'SoC'].min() < battery_v2g_floor or \
        #             charge_schedule.loc[charge_schedule.index.min() + vrg_charge_duration:, 'SoC'].max() > battery_v2g_ceil:  # try new charge interval with same discharge interval, as SoC limit will be either before or after discharge interval and profitable charge intervals may still exist in the other direction
        #         add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time, -test)  # update schedule to NOT charge and discharge at intervals
        #         charge_schedule.loc[discharge_time, 'Checked'] = 0  # discharge interval unchecked, to be tested again
        #         charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Checked'] = 1  # charge interval checked, to be left uncharged

    return charge_schedule


def discharge_mask(charge_schedule, working_charge_schedule, discharge_time, battery_mode):
    # Mask system used as .loc difficult to use in this application: ideally would put working_charge_schedule in place of discharge_time_mask
    discharge_time_mask = charge_schedule.index.to_series().isin(working_charge_schedule.index.to_series().values)
    charge_schedule.loc[discharge_time_mask, 'Discharge_Time'] = discharge_time  # records the time at which the charge added during a charging interval will be discharged. Necessary to calculate the lifetime battery ageing cost
    charge_schedule.loc[discharge_time, 'Checked'] = 1  # most discharge intervals work before SoC check
    virtual_cost(charge_schedule, battery_mode)  # calculate virtual net profit for all available intervals charging to discharge in the discharge interval. V2G argument indicates to calculate discharge revenue
    virtual_carbon_cost(charge_schedule, battery_mode)  # IDK if this works
    working_charge_schedule = charge_schedule[charge_schedule['Checked'] == 0].iloc[:-1,:]  # reduce charge schedule to intervals available
    return charge_schedule, working_charge_schedule


def calculate_running_cost(charge_schedule):
    """Split charge indication column into boolean columns, to enable cumulative summation of charging cost and
    discharging revenue through the connection period separately."""

    kW_to_kWh = time_resolution / pd.Timedelta('60 min')
    battery_discharge = charge_schedule['Charge_In_Interval'].values < 0
    battery_charge = charge_schedule['Charge_In_Interval'].values > 0
    home_by_grid = (charge_schedule['Charge_In_Interval'].values == 0) + battery_charge

    change_in_home_cost = home_by_grid * kW_to_kWh * (charge_schedule['Home_Power'] * charge_schedule['Price'] - (charge_schedule['Solar_Power'] * (charge_schedule['Price'] - kWh_export_fee)))
    change_in_total_cost = battery_charge * charge_schedule['Virtual_Cost'] - battery_discharge * charge_schedule['Virtual_Revenue'] + change_in_home_cost
    cumsum_cost = change_in_total_cost.cumsum()  # cumulatively sum cost and revenue from each interval
    charge_schedule['Running_Cost'] = 0  # initialise column
    charge_schedule.iloc[1:, charge_schedule.columns.get_indexer(['Running_Cost'])] = cumsum_cost[:-1]  # offset to calculate payment after charging occurred


def calculate_running_carbon(charge_schedule):
    """Split charge indication column into boolean columns, to enable cumulative summation of charging cost and
    discharging revenue through the connection period separately."""

    kW_to_kWh = time_resolution / pd.Timedelta('60 min')
    battery_discharge = charge_schedule['Charge_In_Interval'].values < 0
    battery_charge = charge_schedule['Charge_In_Interval'].values > 0
    home_by_grid = (charge_schedule['Charge_In_Interval'].values == 0) + battery_charge

    change_in_home_cost = home_by_grid * kW_to_kWh * (charge_schedule['Home_Power'] - charge_schedule['Solar_Power']) * charge_schedule['Carbon Intensity']
    change_in_total_cost = battery_charge * charge_schedule['Virtual_Carbon_Cost'] - battery_discharge * charge_schedule['Virtual_Carbon_Revenue'] + change_in_home_cost
    cumsum_cost = change_in_total_cost.cumsum()  # cumulatively sum cost and revenue from each interval
    charge_schedule['Running_Carbon_Cost'] = 0  # initialise column
    charge_schedule.iloc[1:, charge_schedule.columns.get_indexer(['Running_Carbon_Cost'])] = cumsum_cost[:-1]  # offset to calculate payment after charging occurred


def add_discharge_to_schedule(charge_schedule, working_charge_schedule, discharge_time, value, motivation):
    """Minimise repetition in adding/removing charge/discharge interval pairs to charge schedule."""
    if motivation == 'Price':
        charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Charge_In_Interval'] += value
        if math.isnan(value/value):
            bodge = 1
        else:
            bodge = value/value
        charge_schedule.loc[working_charge_schedule['Virtual_Net'].idxmin(), 'Checked'] += bodge
        charge_schedule.loc[discharge_time, 'Charge_In_Interval'] -= value
    if motivation == 'Carbon':
        charge_schedule.loc[working_charge_schedule['Virtual_Carbon_Net'].idxmin(), 'Charge_In_Interval'] += value
        if math.isnan(value/value):
            bodge = 1
        else:
            bodge = value/value
        charge_schedule.loc[working_charge_schedule['Virtual_Carbon_Net'].idxmin(), 'Checked'] += bodge
        charge_schedule.loc[discharge_time, 'Charge_In_Interval'] -= value


def calculate_soc(charge_schedule):
    """Convert charge indication column into a SoC time series. Necessary to detect SoC in bounds and plot time vs SoC"""
    SoC_resolution = charge_rate * time_resolution / pd.Timedelta('60 min') / battery_capacity
    cumsum_soc = charge_schedule['Charge_In_Interval'].copy().cumsum() * SoC_resolution + charge_schedule.loc[charge_schedule.index.min(), 'SoC']
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
    discharge_home_frac = 1

    calculate_soc(charge_schedule)  # calculate SoC profile to enable lifetime battery ageing calcs
    soc_from_15 = charge_schedule['SoC'] / 3 + 0.30  # linear formula derived from empirical study, to enable lifetime battery ageing calcs


    if charger_type == 'v1g':
        charge_schedule['Discharge_Time'] = charge_schedule.index.max()  # charge held for v1g until disconnection. IDEA: could add discharge gradient representative of journey
        charge_schedule['Virtual_Revenue'] = 0  # IDEA: PV_kWh_resolution * charge_schedule['Price'] * charger_efficiency

        charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / (
                plug_out_time - plug_in_time)
        cycle_cost_fraction = battery_cost_per_kWh * kWh_resolution * discharge_home_frac / max_battery_cycles  # cost of battery wear due to charging and discharging
        battery_ageing_cost = cycle_cost_fraction / (1 - soc_from_15 * charge_held_fraction * lifetime_ageing_factor)
        charge_schedule['Virtual_Cost'] = charge_schedule['Price'] * (charge_rate - charge_schedule['Solar_Power']) * time_resolution / pd.Timedelta('60 min') / charger_efficiency + battery_ageing_cost


    elif charger_type == 'v2g':

        kWh_discharge_price = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Price'].values
        home_consumption_kW = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Home_Power'].values
        export_kW = charge_rate - home_consumption_kW
        charge_schedule['Virtual_Revenue'] = (kWh_discharge_price * home_consumption_kW + (kWh_discharge_price - kWh_export_fee) * export_kW) * time_resolution / pd.Timedelta('60 min') * charger_efficiency

        charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / (plug_out_time - plug_in_time)
        cycle_cost_fraction = battery_cost_per_kWh * kWh_resolution * discharge_home_frac / max_battery_cycles  # cost of battery wear due to charging and discharging
        battery_ageing_cost = cycle_cost_fraction * lifetime_ageing_factor / (1 - soc_from_15 * charge_held_fraction)
        charge_schedule['Virtual_Cost'] = charge_schedule['Price'] * (charge_rate - charge_schedule['Solar_Power']) * time_resolution / pd.Timedelta('60 min') / charger_efficiency + battery_ageing_cost
        charge_schedule['Adjusted_Price'] = charge_schedule['Price'] * (charge_rate - charge_schedule['Solar_Power'])/charge_rate

    elif charger_type == 'v2h':

        kWh_discharge_price = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Price'].values  # .values * charger_efficiency
        home_consumption_kW = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Home_Power'].values
        keep_revenue_mask = (charge_schedule['Charge_In_Interval'].values == -1) + (charge_schedule['Charge_In_Interval'].values == 1)
        update_revenue_mask = ~keep_revenue_mask
        charge_schedule['Virtual_Revenue'] = update_revenue_mask * kWh_discharge_price * home_consumption_kW * time_resolution / pd.Timedelta('60 min') * charger_efficiency + charge_schedule['Virtual_Revenue'] * keep_revenue_mask

        charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / (plug_out_time - plug_in_time)
        cycle_cost_fraction = battery_cost_per_kWh * home_consumption_kW * time_resolution / pd.Timedelta('60 min') / max_battery_cycles  # cost of battery wear due to charging and discharging
        battery_ageing_cost = cycle_cost_fraction * lifetime_ageing_factor/ (1 - soc_from_15 * charge_held_fraction)
        charge_schedule['Virtual_Cost'] = update_revenue_mask * (charge_schedule['Price'] * (home_consumption_kW - charge_schedule['Solar_Power']) * time_resolution / pd.Timedelta('60 min') / charger_efficiency + battery_ageing_cost) + charge_schedule['Virtual_Cost'] * keep_revenue_mask

    charge_schedule['Virtual_Net'] = charge_schedule['Virtual_Cost'] - charge_schedule['Virtual_Revenue']

    return charge_schedule


def virtual_carbon_cost(charge_schedule, charger_type):
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
    discharge_home_frac = 1

    calculate_soc(charge_schedule)  # calculate SoC profile to enable lifetime battery ageing calcs
    soc_from_15 = charge_schedule['SoC'] / 3 + 0.30  # linear formula derived from empirical study, to enable lifetime battery ageing calcs


    if charger_type == 'v1g':
        charge_schedule['Discharge_Time'] = charge_schedule.index.max()  # charge held for v1g until disconnection. IDEA: could add discharge gradient representative of journey
        charge_schedule['Virtual_Carbon_Revenue'] = 0  # IDEA: PV_kWh_resolution * charge_schedule['Price'] * charger_efficiency

        charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / (
                plug_out_time - plug_in_time)
        cycle_cost_fraction = battery_carbon_per_kWh * kWh_resolution * discharge_home_frac / max_battery_cycles  # cost of battery wear due to charging and discharging
        battery_ageing_cost = cycle_cost_fraction / (1 - soc_from_15 * charge_held_fraction * lifetime_ageing_factor)
        charge_schedule['Virtual_Carbon_Cost'] = charge_schedule['Carbon Intensity'] * (charge_rate - charge_schedule['Solar_Power']) * time_resolution / pd.Timedelta('60 min') / charger_efficiency + battery_ageing_cost


    elif charger_type == 'v2g':

        kWh_discharge_price = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Carbon Intensity'].values
        home_consumption_kW = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Home_Power'].values
        export_kW = charge_rate - home_consumption_kW
        charge_schedule['Virtual_Carbon_Revenue'] = (kWh_discharge_price * (home_consumption_kW * export_kW)) * time_resolution / pd.Timedelta('60 min') * charger_efficiency

        charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / (plug_out_time - plug_in_time)
        cycle_cost_fraction = battery_carbon_per_kWh * kWh_resolution * discharge_home_frac / max_battery_cycles  # cost of battery wear due to charging and discharging
        battery_ageing_cost = cycle_cost_fraction * lifetime_ageing_factor / (1 - soc_from_15 * charge_held_fraction)
        charge_schedule['Virtual_Carbon_Cost'] = charge_schedule['Carbon Intensity'] * (charge_rate - charge_schedule['Solar_Power']) * time_resolution / pd.Timedelta('60 min') / charger_efficiency + battery_ageing_cost
        charge_schedule['Adjusted_Carbon_Intensity'] = charge_schedule['Carbon Intensity'] * (charge_rate - charge_schedule['Solar_Power'])/charge_rate

    elif charger_type == 'v2h':

        kWh_discharge_price = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Carbon Intensity'].values  # .values * charger_efficiency
        home_consumption_kW = charge_schedule.loc[charge_schedule['Discharge_Time'], 'Home_Power'].values
        keep_revenue_mask = (charge_schedule['Charge_In_Interval'].values == -1) + (charge_schedule['Charge_In_Interval'].values == 1)
        update_revenue_mask = ~keep_revenue_mask
        charge_schedule['Virtual_Carbon_Revenue'] = update_revenue_mask * kWh_discharge_price * home_consumption_kW * time_resolution / pd.Timedelta('60 min') * charger_efficiency + charge_schedule['Virtual_Carbon_Revenue'] * keep_revenue_mask

        charge_held_fraction = (charge_schedule['Discharge_Time'] - charge_schedule.index.to_series()) / (plug_out_time - plug_in_time)
        cycle_cost_fraction = battery_carbon_per_kWh * home_consumption_kW * time_resolution / pd.Timedelta('60 min') / max_battery_cycles  # cost of battery wear due to charging and discharging
        battery_ageing_cost = cycle_cost_fraction * lifetime_ageing_factor/ (1 - soc_from_15 * charge_held_fraction)
        charge_schedule['Virtual_Carbon_Cost'] = update_revenue_mask * (charge_schedule['Carbon Intensity'] * (home_consumption_kW - charge_schedule['Solar_Power']) * time_resolution / pd.Timedelta('60 min') / charger_efficiency + battery_ageing_cost) + charge_schedule['Virtual_Carbon_Cost'] * keep_revenue_mask

    charge_schedule['Virtual_Carbon_Net'] = charge_schedule['Virtual_Carbon_Cost'] - charge_schedule['Virtual_Carbon_Revenue']

    return charge_schedule


def plot_vr12g(charge_schedule_vrg, charge_schedule_v1g, charge_schedule_v2g, charge_schedule_v2h, charge_schedule_v2hg, case, row, descrp):
    """Plot DP4 equivalent figures"""

    fig = plt.figure(figsize=(20, 15), dpi=100)

    plt.subplot(511)
    # plt.plot(charge_schedule_v2h['Charge_In_Interval'] * charge_rate, label='V2H Charging Demand')
    # plt.plot(charge_schedule_v2g['Charge_In_Interval'] * charge_rate, label='V2G Charging Demand')
    plt.plot(charge_schedule_v2h['Home_Power'], label='Home Power')
    plt.plot(charge_schedule_v2h['Solar_Power'], label='Solar Power')
    # plt.plot(app_demand_series_frac, label='Appliance Demand')
    plt.grid()
    plt.legend()

    plt.subplot(512)
    plt.plot(charge_schedule_vrg['Price'], label='Price')
    # plt.plot(charge_schedule_v2g['Adjusted_Price'], label='Adjusted Price')
    plt.plot(charge_schedule_v2g['Carbon Intensity'], label='Carbon Intensity')  # need to fix axis
    # plt.plot(charge_schedule_v2g['Virtual_Cost'], label='v2h cost')
    # plt.plot(charge_schedule_v2g['Virtual_Revenue'], label='v2h rev')
    # plt.plot(charge_schedule_v2g['Virtual_Net'], label='v2h net')
    # plt.plot(charge_schedule_v2g['Virtual_Cost'], label='v2g cost')
    plt.grid()
    plt.legend()

    plt.subplot(513)
    plt.plot(charge_schedule_vrg['SoC'], label='vrg SoC')
    plt.plot(charge_schedule_v1g['SoC'], label='v1g SoC')
    # plt.plot(charge_schedule_v2g['SoC'], label='v2g SoC')
    # plt.plot(charge_schedule_v2h['SoC'], label='v2h SoC')
    plt.plot(charge_schedule_v2hg['SoC'], label='v2hg SoC')
    plt.grid()
    plt.legend()

    plt.subplot(514)
    plt.plot(charge_schedule_vrg['Running_Cost'], label='vrg Running_Cost')
    plt.plot(charge_schedule_v1g['Running_Cost'], label='v1g Running_Cost')
    # plt.plot(charge_schedule_v2g['Running_Cost'], label='v2g Running_Cost')
    plt.plot(charge_schedule_v2hg['Running_Cost'], label='v2hg Running_Cost')
    # plt.plot(charge_schedule_v2h['Running_Cost'], label='v2h Running_Cost')
    plt.grid()
    plt.legend()

    plt.subplot(515)
    plt.plot(charge_schedule_vrg['Running_Carbon_Cost'], label='vrg Running_Carbon_Cost')
    plt.plot(charge_schedule_v1g['Running_Carbon_Cost'], label='v1g Running_Carbon_Cost')
    # plt.plot(charge_schedule_v2g['Running_Carbon_Cost'], label='v2g Running_Carbon_Cost')
    plt.plot(charge_schedule_v2hg['Running_Carbon_Cost'], label='v2hg Running_Carbon_Cost')
    # plt.plot(charge_schedule_v2h['Running_Carbon_Cost'], label='v2h Running_Carbon_Cost')
    plt.grid()
    plt.legend()

    # plt.show()

    # figManager = plt.get_current_fig_manager()
    # figManager.window.state('zoomed')
    # figManager.frame.Maximize(True)

    # plt.autoscale()
    # plt.title('Test: ' + str(number))  # Doesn't work
    fig.suptitle('Row: ' + str(row + 2) + ', Case: ' + str(case) + ', ' + descrp)
    fig.savefig('../Results/Figures/' + str(row + 2) + ' ' + str(case) + ', ' + descrp)
    fig.clf()




# def charge_duration


def initialise_charge_schedule(appliance_forecast, heating_type, inputs):
    agile_extract = pd.read_csv('../Inputs/' + tariff_imp_data, parse_dates=[0], index_col=0).resample(time_resolution).pad()
    carbon_intensity = pd.read_csv('../Inputs/' + carbon_intenisty, parse_dates=[0], index_col=0).resample(time_resolution).pad()
    agile_extract_exp = pd.read_csv('../Inputs/' + tariff_exp_data, parse_dates=[0], index_col=0).resample(time_resolution).pad()
    home_power_raw = pd.read_csv('../Inputs/' + 'LMEVHomePower.csv', parse_dates=[0], index_col=0).resample(time_resolution).pad()

    agile_extract.index = agile_extract.index.tz_localize(None)
    carbon_intensity.index = carbon_intensity.index.tz_localize(None)
    agile_extract_exp.index = agile_extract_exp.index.tz_localize(None)
    home_power_raw.index = home_power_raw.index.tz_localize(None)

    # carbon_extract = carbon_intensity[plug_in_time.replace(year=2021): plug_out_time.replace(year=2021)].copy()
    test = plug_out_time
    test1 = plug_in_time

    global connection_extract

    connection_extract = agile_extract[plug_in_time: plug_out_time].copy()  # .iloc[:-1, :]
    connection_extract_mean_price = connection_extract['Price'].mean()
    connection_extract['Price'] = (connection_extract['Price'] - connection_extract_mean_price) * price_volatility_factor + connection_extract_mean_price
    connection_extract.loc[connection_extract.index.max(), 'Price'] = kWh_export_fee / charger_efficiency  # offset v1g and vrg revenue to 0 - this is kind of a hack
    # test2 = carbon_intensity[plug_in_time.replace(year=2021): plug_out_time.replace(year=2021)].values
    connection_extract['Carbon Intensity'] = carbon_intensity[plug_in_time.replace(year=2019): plug_out_time.replace(year=2019)].values
    connection_extract['Charge_In_Interval'] = 0
    connection_extract.loc[connection_extract.index.min(), 'SoC'] = plug_in_SoC

    if solar_connected:
        connection_extract['Solar_Power'] = HomeGen.main(plug_in_time.replace(year=2019), plug_out_time.replace(year=2019), time_resolution,inputs)  # .resample(time_resolution).mean()[1:]
    else:
        connection_extract['Solar_Power'] = connection_extract['Price'] * 0  # BODGE

    if appliance_forecast:
        # connection_extract['Appliance_Power'] = ApplianceDemand.main(plug_in_time, plug_out_time).resample(time_resolution).mean()  # [1:]
        connection_extract['Appliance_Power'] = home_power_raw[
                                                 plug_in_time.replace(year=2019): plug_out_time.replace(
                                                     year=2019)].values

        # test5 = Heat.mainElec(plug_in_time.replace(year=2019), plug_out_time.replace(year=2019), time_resolution, inputs)
        # poc = time.time()
        # connection_extract['Heating_Power_ASHP'] = Heat.mainASHP(plug_in_time, plug_out_time, time_resolution)
        if heating_type == 'Gas':
            connection_extract['Heating_Power'] = Heat.mainElec(plug_in_time.replace(year=2019),
                                                                plug_out_time.replace(year=2019), time_resolution,
                                                                inputs).values  # Heat.mainElec(plug_out_time.replace(year=2019), plug_out_time.replace(year=2019), time_resolution, inputs)

            connection_extract['Home_Power'] = connection_extract['Appliance_Power']
            #connection_extract['Appliance_Power'] = 0 # - connection_extract['Solar_Power']
            gas_cost = connection_extract['Heating_Power'] / gas_efficiency * (time_resolution / pd.Timedelta('60 min')) * gas_price
            gas_carbon = connection_extract['Heating_Power'] / gas_efficiency * (time_resolution / pd.Timedelta('60 min')) * gas_c_intenisty
            total_gas_cost = gas_cost.cumsum()[-1]
            total_gas_carbon = gas_carbon.cumsum()[-1]
        else:
            if heating_type == 'Electric':
                connection_extract['Heating_Power'] = Heat.mainElec(plug_in_time.replace(year=2019),
                                                                    plug_out_time.replace(year=2019), time_resolution,
                                                                    inputs).values  # Heat.mainElec(plug_out_time.replace(year=2019), plug_out_time.replace(year=2019), time_resolution, inputs)
            elif heating_type == 'ASHP':
                connection_extract['Heating_Power'] = Heat.mainASHP(plug_in_time.replace(year=2019),
                                                                    plug_out_time.replace(year=2019), time_resolution,
                                                                    inputs).values  # Heat.mainElec(plug_out_time.replace(year=2019), plug_out_time.replace(year=2019), time_resolution, inputs)
            elif heating_type == 'GSHP':
                connection_extract['Heating_Power'] = Heat.mainGSHP(plug_in_time.replace(year=2019),
                                                                    plug_out_time.replace(year=2019), time_resolution,
                                                                    inputs).values  # Heat.mainElec(plug_out_time.replace(year=2019), plug_out_time.replace(year=2019), time_resolution, inputs)
            else:
                print('Error: heat type input invalid')
            connection_extract['Home_Power'] = connection_extract['Appliance_Power'] + connection_extract['Heating_Power']  # - connection_extract['Solar_Power']
            total_gas_cost = 0
            total_gas_carbon = 0
    else:
        connection_extract['Appliance_Power'] = connection_extract['Price'] * 0  # BODGE
        connection_extract['Heating_Power'] = connection_extract['Price'] * 0  # BODGE
        connection_extract['Home_Power'] = connection_extract['Price'] * 0  # BODGE
        total_gas_cost = 0
        total_gas_carbon = 0
    #Valid = connection_extract
    #print(connection_extract['Heating_Power'].sum())
    #print(connection_extract['Carbon Intensity'].mean())
    #print("203")
    return connection_extract, total_gas_cost, total_gas_carbon


def main(inputs, row):
    print('Test ' + str(row + 2) + ' started')
    global charge_rate
    global battery_capacity
    global charger_efficiency
    global plug_in_SoC
    global battery_cost_per_kWh
    global battery_v2g_floor
    global battery_v2g_ceil
    global kWh_export_fee
    global lifetime_ageing_factor
    global max_battery_cycles
    global price_volatility_factor
    global tariff_imp_data
    global tariff_exp_data
    global carbon_intenisty
    global plug_in_time
    global plug_out_time
    global time_resolution
    global vrg_charge_duration
    global v1g_charge_duration
    global battery_mode
    global heating_type
    global gas_price
    global gas_c_intenisty
    global gas_efficiency
    global smart_home
    global case
    global battery_carbon_per_kWh
    global motivation
    global destination_arrival_time
    global solar_connected

    charge_rate = inputs['Charge Rate']  # kW
    battery_capacity = inputs['Battery Capacity']  # kWh
    charger_efficiency = inputs['Charger Efficiency']  # 0.9 for charger UPDATE TO HAVE SEPARATE VALUE FOR CHARGE AND DISCHARGE
    plug_in_SoC = inputs['Plug In SoC']
    battery_cost_per_kWh = inputs['Battery Cost per kWh']  # 137e2
    battery_v2g_floor = inputs['SoC Floor']
    battery_v2g_ceil = inputs['SoC Ceil']
    kWh_export_fee = inputs['kWh Export Fee']  # 4 p
    lifetime_ageing_factor = inputs['Degradation Factor']  # 1
    max_battery_cycles = inputs['Rated Battery Cycles']  # * (1 + 0.625 * lifetime_ageing_factor)  # for TM3, factored to account for factory rating including lifetime degradation 65/40
    price_volatility_factor = inputs['Price Volatility']  # 1
    tariff_imp_data = inputs['Tariff Import Data']  # 'Inputs\AgileExtract.xls'
    tariff_exp_data = inputs['Tariff Export Data']  # 'Inputs\AgileExtract.xls'
    carbon_intenisty = inputs['Carbon Intensity']
    plug_in_time = pd.to_datetime(inputs['Plug In Time'])  # '2019-02-25 19:00:00' Bugged: '2019-07-23 19:00:00'


    time_resolution = pd.Timedelta(inputs['Time Resolution'])
    # vrg_charge_duration = pd.Timedelta('0 h')
    response_true = API.initialise_api_data(inputs, True)
    response_false = API.initialise_api_data(inputs, False)
    opt_response_true = API.initialise_api_data_optimistic(inputs, True)
    opt_response_false = API.initialise_api_data_optimistic(inputs, False)
    vrg_charge_duration = jcharge.time_charge(inputs, response_true, opt_response_true)
    print(vrg_charge_duration)
    v1g_charge_duration = jcharge.time_charge(inputs, response_false, opt_response_false)
    # vrg_charge_duration = pd.Timedelta('30 min')  # CCHHHHHHAAAANNNGGGGGEEEEEEEE LATER TO VALUES FROM ABOVE
    # v1g_charge_duration =  pd.Timedelta('90 min')  # CCHHHHHHAAAANNNGGGGGEEEEEEEE LATER TO VALUES FROM ABOVE
    battery_mode = inputs['Battery Mode']  # EV or Home
    heating_type = inputs['Heating Type']
    gas_price = inputs['Gas Price']  # 3.8 p
    gas_c_intenisty = inputs['Gas Carbon Intensity']  # 3.8 p
    gas_efficiency = inputs['Gas Efficiency']
    smart_home = inputs['Smart Home']
    case = inputs['Case']
    descp = inputs['Description']
    cost_of_change = inputs['Cost of Change']
    carbon_of_change = inputs['Change CO2e']
    battery_carbon_per_kWh = inputs['Battery Carbon per kWh']
    motivation = inputs['Battery Motivation']
    destination_arrival_time = pd.to_datetime(inputs['Destination Arrival Time'])
    solar_connected = inputs['Solar Capability']

    tic = time.time()

    if battery_mode == 'ICE':  # WARNING not obvious but this short circuits the program. Makes all other inputs irrelevant

        response = API.initialise_api_data(inputs, True)

        petrol_cost = jcharge.petrol_cost(inputs, response_false, opt_response_false) + jcharge.petrol_cost(inputs, response_true, opt_response_true)
        petrol_carbon = (jcharge.journey_carbon_cost(inputs, response_false, opt_response_false) + jcharge.journey_carbon_cost(inputs, response_true, opt_response_true))
        # petrol_cost = 100  # CCHHHHHHAAAANNNGGGGGEEEEEEEE LATER TO VALUES FROM ABOVE

        test2year = 52 / 12

        cost_results = [case, cost_of_change,
                        (test2year * petrol_cost / 100),
                        (test2year * petrol_cost / 100),
                        (test2year * petrol_cost / 100),
                        (test2year * petrol_cost / 100),
                        0]

        carbon_results = [case, carbon_of_change,
                          test2year * petrol_carbon,
                          test2year * petrol_carbon,
                          test2year * petrol_carbon,
                          test2year * petrol_carbon,
                          0]

        output = [cost_results, carbon_results]

        toc = time.time()
        # print(' ICE Test ' + str(row + 2) + ' done in {:.4f} seconds'.format(toc - tic))

        return output

    if battery_mode == 'EV':
        plug_out_time = jcharge.plug_out(inputs, response_false)
        # plug_out_time = pd.to_datetime(inputs['Plug Out Time']) # CCHHHHHHAAAANNNGGGGGEEEEEEEE LATER TO VALUES FROM ABOVE
    else:
        plug_out_time = pd.to_datetime(inputs['Plug Out Time'])

    """Main body of code"""
    zeros_charge_schedule, gas_cost, gas_carbon = initialise_charge_schedule(smart_home, heating_type, inputs)
    # plt.plot(zeros_charge_schedule['Home_Power'], label='Home Power')
    # plt.show()

    vrg_charge_schedule = vrg(zeros_charge_schedule, battery_mode)
    vrg_charge_schedule_max = virtual_carbon_cost(virtual_cost(calculate_soc(vrg_max(zeros_charge_schedule.copy(), battery_mode)), 'v1g'), 'v1g')
    v1g_charge_schedule = v1g(vrg_charge_schedule.copy(), battery_mode, motivation)
    v2g_charge_schedule = v2(v1g_charge_schedule.copy(), 'g', motivation)
    v2hg_charge_schedule = v2(v2g_charge_schedule.copy(), 'h', motivation)
    v2h_charge_schedule = v2(v1g_charge_schedule.copy(), 'h', motivation)

    calculate_running_cost(vrg_charge_schedule_max)
    calculate_running_cost(v1g_charge_schedule)
    calculate_running_cost(v2g_charge_schedule)
    calculate_running_cost(v2hg_charge_schedule)
    calculate_running_cost(v2h_charge_schedule)

    calculate_running_carbon(vrg_charge_schedule_max)
    calculate_running_carbon(v1g_charge_schedule)
    calculate_running_carbon(v2g_charge_schedule)
    calculate_running_carbon(v2hg_charge_schedule)
    calculate_running_carbon(v2h_charge_schedule)
    toc = time.time()

    test2year = 52 / 12  # from 12 sample weeks to 52 weeks in a year

    cost_results = [case, cost_of_change,
                    (test2year * (vrg_charge_schedule_max['Running_Cost'].iloc[-1] + gas_cost))/100,
                    (test2year * (v1g_charge_schedule['Running_Cost'].iloc[-1] + gas_cost))/100,
                    (test2year * (v2hg_charge_schedule['Running_Cost'].iloc[-1] + gas_cost))/100,
                    (test2year * (v2h_charge_schedule['Running_Cost'].iloc[-1] + gas_cost))/100,
                    (test2year * ((vrg_charge_schedule_max['Running_Cost'].iloc[-1] - v2h_charge_schedule['Running_Cost'].iloc[-1])))/100]


    carbon_results = [case, carbon_of_change,
                    (test2year * (vrg_charge_schedule_max['Running_Carbon_Cost'].iloc[-1] + gas_carbon))/1000,
                    (test2year * (v1g_charge_schedule['Running_Carbon_Cost'].iloc[-1] + gas_carbon))/1000,
                    (test2year * (v2hg_charge_schedule['Running_Carbon_Cost'].iloc[-1] + gas_carbon))/1000,
                    (test2year * (v2h_charge_schedule['Running_Carbon_Cost'].iloc[-1] + gas_carbon))/1000,
                    (test2year * ((vrg_charge_schedule_max['Running_Carbon_Cost'].iloc[-1] - v2h_charge_schedule['Running_Carbon_Cost'].iloc[-1])))/1000]

    # print('Test ' + str(row) + ' results:')
    # print('VRG virtual cost of connection period: ', vrg_charge_schedule_max['Running_Cost'].iloc[-1] + gas_cost)
    # print('V1G virtual cost of connection period: ', v1g_charge_schedule['Running_Cost'].iloc[-1] + gas_cost)
    # print('V2G virtual cost of connection period: ', v2g_charge_schedule['Running_Cost'].iloc[-1] + gas_cost)
    # print('V2H virtual cost of connection period: ', v2h_charge_schedule['Running_Cost'].iloc[-1] + gas_cost)
    # print('HEMAS savings per day: ',
    #       (vrg_charge_schedule_max['Running_Cost'].iloc[-1] - v2h_charge_schedule['Running_Cost'].iloc[-1]))
    print('Test ' + str(row + 2) + ' done in {:.4f} seconds'.format(toc - tic))
    print('--------------------------------------------------')

    plot_vr12g(vrg_charge_schedule_max, v1g_charge_schedule, v2g_charge_schedule, v2h_charge_schedule, v2hg_charge_schedule, case, row, descp)

    output = [cost_results, carbon_results]

    return output


"""Inputs from researched data. IDEA: make readable as .txt batch files"""
# charge_rate = 7.4  # kW
# battery_capacity = 54  # kWh
# charger_efficiency = 0.9  # 0.9 for charger UPDATE TO HAVE SEPARATE VALUE FOR CHARGE AND DISCHARGE
# plug_in_SoC = 0.2
# battery_cost_per_kWh = 137e2  # 137e2
# battery_v2g_floor = 0.15
# battery_v2g_ceil = 0.9
# kWh_export_fee = 4  # 4 p
# lifetime_ageing_factor = 1  # 1
# max_battery_cycles = 1500 * 1.625  # * (1 + 0.625 * lifetime_ageing_factor)  # for TM3, factored to account for factory rating including lifetime degradation 65/40
# price_volatility_factor = 1  # 1
# # tariff_data = 'Inputs\Fixed22Tariff.csv'  # 'Inputs\AgileExtract.xls'
# # tariff_data = 'Inputs\AgileExtract.csv'  # 'Inputs\AgileExtract.xls'
# tariff_data = 'Inputs\AgileExtract2.csv'  # 'Inputs\AgileExtract.xls'
# plug_in_time = pd.to_datetime('2021-02-21 19:00:00')  # '2019-02-25 19:00:00' Bugged: '2019-07-23 19:00:00'
# plug_out_time = pd.to_datetime('2021-02-26 07:00:00')  # '2019-02-27 07:00:00' Bugged: '2019-07-26 07:00:00'
# time_resolution = pd.Timedelta('15 min')
# vrg_charge_duration = pd.Timedelta('0.5 h')  # 1.6 TO be provided by Yaz's algo to calculate energy from distance  BUG: cannot be -ve
# # v1g_charge_duration = pd.to_timedelta(JourneyCharge.main()[2], 'h')  # 2 TO be provided by Yaz's algo to calculate energy from distance
# v1g_charge_duration = pd.Timedelta('2 h')  # 2 TO be provided by Yaz's algo to calculate energy from distance
# battery_mode = 'Home'  # EV or Home
# heating_type = 'Electric'
# gas_price = 9  # 3.8 p
# gas_efficiency = 0.8
# smart_home = True

# bigtic = time.time()
#
# inputs_table = pd.read_csv('../Inputs/InputSchedule.csv')
# total_tests = inputs_table.shape[0]
# test = range(total_tests)
# to_write = pd.DataFrame(columns=['Case', 'VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net'])
#
# for row in range(inputs_table.shape[0]):
#     charge_rate = inputs_table.loc[row, 'Charge Rate']  # kW
#     battery_capacity = inputs_table.loc[row, 'Battery Capacity']  # kWh
#     charger_efficiency = inputs_table.loc[row, 'Charger Efficiency'] # 0.9 for charger UPDATE TO HAVE SEPARATE VALUE FOR CHARGE AND DISCHARGE
#     plug_in_SoC = inputs_table.loc[row, 'Plug in SoC']
#     battery_cost_per_kWh = inputs_table.loc[row, 'Battery Cost per kWh']  # 137e2
#     battery_v2g_floor = inputs_table.loc[row, 'SoC Floor']
#     battery_v2g_ceil = inputs_table.loc[row, 'SoC Ceil']
#     kWh_export_fee = inputs_table.loc[row, 'kWh Export Fee']  # 4 p
#     lifetime_ageing_factor = inputs_table.loc[row, 'Degradation Factor'] # 1
#     max_battery_cycles = inputs_table.loc[row, 'Rated Battery Cycles']  # * (1 + 0.625 * lifetime_ageing_factor)  # for TM3, factored to account for factory rating including lifetime degradation 65/40
#     price_volatility_factor = inputs_table.loc[row, 'Price Volatility']  # 1
#     # tariff_data = 'Inputs\Fixed22Tariff.csv'  # 'Inputs\AgileExtract.xls'
#     # tariff_data = 'Inputs\AgileExtract.csv'  # 'Inputs\AgileExtract.xls'
#     tariff_imp_data = inputs_table.loc[row, 'Tariff Import Data']  # 'Inputs\AgileExtract.xls'
#     tariff_exp_data = inputs_table.loc[row, 'Tariff Export Data']  # 'Inputs\AgileExtract.xls'
#     plug_in_time = pd.to_datetime(inputs_table.loc[row, 'Arrival Time'])  # '2019-02-25 19:00:00' Bugged: '2019-07-23 19:00:00'
#     plug_out_time = pd.to_datetime(inputs_table.loc[row, 'Departure Time'])  # '2019-02-27 07:00:00' Bugged: '2019-07-26 07:00:00'
#     time_resolution = pd.Timedelta(inputs_table.loc[row, 'Time Resolution'])
#     vrg_charge_duration = pd.Timedelta(inputs_table.loc[row, 'Reserve Charge Duration'])  # 1.6 TO be provided by Yaz's algo to calculate energy from distance  BUG: cannot be -ve
#     # v1g_charge_duration = pd.to_timedelta(JourneyCharge.main()[2], 'h')  # 2 TO be provided by Yaz's algo to calculate energy from distance
#     v1g_charge_duration = pd.Timedelta(inputs_table.loc[row, 'Journey Charge Duration'])  # 2 TO be provided by Yaz's algo to calculate energy from distance
#     battery_mode = inputs_table.loc[row, 'Battery Mode']  # EV or Home
#     heating_type = inputs_table.loc[row, 'Heating Type']
#     gas_price = inputs_table.loc[row, 'Gas Price']  # 3.8 p
#     gas_efficiency = inputs_table.loc[row, 'Gas Efficiency']
#     smart_home = inputs_table.loc[row, 'Smart Home']
#
#     # app_demand_series = ApplianceDemand.main(plug_in_time, plug_out_time)
#     # app_demand_series_frac = app_demand_series.resample(time_resolution).mean()
#     # app_demand_series_frac = app_demand_series_frac/charge_rate
#
#     # plt.plot(app_demand_series)
#     # plt.plot(app_demand_series_avg)
#     # plt.show()
#     tic = time.time()
#
#     """Main body of code"""
#     zeros_charge_schedule, gas_cost = initialise_charge_schedule(smart_home, heating_type)
#
#     # plt.plot(zeros_charge_schedule['Home_Power'], label='Home Power')
#     # plt.show()
#
#     vrg_charge_schedule = vrg(zeros_charge_schedule, battery_mode)
#     vrg_charge_schedule_max = virtual_cost(calculate_soc(vrg_max(zeros_charge_schedule.copy(), battery_mode)), 'v1g')
#     v1g_charge_schedule = v1g(vrg_charge_schedule.copy(), battery_mode)
#     v2g_charge_schedule = v2(v1g_charge_schedule.copy(), 'g')
#     v2h_charge_schedule = v2(v2g_charge_schedule.copy(), 'h')
#     # v2h_charge_schedule = v2h(v1g_charge_schedule.copy())
#
#     calculate_running_cost(vrg_charge_schedule_max)
#     calculate_running_cost(v1g_charge_schedule)
#     calculate_running_cost(v2g_charge_schedule)
#     calculate_running_cost(v2h_charge_schedule)
#     toc = time.time()
#
#     to_write_list = [row,
#                 vrg_charge_schedule_max['Running_Cost'].iloc[-1] + gas_cost,
#                 v1g_charge_schedule['Running_Cost'].iloc[-1] + gas_cost,
#                 v2g_charge_schedule['Running_Cost'].iloc[-1] + gas_cost,
#                 v2h_charge_schedule['Running_Cost'].iloc[-1] + gas_cost,
#                 (vrg_charge_schedule_max['Running_Cost'].iloc[-1] - v2h_charge_schedule['Running_Cost'].iloc[-1])]
#
#     to_write.loc[len(to_write)] = to_write_list
#
#     # with open('my_csv.csv', 'a') as f:
#     #     # to_write.to_csv(f, header='v2h Cost')
#     #     wr = csv.writer(fp, dialect='excel')
#     #     wr.writerrow(to_write)
#
#     print('Test ' + str(row + 1) + '/' + str(total_tests) + ' results:')
#     print('VRG virtual cost of connection period: ', vrg_charge_schedule_max['Running_Cost'].iloc[-1] + gas_cost)
#     print('V1G virtual cost of connection period: ', v1g_charge_schedule['Running_Cost'].iloc[-1] + gas_cost)
#     print('V2G virtual cost of connection period: ', v2g_charge_schedule['Running_Cost'].iloc[-1] + gas_cost)
#     print('V2H virtual cost of connection period: ', v2h_charge_schedule['Running_Cost'].iloc[-1] + gas_cost)
#     print('HEMAS savings per day: ', (vrg_charge_schedule_max['Running_Cost'].iloc[-1] - v2h_charge_schedule['Running_Cost'].iloc[-1]))
#     print('Done in {:.4f} seconds'.format(toc - tic))
#     print('--------------------------------------------------')
#
#     plot_vr12g(vrg_charge_schedule_max, v1g_charge_schedule, v2g_charge_schedule, v2h_charge_schedule, row)
#
# to_write.to_csv('../Results/OutputSchedule.csv')
# bigtoc = time.time()
# print('All done in {:.4f} seconds'.format(bigtoc-bigtic))

