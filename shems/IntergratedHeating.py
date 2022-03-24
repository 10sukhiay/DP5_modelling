import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import numpy as np

def mainElec(arrival_time, departure_time, time_resolution,inputs):
    plt.close('all')
   
    ## Variables ##
    hour_resolution = pd.Timedelta('60 min')
    timeratio = hour_resolution / time_resolution
    time_res = 60 / timeratio

    ## Room Specs ##
    Wall_Height = 2.4;
    Wall_Length = inputs['Wall Length']
    Window_Area = 2;
    No_Windows = inputs['No.Windows']
    Door_Area = 2;
    No_Doors = inputs['No.Doors']    

    Tempno = 0

    OutsideTempData = pd.read_csv(os.getcwd()[:-5] + 'Inputs/HomeGen/Bristoltemp.csv')
    OutsideTempData['Datetime'] = pd.to_datetime(OutsideTempData['Datetime'])
    OutsideTempData = OutsideTempData.set_index("Datetime").resample(time_resolution).interpolate()
    MaskedOutsideTemp = OutsideTempData[arrival_time: departure_time].copy()

    Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
    Inside_Temp = inputs['Inside Temp']
    Inside_Temp_flow = Inside_Temp + 1
    Desired_Temp = inputs['Desired Temp']
    Outside_Temp_Change = Inside_Temp - Outside_Temp
    Time = 0
    Time_Data = []

    Power_df = pd.DataFrame()
    DataElec = pd.DataFrame()
    DataPlot = pd.DataFrame()
    DataPlot1 = pd.DataFrame()

    Total_Window_Area = Window_Area * No_Windows
    Total_Door_Area = Door_Area * No_Doors
    Wall_Area = (Wall_Height * Wall_Length) - Total_Window_Area/4 - Total_Door_Area/4;
    Room_Volume = Wall_Height * Wall_Length * Wall_Length

    ## Energy Needed to heat the room ##
    Density_Air = 1.225
    SHC_Water = 4187
        
    ## Loss through walls,roof and floor ##
    WallU = inputs['Wall U']
    FloorU = 0.22
    RoofU = inputs['Roof U']
    WindowU = 1
    Window_Area = 1.2 * 2
    No_Windows = 4
    DoorU = 2
    Door_Area = 2
    No_Doors = 2
    SmallCorrection = 1
    ## Room heating ##
    PowerRating = inputs['Boiler Rating']
    ShowerTemp = inputs['Water Temp']
    TotalHeatedWater = 0
    TankVolume = inputs['Tank Volume']
    
    total_rows = len(MaskedOutsideTemp)*time_res
    Water = mainShower(arrival_time, departure_time,time_resolution,inputs)
    
    while Time < total_rows:
        if Inside_Temp < Desired_Temp:
            
            Heating = PowerRating 
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            test = 0
            
            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss)
        
            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res 
            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Water
            
            if (Inside_Temp_Heating + Inside_Temp) > Desired_Temp:
                Per_min_Energy = (Desired_Temp - Inside_Temp_flow) * Density_Air * Room_Volume * SHC_Water
                Per_Second_change = Per_min_Energy / 60 / time_res
                Heating = Energy_Loss + Per_Second_change
            else:
                Heating = PowerRating
                
            WaterUse = Water.iloc[Tempno, 0]
            TotalHeatedWater = TotalHeatedWater - int(WaterUse)
            EnergyForWAter =0
            
            DataElec = DataElec.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'test':test, 'Power': Heating, 'EnergyLoss': Energy_Loss,'TotalHeatedWater':TotalHeatedWater,'EnergyForWAter':EnergyForWAter}, ignore_index=True)
            DataPlot = DataPlot.append({'Power': Heating,'TotalHeatedWater':TotalHeatedWater}, ignore_index=True)
            DataPlot1 = DataPlot1.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'Power': Heating}, ignore_index=True)
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df = Power_df.append({'Power': Heating / 1000}, ignore_index=True)
        
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
    
        
        else:
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            test = 1
            EnergyForWAter = 0

            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss)
            
            if Energy_Loss < PowerRating:
                Heating = Energy_Loss
            else:
                Heating = PowerRating
        
            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res 
            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Water
            
            WaterUse = Water.iloc[Tempno, 0]
            TotalHeatedWater = TotalHeatedWater - int(WaterUse)

            if Heating < PowerRating and TotalHeatedWater < TankVolume:
                HeatedWater = (PowerRating - Heating) / (SHC_Water * (ShowerTemp - Outside_Temp))
                HeatedWater = HeatedWater * 60 * time_res 
                WaterCapacity = TankVolume - TotalHeatedWater
                if HeatedWater > WaterCapacity:
                    HeatedWater = WaterCapacity
                    EnergyForWAter = WaterCapacity * SHC_Water * (ShowerTemp - Outside_Temp) / (60*time_res)
                    Heating = Heating + EnergyForWAter
                    test = 1.1
                else:
                    EnergyForWAter = PowerRating - Heating
                    Heating = Heating + EnergyForWAter
                    test = 1.2
                
                TotalHeatedWater = TotalHeatedWater + HeatedWater
            

            DataElec = DataElec.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'test':test, 'Power': Heating, 'EnergyLoss': Energy_Loss,'TotalHeatedWater':TotalHeatedWater,'EnergyForWAter':EnergyForWAter}, ignore_index=True)
            DataPlot = DataPlot.append({'Power': Heating,'TotalHeatedWater':TotalHeatedWater}, ignore_index=True)
            DataPlot1 = DataPlot1.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'Power': Heating}, ignore_index=True)
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df = Power_df.append({'Power': Heating / 1000}, ignore_index=True)
        
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
        
    # Power_df.index = MaskedOutsideTemp.index
    DataElec.index = MaskedOutsideTemp.index
    DataPlot.index = MaskedOutsideTemp.index
    DataPlot1.index = MaskedOutsideTemp.index

    #print(Power_df["Power"].sum()/4)

    DataPlot.plot(secondary_y=['Power'] ).legend(loc='lower left')
    DataPlot1.plot(secondary_y=['Power'] ).legend(loc='lower left')
    plt.legend(loc='upper right')


    #TotalPower = Power_df.sum()
    #print(TotalPower)

    return Power_df

def mainASHP(arrival_time, departure_time, time_resolution,inputs):

    plt.close('all')
    
    global Power_df1
    global DataASHP
        
    ## Room Specs ##
    Wall_Height = 2.4;
    Wall_Length = inputs['Wall Length']
    Window_Area = 2;
    No_Windows = inputs['No.Windows']
    Door_Area = 2;
    No_Doors = inputs['No.Doors']    
    
    hour_resolution = pd.Timedelta('60 min')
    timeratio = hour_resolution / time_resolution

    time_res = 60 / timeratio
    Tempno = 0

    OutsideTempData = pd.read_csv(os.getcwd()[:-5] + 'Inputs/HomeGen/Bristoltemp.csv')
    OutsideTempData['Datetime'] = pd.to_datetime(OutsideTempData['Datetime'])
    OutsideTempData = OutsideTempData.set_index("Datetime").resample(time_resolution).interpolate()
    MaskedOutsideTemp = OutsideTempData[arrival_time: departure_time].copy()

    Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
    Inside_Temp = inputs['Inside Temp']
    Inside_Temp_flow = Inside_Temp + 1
    Desired_Temp = inputs['Desired Temp']
    Outside_Temp_Change = Inside_Temp - Outside_Temp
    Time = 0
    Time_Data = []

    Power_df1 = pd.DataFrame()
    DataASHP = pd.DataFrame()
    DataPlot = pd.DataFrame()
    DataPlot1 = pd.DataFrame()

    Total_Window_Area = Window_Area * No_Windows
    Total_Door_Area = Door_Area * No_Doors
    Wall_Area = (Wall_Height * Wall_Length) - Total_Window_Area/4 - Total_Door_Area/4;
    Room_Volume = Wall_Height * Wall_Length * Wall_Length

    ## Energy Needed to heat the room ##
    Density_Air = 1.225
    SHC_Air = 1000
        
    ## Loss through walls,roof and floor ##
    WallU = inputs['Wall U']
    FloorU = 0.22
    RoofU = inputs['Roof U']
    WindowU = 1.8
    Window_Area = 1.2 * 2
    No_Windows = 4
    DoorU = 3
    Door_Area = 2
    No_Doors = 2
    
    ## Room heating ##
    HeatPump_Rated = inputs['Heatpump Rating']
    HeatPump_Power = HeatPump_Rated
    TotalHeatedWater = 0
    TankVolume = inputs['Tank Volume']
    SHC_Water = 4180
    ShowerTemp = inputs['Water Temp']

    total_rows = len(MaskedOutsideTemp)*time_res
    Water = mainShower(arrival_time, departure_time,time_resolution,inputs)
    
    while Time < total_rows:
        if Inside_Temp < Desired_Temp:
            
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            test = 0
            
            HeatPump_Power = HeatPump_Rated       
            CoP = 1 / (1 - (abs(Outside_Temp / Inside_Temp_flow)))
            if CoP > 5:
                CoP = 5
            if CoP < 0:
                CoP = 0   
            Heating = HeatPump_Power * CoP
            
            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss)

            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res
            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            
            if (Inside_Temp_Heating + Inside_Temp) > Desired_Temp:
                Per_min_Energy = (Desired_Temp - Inside_Temp_flow) * Density_Air * Room_Volume * SHC_Air
                Per_Second_change = Per_min_Energy / (60 * time_res)
                Heating = Per_Second_change + Energy_Loss
                HeatPump_Power = (Energy_Loss + Per_Second_change)/CoP
                test = 2.3
                Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            else:
                Heating = HeatPump_Power * CoP 
                test = 2.4
                if CoP < 0.001:
                    CoP = 0.1
                    Heating = HeatPump_Power * CoP 
            
            WaterUse = Water.iloc[Tempno, 0]
            TotalHeatedWater = TotalHeatedWater - int(WaterUse)
            EnergyForWAter = 0
            HeatPump_PowerTot = HeatPump_Power  
        
            DataASHP = DataASHP.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'test':test, 'Power': HeatPump_Power,'Heating':Heating, 'EnergyLoss': Energy_Loss, 'Increasetemp':Inside_Temp_Heating,'CoP':CoP,'TotalHeatedWater':TotalHeatedWater}, ignore_index=True)
            DataPlot = DataPlot.append({'Power': EnergyForWAter,'TotalHeatedWater':TotalHeatedWater}, ignore_index=True)
            DataPlot1 = DataPlot1.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'HeatPump_Power': HeatPump_Power,'Total_Power':HeatPump_PowerTot, 'Water_Power': EnergyForWAter}, ignore_index=True)
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df1 = Power_df1.append({'Total Power': HeatPump_PowerTot  / 1000}, ignore_index=True)
        
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
            
        else:

            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0]
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            test = 1
            EnergyForWAter = 0
            
            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss)

            CoP = 1 / (1 - abs((Outside_Temp / Inside_Temp_flow)))
            if CoP > 5:
                CoP = 5
            if CoP < 0:
                CoP = 0  
            Heating = HeatPump_Rated * CoP 
       
            Heating = Energy_Loss 
            HeatPump_Power = Energy_Loss / CoP  
            if Outside_Temp > Inside_Temp_flow:
                HeatPump_Power = 0
            test = 1.14
            
            WaterUse = Water.iloc[Tempno, 0]
            TotalHeatedWater = TotalHeatedWater - int(WaterUse)
                        
            if TotalHeatedWater < TankVolume:
                HeatedWater = (HeatPump_Rated - HeatPump_Power) / (SHC_Water * (ShowerTemp - Outside_Temp))
                HeatedWater = HeatedWater * 60 * time_res 
                WaterCapacity = TankVolume - TotalHeatedWater
                if HeatedWater > WaterCapacity:
                    HeatedWater = WaterCapacity
                    EnergyForWAter = WaterCapacity * SHC_Water * (ShowerTemp - Outside_Temp) / (60*time_res)
                    HeatPump_PowerTot = HeatPump_Power + EnergyForWAter
                    test = 1.1
                else:
                    EnergyForWAter = HeatPump_Rated - HeatPump_Power
                    HeatPump_PowerTot = HeatPump_Power + EnergyForWAter
                    
                TotalHeatedWater = TotalHeatedWater + HeatedWater   
            else:
               EnergyForWAter = 0
               HeatPump_PowerTot = HeatPump_Power + EnergyForWAter                   
            
            if HeatPump_Power > HeatPump_Rated:
                Heating = HeatPump_Rated * CoP
                HeatPump_Power = HeatPump_Rated
                test = 1.2
                HeatedWater = 0
                TotalHeatedWater = TotalHeatedWater + HeatedWater

            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res

            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            
            
            DataASHP = DataASHP.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'test':test, 'Power': HeatPump_Power,'Heating':Heating, 'EnergyLoss': Energy_Loss, 'Increasetemp':Inside_Temp_Heating,'CoP':CoP,'TotalHeatedWater':TotalHeatedWater}, ignore_index=True)
            DataPlot = DataPlot.append({'Power': EnergyForWAter,'TotalHeatedWater':TotalHeatedWater}, ignore_index=True)
            DataPlot1 = DataPlot1.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'HeatPump_Power': HeatPump_Power,'Total_Power':HeatPump_PowerTot, 'Water_Power': EnergyForWAter}, ignore_index=True)
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df1 = Power_df1.append({'Total Power': HeatPump_PowerTot / 1000}, ignore_index=True)
        
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
        
    Power_df1.index = MaskedOutsideTemp.index
    DataASHP.index = MaskedOutsideTemp.index
    DataPlot.index = MaskedOutsideTemp.index
    DataPlot1.index = MaskedOutsideTemp.index

    #print(Power_df1["Total Power"].sum())
    DataPlot.plot(secondary_y=['Power'] ).legend(loc='lower left')
    DataPlot1.plot(secondary_y=['Total_Power','HeatPump_Power','Water_Power'] ).legend(loc='lower left')
    plt.legend(loc='upper right')
    
    # TotalPower = Power_df1.sum() / timeratio
    # print(TotalPower)
    
    return Power_df1

def mainGSHP(arrival_time, departure_time, time_resolution,inputs):

    plt.close('all')

    hour_resolution = pd.Timedelta('60 min')
    timeratio = hour_resolution / time_resolution
    time_res = 60 / timeratio
        
    ## Room Specs ##
    Wall_Height = 2.4;
    Wall_Length = inputs['Wall Length']
    Window_Area = 2;
    No_Windows = inputs['No.Windows']
    Door_Area = 2;
    No_Doors = inputs['No.Doors']     

    Tempno = 0

    OutsideTempData = pd.read_csv(os.getcwd()[:-5] + 'Inputs/HomeGen/Bristoltemp.csv')
    OutsideTempData['Datetime'] = pd.to_datetime(OutsideTempData['Datetime'])
    OutsideTempData = OutsideTempData.set_index("Datetime").resample(time_resolution).interpolate()
    MaskedOutsideTemp = OutsideTempData[arrival_time: departure_time].copy()

    Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0] + 1
    Inside_Temp = inputs['Inside Temp']
    Inside_Temp_flow = Inside_Temp+1
    Desired_Temp = inputs['Desired Temp']
    Outside_Temp_Change = Inside_Temp - Outside_Temp
    Time = 0
    Time_Data = []

    Power_df2 = pd.DataFrame()
    DataGSHP = pd.DataFrame()
    DataPlot = pd.DataFrame()
    DataPlot1 = pd.DataFrame()

    Total_Window_Area = Window_Area * No_Windows
    Total_Door_Area = Door_Area * No_Doors
    Wall_Area = (Wall_Height * Wall_Length) - Total_Window_Area/4 - Total_Door_Area/4;
    Room_Volume = Wall_Height * Wall_Length * Wall_Length

    ## Energy Needed to heat the room ##
    Density_Air = 1.225
    SHC_Air = 1000
        
    ## Loss through walls,roof and floor ##
    WallU = inputs['Wall U']
    FloorU = 0.22
    RoofU = inputs['Roof U']
    WindowU = 1.8
    Window_Area = 1.2 * 2
    No_Windows = 4
    DoorU = 3
    Door_Area = 2
    No_Doors = 2
    
    ## Room heating ##
    HeatPump_Rated = inputs['Heatpump Rating']
    HeatPump_Power = HeatPump_Rated
    TotalHeatedWater = 0
    TankVolume = inputs['Tank Volume']
    SHC_Water = 4180
    ShowerTemp = inputs['Water Temp']

    total_rows = len(MaskedOutsideTemp)*time_res
    Water = mainShower(arrival_time, departure_time,time_resolution,inputs)
    
    while Time < total_rows:
        if Inside_Temp < Desired_Temp:
            
            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0] + 1
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            test = 0
            
            HeatPump_Power = HeatPump_Rated       
            CoP = 1 / (1 - (abs(Outside_Temp / Inside_Temp_flow)))
            if CoP > 5:
                CoP = 5
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
            
            if (Inside_Temp_Heating + Inside_Temp) > Desired_Temp:
                Per_min_Energy = (Desired_Temp - Inside_Temp_flow) * Density_Air * Room_Volume * SHC_Air
                Per_Second_change = Per_min_Energy / (60 * time_res)
                Heating = Per_Second_change + Energy_Loss
                HeatPump_Power = (Energy_Loss + Per_Second_change)/CoP
                test = 2.3
                Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            else:
                Heating = HeatPump_Power * CoP 
                test = 2.4
                if CoP < 0.001:
                    CoP = 0.01
                    Heating = HeatPump_Power * CoP 
             
            WaterUse = Water.iloc[Tempno, 0]
            TotalHeatedWater = TotalHeatedWater - int(WaterUse)
            EnergyForWAter = 0
            HeatPump_PowerTot = HeatPump_Power
        
            DataGSHP = DataGSHP.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'test':test, 'Power': HeatPump_Power,'Heating':Heating, 'EnergyLoss': Energy_Loss, 'Increasetemp':Inside_Temp_Heating,'CoP':CoP,'TotalHeatedWater':TotalHeatedWater}, ignore_index=True)
            DataPlot = DataPlot.append({'Power': EnergyForWAter,'TotalHeatedWater':TotalHeatedWater}, ignore_index=True)
            DataPlot1 = DataPlot1.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'HeatPump_Power': HeatPump_Power,'Total_Power':HeatPump_PowerTot, 'Water_Power': EnergyForWAter}, ignore_index=True)
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df2 = Power_df2.append({'Total Power': HeatPump_PowerTot / 1000}, ignore_index=True)
        
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
            
        else:

            Outside_Temp = MaskedOutsideTemp.iloc[Tempno, 0] + 1
            Outside_Temp_Change = Inside_Temp - Outside_Temp
            test = 1
            EnergyForWAter = 0
            
            Wall_Loss = WallU * (Wall_Area * 4) * Outside_Temp_Change
            Floor_Loss = FloorU * (Wall_Length * 2) * Outside_Temp_Change
            Roof_Loss = RoofU * (Wall_Length * 2) * Outside_Temp_Change
            Window_Loss = WindowU * (Window_Area * No_Windows) * Outside_Temp_Change
            Door_Loss = DoorU * (Door_Area * No_Doors) * Outside_Temp_Change
            Energy_Loss = (Wall_Loss + Floor_Loss + Roof_Loss + Window_Loss + Door_Loss) * 1.1

            CoP = 1 / (1 - (abs(Outside_Temp / Inside_Temp_flow)))
            if CoP > 5:
                CoP = 5
            if CoP < 0:
                CoP = 0  
            Heating = HeatPump_Rated * CoP 
       
            Heating = Energy_Loss 
            HeatPump_Power = Energy_Loss / CoP  
            if Outside_Temp > Inside_Temp_flow:
                HeatPump_Power = 0
            test = 1.14
            
            WaterUse = Water.iloc[Tempno, 0]
            TotalHeatedWater = TotalHeatedWater - int(WaterUse)
                        
            if TotalHeatedWater < TankVolume:
                HeatedWater = (HeatPump_Rated - HeatPump_Power) / (SHC_Water * (ShowerTemp - Outside_Temp))
                HeatedWater = HeatedWater * 60 * time_res 
                WaterCapacity = TankVolume - TotalHeatedWater
                if HeatedWater > WaterCapacity:
                    HeatedWater = WaterCapacity
                    EnergyForWAter = WaterCapacity * SHC_Water * (ShowerTemp - Outside_Temp) / (60*time_res)
                    HeatPump_PowerTot = HeatPump_Power + EnergyForWAter
                    test = 1.1
                else:
                    EnergyForWAter = HeatPump_Rated - HeatPump_Power
                    HeatPump_PowerTot = HeatPump_Power + EnergyForWAter
                                
                TotalHeatedWater = TotalHeatedWater + HeatedWater   
            else:
                EnergyForWAter = 0
                HeatPump_PowerTot = HeatPump_Power + EnergyForWAter
           
            if HeatPump_Power > HeatPump_Rated:
                Heating = HeatPump_Rated * CoP
                HeatPump_Power = HeatPump_Rated
                test = 1.2
                HeatedWater = 0
                TotalHeatedWater = TotalHeatedWater + HeatedWater

            Per_Second_change = Heating - Energy_Loss
            Per_min_Energy = Per_Second_change * 60 * time_res

            Inside_Temp_Heating = (Per_min_Energy) / (Density_Air * Room_Volume) / SHC_Air
            
            
            DataGSHP = DataGSHP.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'test':test, 'Power': HeatPump_Power,'Heating':Heating, 'EnergyLoss': Energy_Loss, 'Increasetemp':Inside_Temp_Heating,'CoP':CoP,'TotalHeatedWater':TotalHeatedWater}, ignore_index=True)
            DataPlot = DataPlot.append({'Power': EnergyForWAter,'TotalHeatedWater':TotalHeatedWater}, ignore_index=True)
            DataPlot1 = DataPlot1.append({'OutsideTemp':Outside_Temp,'InsideTemp':Inside_Temp,'HeatPump_Power': HeatPump_Power,'Total_Power':HeatPump_PowerTot, 'Water_Power': EnergyForWAter}, ignore_index=True)
            Time = Time + time_res
            Time_Data.append(Time)
            Tempno = Tempno + 1
            Power_df2 = Power_df2.append({'Total Power': HeatPump_PowerTot / 1000}, ignore_index=True)
        
            Inside_Temp = Inside_Temp + Inside_Temp_Heating
        
    Power_df2.index = MaskedOutsideTemp.index
    DataGSHP.index = MaskedOutsideTemp.index
    DataPlot.index = MaskedOutsideTemp.index
    DataPlot1.index = MaskedOutsideTemp.index

    #print(Power_df2["Total Power"].sum())
    #DataPlot.plot(secondary_y=['Power'] ).legend(loc='lower left')
    DataPlot1.plot(secondary_y=['Total_Power','HeatPump_Power','Water_Power'] ).legend(loc='lower left')
    plt.legend(loc='upper right')
    
    # TotalPower = Power_df2.sum()
    # print(TotalPower)
    
    return Power_df2

def mainShower(arrival_time, departure_time,time_resolution,inputs):
    global ShowerPower
    NoOfShowers = inputs['No. of Showers']
    WaterPerShower = inputs['Water per Shower ']
    
    app_data = 'Inputs/Typical_home_demand.xls'
    app_demand = pd.read_excel(os.getcwd()[:-5] + app_data)
    date_time_index = pd.date_range(arrival_time, departure_time + time_resolution, freq=time_resolution)
    ShowerPower = pd.DataFrame(0, index=date_time_index, columns=['Power'])
    dates = list(set(date_time_index.date))
        
    for index, row in app_demand.iterrows():
        if row['Device'] == 'Shower':
            for day in dates:
                time_on = pd.to_datetime(str(day) + ' ' + str(row['Time On']))
                ShowerPower.loc[time_on: time_on , 'Power'] += row['Power']
    ShowerPower = ShowerPower * WaterPerShower * NoOfShowers
        
    return ShowerPower
