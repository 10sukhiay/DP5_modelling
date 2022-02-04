import pandas as pd
import matplotlib.pyplot as plt

Solar_Panel_Area = 1.4;
Space_From_Edge = 0.5;
System_Efficency = 0.85;
Roof_Height = 5;
Roof_Length = 6;

## Roof Calcs ##
Area_of_Roof = Roof_Height * Roof_Length;
No_of_Panels = round((Area_of_Roof-((2*Roof_Height*Space_From_Edge)+(2*Roof_Length*Space_From_Edge)))/Solar_Panel_Area);
Panel_Area = No_of_Panels*Solar_Panel_Area;

arrival_time = pd.to_datetime('2019-02-25 19:00:00')
departure_time = pd.to_datetime('2019-02-26 19:00:00')
time_resolution = pd.Timedelta('20 min')
hour_resolution = pd.Timedelta('60 min')
hour_ratio = hour_resolution / time_resolution

IrradianceData = pd.read_excel('Bristoldata.xlsx', parse_dates=[0], index_col=0)
MaskedIrradiance = IrradianceData[arrival_time: departure_time].resample(time_resolution).interpolate().iloc[:-1, :]

## Temp ##

Temperature = pd.read_excel("TempData.xlsx", parse_dates=[0], index_col=0);
Temperature = Temperature.iloc[:,:-1]
MaskedTemp = Temperature[arrival_time: departure_time].resample(time_resolution).pad().iloc[:-1, :]
VaryTemp = (MaskedTemp - 25)* 0.00045;

Panel_Efficency = MaskedTemp.copy()
Panel_Efficency  = 0.17 * Panel_Efficency/Panel_Efficency

TempCoeff = Panel_Efficency - VaryTemp;
Month_Area = MaskedIrradiance * Panel_Area;
Time_Generation = Month_Area * System_Efficency * TempCoeff.values/1000
Time_Total = Time_Generation.sum() / hour_ratio


Generation_Text ='Your gerneration over this period could be ', int(Time_Total), 'kWhs';
print(Generation_Text)

plt.plot(Time_Generation['Irrad'])
plt.show()
