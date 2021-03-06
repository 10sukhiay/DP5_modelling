import pandas as pd
import matplotlib.pyplot as plt
import os


def main(arrival_time, departure_time, time_resolution, inputs):

    Solar_Panel_Area = 1.4
    Space_From_Edge = 0.5
    System_Efficency = 0.85
    Roof_Height = inputs['Roof Height']
    Roof_Length = inputs['Roof Width']

    ## Roof Calcs ##
    Area_of_Roof = Roof_Height * Roof_Length
    No_of_Panels = round((Area_of_Roof-((2*Roof_Height*Space_From_Edge)+(2*Roof_Length*Space_From_Edge)))/Solar_Panel_Area)
    Panel_Area = No_of_Panels*Solar_Panel_Area

    hour_resolution = pd.Timedelta('60 min')
    hour_ratio = hour_resolution / time_resolution

    IrradianceData1 = pd.read_csv(os.getcwd()[:-5] + 'Inputs/HomeGen/Bristol4.csv')
    IrradianceData1['Datetime'] = pd.to_datetime(IrradianceData1['Datetime'])
    IrradianceData1 = IrradianceData1.set_index("Datetime").resample(time_resolution)
    IrradianceData1 = IrradianceData1.interpolate()
    MaskedIrradiance = IrradianceData1[arrival_time: departure_time].copy()

    Temperature = pd.read_csv(os.getcwd()[:-5] + 'Inputs/HomeGen/Bristoltemp.csv')
    Temperature['Datetime'] = pd.to_datetime(Temperature['Datetime'])
    Temperature = Temperature.set_index("Datetime").resample(time_resolution).interpolate()
    MaskedTemp = Temperature[arrival_time: departure_time].copy()

    #Temperature = pd.read_excel(os.getcwd()[:-5] + 'Inputs/HomeGen/Temp1.xls', parse_dates=[0], index_col=0).resample(time_resolution).interpolate()
    #MaskedTemp = Temperature[arrival_time: departure_time].copy() # .resample(time_resolution).pad()  # .iloc[:-1, :]
    VaryTemp = (MaskedTemp - 25) * 0.00045

    Panel_Efficency = MaskedTemp.copy()
    Panel_Efficency  = 0.17 * Panel_Efficency/Panel_Efficency

    TempCoeff = Panel_Efficency - VaryTemp
    Month_Area = MaskedIrradiance * Panel_Area
    Time_Generation = Month_Area * System_Efficency * TempCoeff.values / 1000
    Time_Total = Time_Generation.sum() / hour_ratio
    return Time_Generation.values

# Generation_Text ='Your gerneration over this period could be ', int(Time_Total), 'kWhs';
# print(Generation_Text)
#
# plt.plot(Time_Generation['Irrad'])
# plt.show()
