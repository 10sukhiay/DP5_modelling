import pandas as pd
import matplotlib.pyplot as plt
import os

def main(arrival_time, departure_time, time_resolution):
    
    ## Variables ##
    
    ## Room Specs ##
    Wall_Height = 2.4;
    Wall_Length = 8.3;
    Window_Area = 2;
    No_Windows = 10;
    Door_Area = 2;
    No_Doors = 3;    
    
    time_res = 5
    Tempno = 0
    
    OutsideTempData = pd.read_excel(os.getcwd()[:-5] + 'Inputs\HomeGen\Temp1.xls', parse_dates=[0], index_col=0).resample(time_resolution).interpolate()
    MaskedOutsideTemp = OutsideTempData[arrival_time: departure_time].copy()

    Outside_Temp = MaskedOutsideTemp.iloc[Tempno,0];
    Inside_Temp = 18;
    Desired_Temp = 24;
    Inside_Temp_Change = Desired_Temp - Inside_Temp;
    Outside_Temp_Change = Inside_Temp - Outside_Temp;
    Temp_Data = []
    Time = 0
    Time_Data = []
    Power_Data = []
    Energy_Data = []
    
    Total_Window_Area = Window_Area * No_Windows;
    Total_Door_Area = Door_Area * No_Doors;
    Wall_Area = (Wall_Height * Wall_Length) - Total_Window_Area/4 - Total_Door_Area/4;
    Room_Volume = Wall_Height * Wall_Length * Wall_Length;

    ## Energy Needed to heat the room ##
    Density_Air = 1.225;
    SHC_Air = 1000;

    ## Loss through walls,roof and floor ##
    WallU = 0.3;
    FloorU = 0.22;
    RoofU = 0.16;
    WindowU = 1.8;
    DoorU = 3;
    
    
    ## Room heating ##
    Heating = 500;
    
    total_rows = len(MaskedOutsideTemp)*time_res

    while Time < total_rows :
        if Inside_Temp < Desired_Temp:
                
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno,0];
            Outside_Temp_Change = Inside_Temp - Outside_Temp;
            
            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss) * 1.1
            
            Per_Second_change = Heating - Energy_Loss;
            Per_min_Energy = Per_Second_change * 60 * time_res ;
    
            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            Inside_Temp = Inside_Temp + Inside_Temp_Heating;
            
            Energy_Data.append(Per_min_Energy)
            Temp_Data.append(Inside_Temp)
            Time = Time + time_res
            Time_Data.append(Time)
            Power_Data.append(Heating)
            Tempno = Tempno + 1;
        
        else:
            Heating = Energy_Loss
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno,0];
            Outside_Temp_Change = Inside_Temp - Outside_Temp;
    
            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss) * 1.1
    
            Per_Second_change = Heating - Energy_Loss;
            Per_min_Energy = Per_Second_change * 60 * time_res;
    
            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            Inside_Temp = Inside_Temp + Inside_Temp_Heating;
    
            Energy_Data.append(Per_min_Energy)
            Temp_Data.append(Inside_Temp)
            Time = Time + time_res
            Time_Data.append(Time)
            Power_Data.append(Heating)
            Tempno = Tempno + 1;

        Power_Data[0] = Power_Data[1];
        return Power_Data


fig,ax = plt.subplots()
ax.plot(Time_Data, Temp_Data, color="red")
ax.set_xlabel("Time (Min)",fontsize=14)
ax.set_ylabel("Temp oC",fontsize=14)
ax2=ax.twinx()
ax2.plot(Time_Data, Power_Data,color="blue")
ax2.set_ylabel("Power for Heating",fontsize=14)
ax.plot(Time_Data, MaskedOutsideTemp.iloc[:,0],color="green")
plt.show()
