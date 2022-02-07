import pandas as pd
import matplotlib.pyplot as plt
import os

def main(arrival_time, departure_time, time_resolution):
   
     ## Variables ##
     #arrival_time = pd.to_datetime('2019-02-25 19:00:00')  # '2019-02-25 19:00:00' Bugged: '2019-07-23 19:00:00'
     #departure_time = pd.to_datetime('2019-02-26 07:00:00')  # '2019-02-27 07:00:00' Bugged: '2019-07-26 07:00:00'
     #time_resolution = pd.Timedelta('15 min')

    ## Room Specs ##
    Wall_Height = 2.4;
    Wall_Length = 8.3;
    Window_Area = 2;
    No_Windows = 10;
    Door_Area = 2;
    No_Doors = 3;    

    time_res = 15
    Tempno = 0
    
    OutsideTempData = pd.read_excel(os.getcwd()[:-5] + 'Inputs\HomeGen\Temp1.xls', parse_dates=[0], index_col=0).resample(time_resolution).interpolate()
    MaskedOutsideTemp = OutsideTempData[arrival_time: departure_time].copy()

    Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
    Inside_Temp = 18
    Desired_Temp = 24
    Inside_Temp_Change = Desired_Temp - Inside_Temp
    Outside_Temp_Change = Inside_Temp - Outside_Temp
    Temp_Data = []
    Time = 0
    Time_Data = []
    Energy_Data = []
    

    Power_df = pd.DataFrame(columns=['Power'])

    Total_Window_Area = Window_Area * No_Windows
    Total_Door_Area = Door_Area * No_Doors
    Wall_Area = (Wall_Height * Wall_Length) - Total_Window_Area/4 - Total_Door_Area/4;
    Room_Volume = Wall_Height * Wall_Length * Wall_Length

    ## Energy Needed to heat the room ##
    Density_Air = 1.225
    SHC_Air = 1000
        
    ## Loss through walls,roof and floor ##
    WallU = 0.3
    FloorU = 0.22
    RoofU = 0.16
    WindowU = 1.8
    Window_Area = 1.2 * 2
    No_Windows = 4
    DoorU = 3
    Door_Area = 2
    No_Doors = 2
    
    
    ## Room heating ##
    Heating = 1000

    total_rows = len(MaskedOutsideTemp)*time_res
    
    while Time < total_rows:
        if Inside_Temp < Desired_Temp:
            
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            
            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss) * 1.1
        
        
            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res
            
            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
        
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df = Power_df.append({'Power': Heating / 1000}, ignore_index=True)
        
        else:
            Heating = Energy_Loss

<<<<<<< HEAD
        Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
        Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
        Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
        Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
        Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss) * 1.1
=======
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
            Outside_Temp_Change = Inside_Temp - Outside_Temp

            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss) * 1.1
>>>>>>> main

            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res

            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            Inside_Temp = Inside_Temp + Inside_Temp_Heating

            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df = Power_df.append({'Power': Heating / 1000}, ignore_index=True)
        
    Power_df.index = MaskedOutsideTemp.index
    return Power_df


