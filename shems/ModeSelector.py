import ChargeController
import pandas as pd
from multiprocessing import Pool
import time
from joblib import Parallel, delayed
import os

# bigtic = time.time()
#
# inputs_table = pd.read_csv('../Inputs/InputSchedule.csv')
# total_tests = inputs_table.shape[0]
# test = range(total_tests)
# results = pd.DataFrame(columns=['VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net'])
#
# for row in range(inputs_table.shape[0]):
#     # test1 = inputs_table.loc[row, :]
#     results.loc[len(results)] = ChargeController.main(inputs_table.loc[row, :], row)
#     # results.loc[len(results)] = result
#
# results.to_csv('../Results/OutputScheduleSeries.csv')
#
# bigtoc = time.time()
# print('Series done in {:.4f} seconds'.format(bigtoc - bigtic))

# bigtic = time.time()
#
# process_list = []
# inputs_table = pd.read_csv('../Inputs/InputSchedule.csv')
# total_tests = inputs_table.shape[0]
# test = range(total_tests)
# results = pd.DataFrame(columns=['VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net'])
#
# pool = Pool(processes=2)
# for row in range(inputs_table.shape[0]):
#     # results.loc[len(results)] = pool.apply_async(func=ChargeController.main, args=inputs_table.loc[row, :])
#     pool.apply_async(func=ChargeController.main, args=inputs_table.loc[row, :])
# print('no way')
# pool.close()
# pool.join()
#
# bigtoc = time.time()
# print('Multi done in {:.4f} seconds'.format(bigtoc - bigtic))

bigtic = time.time()

process_list = []
inputs_table = pd.read_csv('../Inputs/InputSchedule.csv')
total_tests = inputs_table.shape[0]
test = range(total_tests)
results = pd.DataFrame(columns=['VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net'])

result = Parallel(n_jobs=os.cpu_count() - 1)(delayed(ChargeController.main)(inputs_table.loc[row, :], row) for row in range(inputs_table.shape[0]))
results = pd.DataFrame(result, columns=['VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net'])
results.to_csv('../Results/OutputScheduleMulti.csv')

# product_comparison =

bigtoc = time.time()
print('Multi done in {:.4f} seconds'.format(bigtoc - bigtic))