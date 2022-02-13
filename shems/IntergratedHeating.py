import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import numpy as np

def mainElec(arrival_time, departure_time, time_resolution):
   
    ## Variables ##
    #arrival_time = pd.to_datetime('2019-02-25 19:00:00')  # '2019-02-25 19:00:00' Bugged: '2019-07-23 19:00:00'
    #departure_time = pd.to_datetime('2019-02-26 07:00:00')  # '2019-02-27 07:00:00' Bugged: '2019-07-26 07:00:00'
    #time_resolution = pd.Timedelta('15 min')
    hour_resolution = pd.Timedelta('60 min')
    timeratio = hour_resolution / time_resolution
    global DataElec
    global Power_df
    global TotalPower
    ## Room Specs ##
    Wall_Height = 2.4;
    Wall_Length = 10;
    Window_Area = 2;
    No_Windows = 10;
    Door_Area = 2;
    No_Doors = 3;    

    time_res = 5
    Tempno = 0
    
    OutsideTempData = pd.read_excel(os.getcwd()[:-5] + 'Inputs\HomeGen\Temp1.xls', parse_dates=[0], index_col=0).resample(time_resolution).interpolate()
    MaskedOutsideTemp = OutsideTempData[arrival_time: departure_time].copy()

    Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
    Inside_Temp = 15
    Desired_Temp = 21
    Inside_Temp_Change = Desired_Temp - Inside_Temp
    Outside_Temp_Change = Inside_Temp - Outside_Temp
    Temp_Data = []
    Time = 0
    Time_Data = []
    Energy_Data = []
    

    Power_df = pd.DataFrame(columns=['Power'])
    DataElec = pd.DataFrame()

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
    

    total_rows = len(MaskedOutsideTemp)*time_res
    
    while Time < total_rows:
        if Inside_Temp < Desired_Temp:
            
            Heating = 1000
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            test = 0
            
            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss) * 1.1
        
            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res
            
            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            
            DataElec = DataElec.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'test':test, 'Power': Heating, 'EnergyLoss': Energy_Loss}, ignore_index=True)
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df = Power_df.append({'Power': Heating / 1000}, ignore_index=True)
        
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
    
        
        else:
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            test = 1

            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss) * 1.1
            
            if Energy_Loss < 1000:
                Heating = Energy_Loss
            else:
                Heating = 1000
        
            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res
            
            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air

            DataElec = DataElec.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'test':test, 'Power': Heating, 'EnergyLoss': Energy_Loss}, ignore_index=True)
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df = Power_df.append({'Power': Heating / 1000}, ignore_index=True)
        
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
        
    Power_df.index = MaskedOutsideTemp.index
    DataElec.index = MaskedOutsideTemp.index
    #PowerTot = Data['Power'].sum()/1000/timeratio
    #print (PowerTot)
<<<<<<< Updated upstream
    return Power_df.values
=======
    
    #ShowerPower = mainShower(arrival_time, departure_time)
    #TotalPower =  Power_df["Power"] + ShowerPower["Power"]
    #TotalPower = TotalPower.dropna()
    
    return Power_df
>>>>>>> Stashed changes

def mainASHP(arrival_time, departure_time, time_resolution):

    hour_resolution = pd.Timedelta('60 min')
    timeratio = hour_resolution / time_resolution
    global Power_df1
        
    ## Room Specs ##
    Wall_Height = 2.4;
    Wall_Length = 10;
    Window_Area = 2;
    No_Windows = 10;
    Door_Area = 2;
    No_Doors = 3;    

    time_res = 5
    Tempno = 0
    
    OutsideTempData = pd.read_excel(os.getcwd()[:-5] + 'Inputs\HomeGen\Temp1.xls', parse_dates=[0], index_col=0).resample(time_resolution).interpolate()
    MaskedOutsideTemp = OutsideTempData[arrival_time: departure_time].copy()

    Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
    Inside_Temp = 15
    Desired_Temp = 21
    Inside_Temp_Change = Desired_Temp - Inside_Temp
    Outside_Temp_Change = Inside_Temp - Outside_Temp
    Temp_Data = []
    Time = 0
    Time_Data = []
    Energy_Data = []
    

    Power_df1 = pd.DataFrame(columns=['Power'])
    DataASHP = pd.DataFrame()

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
    HeatPump_Rated = 1000
    HeatPump_Power = HeatPump_Rated

    total_rows = len(MaskedOutsideTemp)*time_res
    
    while Time < total_rows:
        if Inside_Temp < Desired_Temp:
            
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            test = 0
            
            HeatPump_Power = 1000       
            CoP = 1 / (1 - (Outside_Temp / Inside_Temp))
            if CoP > 3:
                CoP = 3
            if CoP < 0:
                CoP = 0   
            Heating = HeatPump_Power * CoP
            
            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss) * 1.1
        
            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res
            
            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            #Water_Heating = 0
        
            DataASHP = DataASHP.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'test':test, 'Power': HeatPump_Power,'Heating':Heating, 'EnergyLoss': Energy_Loss, 'Increasetemp':Inside_Temp_Heating,'CoP':CoP,'Water_Heating':Water_Heating}, ignore_index=True)
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df1 = Power_df1.append({'Power': HeatPump_Power / 1000}, ignore_index=True)
        
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
            
        else:

            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            test = 1
            
            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss) * 1.1

            SmallCorrection = 0.95
            CoP = 1 / (1 - (Outside_Temp / Inside_Temp)) 
            if CoP > 3:
                CoP = 3
            if CoP < 0:
                CoP = 0  
            Heating = HeatPump_Rated * CoP * SmallCorrection
       
            Heating = Energy_Loss * SmallCorrection
            HeatPump_Power = Energy_Loss / CoP  
            test = 1.1
        
            if HeatPump_Power > HeatPump_Rated:
                Heating = HeatPump_Rated * CoP
                HeatPump_Power = HeatPump_Rated
                test = 1.2

            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res

            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            
           # if HeatPump_Power < HeatPump_Rated:
                #Water_Heating = (HeatPump_Rated - HeatPump_Power) * 60 * time_res / 1000
           # else:
                #Water_Heating = 0
                
            
            
            DataASHP = DataASHP.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'test':test, 'Power': HeatPump_Power,'Heating':Heating, 'EnergyLoss': Energy_Loss, 'Increasetemp':Inside_Temp_Heating,'CoP':CoP,'Water_Heating':Water_Heating}, ignore_index=True)
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df1 = Power_df1.append({'Power': Heating / 1000}, ignore_index=True)
        
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
        
    Power_df1.index = MaskedOutsideTemp.index
    DataASHP.index = MaskedOutsideTemp.index

    #ShowerPower = mainShower(arrival_time, departure_time)
    #ShowerPowerMask = ShowerPower/ShowerPower
    #ShowerPowerMask = ShowerPowerMask.fillna(0)
    #TotalPower = ShowerPowerMask * DataASHP['Water_Heating'].values
   #TotalPowerGen = ShowerPowerMask.multiply(DataASHP['Water_Heating'], axis=0)/1000
    #TotalPower = ShowerPower - TotalPowerGen
    Power_df1 = Power_df1 + TotalPower
   #Power_df1 = Power_df1.dropna()
    
    #PowerTot = Data['Power'].sum()/1000/timeratio
    #print (PowerTot)
<<<<<<< Updated upstream
    return Power_df1.values
=======
    return Power_df1

def mainShower(arrival_time, departure_time):
    # arrival_time = pd.to_datetime('2019-02-23 19:15:00')
    # departure_time = pd.to_datetime('2019-02-27 7:00:00')
    
    app_data = 'Inputs\Typical_home_demand.xls'
    app_demand = pd.read_excel(os.getcwd()[:-5] + app_data)
    time_resolution = pd.Timedelta('15 min')
    #time_resolution = pd.Timedelta(app_demand['Duration (h)'].min(), 'h')
    # app_demand_series = pd.date_range(arrival_time, departure_time, freq=time_resolution)
    date_time_index = pd.date_range(arrival_time, departure_time + time_resolution, freq=time_resolution)
    ShowerPower = pd.DataFrame(0, index=date_time_index, columns=['Power'])
    dates = list(set(date_time_index.date))
    
    time_res = 15
    Water = 40
    ShowerWater = Water / (60 / time_res)
    Water_SHC = 4187
    Water_Temp_Change = 40 - 15

    # app_demand_series['Day of Week'] = app_demand_series.index.dayofweek

    for index, row in app_demand.iterrows():
        if row['Device'] == 'Shower':
            for day in dates:
                time_on = pd.to_datetime(str(day) + ' ' + str(row['Time On']))
                time_on = time_on - timedelta(hours=1)
                ShowerPower.loc[time_on: time_on + pd.Timedelta(row[1], 'h'), 'Power'] += row[
                    'Power']
    ShowerPower = ShowerPower * ShowerWater * Water_SHC * Water_Temp_Change / (60*60) / 1000
    print(ShowerPower.sum())
    
            

    # plt.plot(app_demand_series)
    # plt.show()

    return ShowerPower
>>>>>>> Stashed changes
