import ChargeController
import pandas as pd
from multiprocessing import Pool
import time
from joblib import Parallel, delayed
import os


def run_series():
    bigtic = time.time()

    inputs_table = pd.read_csv('../Inputs/InputSchedule.csv')
    total_tests = inputs_table.shape[0]
    test = range(total_tests)
    results = pd.DataFrame(columns=['Case', 'VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net'])

    for row in range(inputs_table.shape[0]):
        results.loc[len(results)] = ChargeController.main(inputs_table.loc[row, :], row)

    results.to_csv('../Results/OutputScheduleSeries.csv')

    bigtoc = time.time()
    print('Series done in {:.4f} seconds'.format(bigtoc - bigtic))
    return results


def run_multi():
    bigtic = time.time()

    inputs_table = pd.read_csv('../Inputs/InputSchedule.csv')
    result = Parallel(n_jobs=10)(delayed(ChargeController.main)(inputs_table.loc[row, :], row) for row in range(inputs_table.shape[0]))
    results = pd.DataFrame(result, columns=['Case', 'VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net'])
    results.to_csv('../Results/OutputScheduleMulti.csv')

    bigtoc = time.time()
    print('Multi done in {:.4f} seconds'.format(bigtoc - bigtic))
    return results


def pcs(TBM_results):
    test = set(TBM_results['Case'])
    for case in test:
        case_mask = TBM_results['Case'] == case
        total_savings = (case_mask*TBM_results['HEMAS Net']).sum()
    return total_savings

results = run_multi()
print(pcs(results))

