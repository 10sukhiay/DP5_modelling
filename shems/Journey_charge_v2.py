"""
Calculates the necessary charge requirement to complete a specified journey
Each journey is defined by characteristics which are variable in Inputs_Journey file

Yazad Sukhia
Feb 2022
"""

# import required packages for use
import time
import pandas as pd
import Inputs_Journey_v2 as inp
import API_tests as API
import os
# import matplotlib as plt


def main():
    start_time = time.time()
    inputs = pd.read_excel('../Inputs/Yaz_Journey_API_inputs_data.xlsx').iloc[0, :]
    results_journey(inputs, False)
    charge_time = time_charge(inputs, False)
    # print(charge_time)
    # display_results() # this is added after display_results() has been formed
    end_time = time.time()
    print('Completed in {:.4f} seconds'.format(end_time - start_time))
    return charge_time


"""
The following functions are developed specifically to calculate values called by the charge controller that inform 
elements of the charging logic. Individual functions contain descriptions of functionality; while below a brief outline 
of how charging logic is affected by the calculated values is explained 
 
    plug_out        --- defines the time at which the controller must charge to the calculated energy requirement for 
                        each specified journey  
    time_charge     --- defines the minimum amount of time that must be spent charging in order to charge to the 
                        required level for each specified journey 
"""


def plug_out(inputs, reserve_journey):
    """Calculates when the charge controller must stop charging by. This is an estimated plug out time based on the user
    input desired time to arrive at their specified travel destination and the API estimated time for this journey to be
    completed"""
    destination_arrival_time = pd.to_datetime(inputs['Destination Arrival Time'])
    plug_out_time = destination_arrival_time - API.journey_time_traffic(inputs, reserve_journey)
    return plug_out_time


def time_charge(inputs, reserve_journey):
    """Calculates the time that will be needed to charge to the required level for each specified journey, based on the
    required charge calculation and the charge rate of the controller used (outlined in the user inputs)"""
    final_charge_kwh = final_kwh(inputs, reserve_journey)
    charge_time = pd.Timedelta(str(final_charge_kwh / inputs['Charge Rate']) + 'h')
    return charge_time


"""
The following functions are developed to work out the individual effect a range of specified journey characteristics 
have on the total charge requirement of an EV. The effects of defined journey characteristics are variable based 
broadly on two main categories 

    personal variation between users    --- includes the use of HVAC (Heating, Ventilation, Air Conditioning) systems 
                                            driving style (EFFICIENT, MODERATE, AGGRESSIVE)
                                            the use of regenerative braking systems                              
    external environment                --- includes external factors such as weather conditions (precipitation) and 
                                            temperature variation between different journeys 

While personal variation between users is either set up through the input file or as an inferred effect of the external
environment [e.g. HVAC use is dependant on how hot / cold it is outside], the state of the external environment is 
provided by historical data and is read based on a user input for date of journey. Data sources are as follows 
    
    Precipitation                        --- https://www.metoffice.gov.uk/hadobs/hadukp/data/download.html
                                             Met Office Data 
    External Temperature                 ---
"""


def heating(inputs, reserve_journey):
    """Calculates relative effect that use of heating systems will have on charge requirement. Use of heating is set at
    a threshold level and is assumed to be "ON" when external temperature is below 7°C. This can be changed by adapting
    the IFS conditional statement in the 'Inputs/HomeGen/Temp1.xls' file. Uses input plug_out_time to find external
    temperature at the time of journey"""
    plug_out_time = plug_out(inputs, reserve_journey)
    td = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Temp1.xls', parse_dates=[0], index_col=0)
    heat = td[plug_out_time.replace(year=2019):plug_out_time.replace(year=2019) + pd.Timedelta('1 h')].copy().iloc[0, 1]
    if heat == "ON":
        heat_effect = 0.85
    else:
        heat_effect = 1
    return heat_effect


def cooling(inputs, reserve_journey):
    """Calculates relative effect that use of cooling systems will have on charge requirement. Use of cooling is set at
    a threshold level and is assumed to be "ON" when external temperature is above 20°C. This can be changed by adapting
    the IFS conditional statement in the 'Inputs/HomeGen/Temp1.xls' file. Uses input plug_out_time to find external
    temperature at the time of journey"""
    plug_out_time = plug_out(inputs, reserve_journey)
    td = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Temp1.xls', parse_dates=[0], index_col=0)
    cool = td[plug_out_time.replace(year=2019):plug_out_time.replace(year=2019) + pd.Timedelta('1 h')].copy().iloc[0, 2]
    if cool == "ON":
        cool_effect = 0.83
    else:
        cool_effect = 1
    return cool_effect


def rain(inputs, reserve_journey):
    """Calculates relative effect that levels of precipitation will have on charge requirement. Uses input plug_out_time
    to find precipitation level at the time of journey. Severity is classified in banded groups ranging from NONE,
    LIGHT, MILD, HEAVY"""
    plug_out_time = plug_out(inputs, reserve_journey)
    precipdata = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Precipitation_data_uk_2021.xlsx', parse_dates=[0], index_col=0)
    rain_effect = precipdata[plug_out_time.replace(year=2021):plug_out_time.replace(year=2021) + pd.Timedelta('1 day')].copy().iloc[0, 1]
    return rain_effect


def temp(inputs, reserve_journey):
    """Calculates relative effect that the external ambient temperature will have on charge requirement. Uses input
    plug_out_time to find temperature level at the time of journey"""
    plug_out_time = plug_out(inputs, reserve_journey)
    td = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Temp1.xls', parse_dates=[0], index_col=0)
    temperature = td[plug_out_time.replace(year=2019):plug_out_time.replace(year=2019) + pd.Timedelta('1 h')].copy().iloc[0, 0]
    # temp = TempData[plug_out_time:plug_out_time + pd.Timedelta('1 h')].copy().iloc[0, 0]
    # temp = inputs['Temperature']
    if temperature < 23:
        temp_effect = (1-((23-temperature) * 0.0033))
    else:
        temp_effect = 1
    return temp_effect


"""
The following functions are developed to work out the amount of charge that a user-specified journey will require to 
complete. Trip distance is calculated by a google maps API called from the API_tests script and requires an input origin
and destination, while EV characteristics are initially set by manufacture specifications
"""


def charge_p_range(inputs):
    """Defines the initial estimated amount of charge required for the selected EV type to move 1km. This is calculated
    directly from manufacture quoted vehicle characteristics"""
    charge_per_range = float(inputs['Battery Capacity']) / float(inputs['Vehicle Range'])
    return charge_per_range


def init_charge(inputs, reserve_journey):
    """Calculates the initial charge required to complete the specified journey input"""
    trip_distance = API.journey_distance(inputs, reserve_journey)
    charge_per_range = charge_p_range(inputs)
    capacity = inputs['Battery Capacity']
    init_charge_req = ((charge_per_range * trip_distance) / capacity) * 100
    return init_charge_req


def shift_charge(inputs, reserve_journey):
    """Calculates a shifted charge requirement based on the calculated effects of individual journey characteristics"""
    heat_effect = heating(inputs, reserve_journey)
    cool_effect = cooling(inputs, reserve_journey)
    rain_effect = rain(inputs, reserve_journey)
    temp_effect = temp(inputs, reserve_journey)
    range_shift = (heat_effect * cool_effect * inputs['Driving Style'] * inputs["Regen Braking"] * rain_effect * temp_effect)
    # print(inp.rain[1])
    # print(inp.heating[0])
    # print(inp.cooling[0])
    # print(inp.style[0])
    # print(inp.regen[1])
    apply_r_shift = (1/range_shift)
    init_charge_req = init_charge(inputs, reserve_journey)
    shift_charge_req = init_charge_req * apply_r_shift
    return shift_charge_req


def charge_add(inputs):
    """Calculates an additional energy requirement to complete a journey based on elevation change along the journey"""
    delta_h = inputs['Distance up'] - inputs['Distance down']  # This can be read from the input excel file eventually
    capacity = inputs['Battery Capacity']
    mass = inputs['Vehicle Mass']
    if delta_h > 0:
        energy_j = delta_h * mass * 9.81
        energy_kwh = energy_j / 3600000
        add_charge = ((energy_kwh / capacity) * 100)
    else:
        add_charge = 0
    return add_charge


"""
The following functions are developed to call the group of functions above and simplify any requests the charge 
controller makes for the energy requirement of a journey
"""


def final_charge(inputs, reserve_journey):
    """Calculates the total energy requirement for a given EV journey based on defined journey characteristics as a % of
    the total battery capacity of the vehicle"""
    shift_charge_req = shift_charge(inputs, reserve_journey)
    add_charge = charge_add(inputs)
    charge_final = shift_charge_req + add_charge
    return charge_final


def final_kwh(inputs, reserve_journey):
    """Converts the final charge requirement calculated in final_charge from a percentage into a kWh requirement"""
    final_charge_percent = final_charge(inputs, reserve_journey)
    final_charge_kwh = (final_charge_percent / 100) * inputs['Battery Capacity']
    return final_charge_kwh


def results_journey(inputs, reserve_journey):
    """Presents and prints the final results in the terminal"""
    final_charge_percent = round(final_charge(inputs, reserve_journey), 2)
    print(final_charge_percent, "% of total capacity required to charge")
    final_charge_kwh = round((final_charge_percent / 100) * inputs['Battery Capacity'], 2)
    print("This is equivalent to", final_charge_kwh, "kWh")
    charge_time = round(final_charge_kwh / inputs['Charge Rate'], 2)
    print("Therefore", charge_time, "hours are needed to charge to requirement using a", inputs['Charge Rate'], "kW charger")
    pounds_saved = journey_savings(inputs, reserve_journey)
    print('£', pounds_saved, 'on this journey saved with this EV selection')
    return


"""
The following functions are developed to evaluate the cost of individual journeys in terms of both:

    Financial Cost (£)          ---   
    Carbon Cost (Kg Co2)        ---  
    
"""


def petrol_cost(inputs, reserve_journey):
    """Determines what the cost of fuel would be for the duration of the specified journey assuming an ICE is used"""
    plug_out_time = plug_out(inputs, reserve_journey)
    petrol_price_data = pd.read_excel(os.getcwd()[:-5] + 'Inputs/2021_data_petrol_price.xlsx', parse_dates=[0], index_col=0)
    p_per_litre = petrol_price_data[plug_out_time.replace(year=2021):plug_out_time.replace(year=2021) + pd.Timedelta(days=7)].copy().iloc[0, 0]
    l_per_km = (2.35215 / inputs['MPG'])  # in litres per km
    petrol_consump_rate = l_per_km
    petrol_cost = p_per_litre     # CAN USE inputs['p per litre'] INSTEAD FROM INPUT FILE
    petrol_p_per_km = petrol_consump_rate * petrol_cost
    journey_petrol_price = API.journey_distance(inputs, reserve_journey) * petrol_p_per_km
    return journey_petrol_price


def journey_carbon_cost(inputs, reserve_journey):
    """Determines the Co2 used (in kg) during the specified journey based on the mass of fuel required to complete the
    journey assuming an ICE is used"""
    l_per_km = (2.35215 / inputs['MPG'])  # in litres per km
    petrol_consump_rate = l_per_km
    kg_carbon_per_litre = inputs['Carbon Kg per litre Fuel']
    petrol_co2_per_km = petrol_consump_rate * kg_carbon_per_litre
    journey_co2_price = round(API.journey_distance(inputs, reserve_journey) * petrol_co2_per_km, 2)
    return journey_co2_price


def journey_cost(inputs, reserve_journey):
    """Determines the cost any journey specified; toggles between vehicle selections; where vehicle_select = 1 & 2 refer
    to EVs while = 3 refers to the use of an ICE"""
    journey_price = 0
    vehicle_select = inputs['Vehicle Type']
    petrol_cost = inputs['p per litre']
    l_per_km = (2.35215 / inputs['MPG'])
    petrol_consump_rate = l_per_km
    elec_cost = inp.kwh_cost
    if vehicle_select == 1 or vehicle_select == 2:
        final_charge_kwh = final_kwh(inputs, reserve_journey)
        journey_price = final_charge_kwh * elec_cost
    elif vehicle_select == 3:
        petrol_p_per_km = petrol_consump_rate * petrol_cost
        journey_price = API.journey_distance(inputs, reserve_journey) * petrol_p_per_km
    return journey_price


def journey_savings(inputs, reserve_journey):
    """Based on the vehicle selected, will calculate a potential cost saving between the selection and an ICE. In the
    case of an ICE being selected for the journey, savings will return £0."""
    trip_cost = journey_cost(inputs, reserve_journey)
    journey_petrol_price = petrol_cost(inputs, reserve_journey)
    trip_savings = round(((journey_petrol_price - trip_cost) / 100), 2)
    return trip_savings


# def display_results():
# TO COMPLETE LATER- USE WHEN DISPLAYING RESULTS FOR INDIVIDUAL SECTION


if __name__ == "__main__":
    main()
