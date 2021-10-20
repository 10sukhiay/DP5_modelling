import pandas as pd
import openpyxl
import numpy as np
import os
import datetime

arrival_time = datetime.datetime(2019, 2, 25, 19, 15, 00)
departure_time = datetime.datetime(2019, 2, 27, 19, 15, 00)
agile_extract = pd.read_excel(os.getcwd()[:-5] + 'Inputs\AgileExtract.xlsx')

test = 'end'