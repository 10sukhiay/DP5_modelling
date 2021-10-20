import pandas as pd
import numpy as np

## Variables ##
DayIndex = list(range(1, 25));
MonthIndex = list(range(0, 12));

Solar_Panel_Area = 1.4;
Space_From_Edge = 0.5;
Panel_Capacity = 250;
Panel_Efficency =  0.17 * pd.DataFrame(np.ones((12, 24)))
Panel_Efficency.index = MonthIndex;
Panel_Efficency.columns = DayIndex;
System_Efficency = 0.85;

## Roof Inputs ##
Previous_Solar = 0;

if Previous_Solar == '0':
    Roof_Height = 4;
    Roof_Length = 6;

    ## Roof Calcs ##
    Area_of_Roof = Roof_Height * Roof_Length;
    No_of_Panels = round((Area_of_Roof-((2*Roof_Height*Space_From_Edge)+(2*Roof_Length*Space_From_Edge)))/Solar_Panel_Area);
    Panel_Area = No_of_Panels*Solar_Panel_Area;
    Roof_Capacity = No_of_Panels*Panel_Capacity/1000;
    RoofCapacity = ['You can fit ',str(No_of_Panels),' panels on your roof, with a capacity of ', str(Roof_Capacity), ' kW'];
    print(RoofCapacity)
else:
    Panel_Area = int(Previous_Solar) * 4 * Solar_Panel_Area;
    Roof_Capacity = 0; 


## Irradiance Data ##
Location = 1;
if Location == 0 :
    Irr = pd.read_excel("Plymouth.xlsx");
elif Location == 1 :
    Irr = pd.read_excel("Bristol.xlsx");
elif Location == 2 :
    Irr = pd.read_excel("London.xlsx");
elif Location == 3 :
    Irr = pd.read_excel("Birmingham.xlsx");
elif Location == 4 :
    Irr = pd.read_excel("Manchester.xlsx");
elif Location == 5 :
    Irr = pd.read_excel("Newcastle.xlsx");
elif Location == 6 :
    Irr = pd.read_excel("Glasgow.xlsx");
elif Location == 7 :
    Irr = pd.read_excel("Inverness.xlsx");

VariationEffects = pd.DataFrame(np.random.randint(-10,10,size=(12, 24)))/100;
VariationEffects += 1;      
VariationEffects.columns = DayIndex;

Irr_PanelAngle_0 = Irr.loc[0:11,:];
Irr_PanelAngle_35 = Irr.loc[12:23,:];
Irr_PanelAngle_50 = Irr.loc[24:35,:];

Irr_PanelAngle_35.index = MonthIndex;
Irr_PanelAngle_50.index = MonthIndex;

Irr_PanelAngle_0 = Irr_PanelAngle_0 * VariationEffects;
Irr_PanelAngle_35 = Irr_PanelAngle_35 * VariationEffects;
Irr_PanelAngle_50 = Irr_PanelAngle_50 * VariationEffects;   

Roof_Pitch = 1;
if Roof_Pitch == 0:
    MonthIrr = Irr_PanelAngle_0;
elif Roof_Pitch == 1:
    MonthIrr = Irr_PanelAngle_35;
elif Roof_Pitch == 2:
    MonthIrr = Irr_PanelAngle_50;
else :
    MonthIrr = Irr_PanelAngle_35;

## Temp ##
Temperature = pd.read_excel("Temp.xlsx");
VaryTemp = Temperature - 25;
VaryTemp = VaryTemp * 0.00045;

TempCoeff = Panel_Efficency - VaryTemp;

## Generation Calcs ##
Days_In_Month = np.array([31,28,31,30,31,30,31,31,30,31,30,31]);
Month_Area = MonthIrr * Panel_Area;
Month_Efficency = Month_Area * TempCoeff * System_Efficency;
Month_Total = Month_Efficency.mul(Days_In_Month,axis=0)/1000
Month_Totals = Month_Total.sum(axis=1);
Average_Month_Tot = Month_Totals.mean(axis = 0); 
Year_Generation = sum(Month_Totals);

Generation_Text =['Your yearly gerneration could be ', str(Year_Generation), 'kWhs'];
print(Generation_Text)

## Traiff inputs ##
Home_Use = 3400;
if Home_Use == '':
     Home_Use = 3400;

HomeUseFactor = int(Home_Use)/3400;

## Real Tarrif ## 
Tarifs = pd.read_excel("Tarifs.xlsx")
TariffOut= Tarifs.loc[0:11,:]/100;
TariffIn= Tarifs.loc[12:24,:]/100;
TariffIn.index = MonthIndex;

Yealy_Wind_Resource = 1;
if Yealy_Wind_Resource == '0':
    TariffOut = 1.1 * TariffOut;
    TariffIn = 1.1 * TariffIn;
elif Yealy_Wind_Resource == '2':
    TariffOut = 0.9 * TariffOut;
    TariffIn = 0.9 * TariffIn;


AverageTarrifIn = (TariffIn.mean(axis = 0)).mean(axis = 0); 

HouseUse = pd.read_excel("HouseUse.xlsx")
HomeUse =  HomeUseFactor * HouseUse;

SolarGenLessHomeUse = Month_Total - HomeUse; 
PrePanelHome = HomeUse * TariffIn;
PrePanelHome = PrePanelHome.sum(); 
PrePanelHome = PrePanelHome.sum(); 

## EV fuel Savings ##

Car_Milage = 12000;
if Car_Milage == '':
    Car_Milage = 12000;
else:
    Car_Milage = int(Car_Milage);


Car_MPG = 22.2;
if Car_MPG == '':
     Car_KmperL = 22.2;
else:  
    Car_KmperL = int(Car_MPG) * 0.425144;         

Fuel_Cost = 1.2;

EV_KmperKW = 0.19;
if EV_KmperKW == '':
     EV_KwhperKm = 0.19;
else:
    EV_KmperKW = int(EV_KmperKW);

MonthTemp = Temperature.mean(axis = 0)
EVTempLosses =((round(MonthTemp - 4))/100)+1;

Car_Fuel_Cost = (Car_Milage / Car_KmperL) * Fuel_Cost;
EV_Fuel_Total = (Car_Milage/12) * EV_KwhperKm * EVTempLosses;
EV_Fuel_Total_sum = sum(EV_Fuel_Total);
EV_Fuel_Total_NoSolar = sum(EV_Fuel_Total * AverageTarrifIn);
Fuel_Cost_Difference = (Car_Fuel_Cost - EV_Fuel_Total_NoSolar);

WFHHours = 20;
WFHCharging = Car_Milage/12 * EV_KwhperKm / WFHHours;

SolarLessHomeEV = SolarGenLessHomeUse;
print(SolarLessHomeEV);

for i in range(1, 9):
    SolarLessHomeEV[i] -= WFHCharging;

for i in range(11, 16):
    SolarLessHomeEV[i] -= WFHCharging;

for i in range(17, 24):
    SolarLessHomeEV[i] -= WFHCharging;
    
print(SolarLessHomeEV);

## Traiff Calcs ##
#TotalTarif = pd.DataFrame(np.ones((12, 24)))

#for rowIndex, row in SolarLessHomeEV.iterrows(): 
#    for columnIndex, value in row.items():
#        if  SolarLessHomeEV[rowIndex,columnIndex] < '0':
#             TotalTarif[rowIndex,columnIndex] = SolarLessHomeEV[rowIndex,columnIndex] * TariffIn[rowIndex,columnIndex];
#        else:
#            TotalTarif[rowIndex,columnIndex] = SolarLessHomeEV[rowIndex,columnIndex] * TariffOut[rowIndex,columnIndex];

#Diff_Usage = round(Year_Generation - EV_Fuel_Total_sum);
#CarandHome = Car_Fuel_Cost + PrePanelHome;
#Total_Saved = (Car_Fuel_Cost + PrePanelHome) + sum(sum(TotalTarif));
#x=['Your yearly savings could be £', str(round(Total_Saved)),', to charge your car at home and use ',str(Diff_Usage),' kWh at home'];
#print(x)