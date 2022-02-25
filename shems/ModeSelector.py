import ChargeController
import pandas as pd
from multiprocessing import Pool
import time
from joblib import Parallel, delayed
import os


def run_series():
    bigtic = time.time()

    inputs_table = pd.read_excel('../Inputs/InputSchedule2.xlsx')
    total_tests = inputs_table.shape[0]
    test = range(total_tests)
    results = pd.DataFrame(columns=['Case', 'Cost of Change', 'VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net'])

    for row in range(inputs_table.shape[0]):
        results.loc[len(results)] = ChargeController.main(inputs_table.loc[row, :], row)

    results.to_csv('../Results/OutputScheduleSeries.csv')

    bigtoc = time.time()
    print('Series done in {:.4f} seconds'.format(bigtoc - bigtic))
    return results


def run_multi():
    bigtic = time.time()

    inputs_table = pd.read_excel('../Inputs/InputSchedule2.xlsx')
    # inputs_table = pd.read_csv('../Inputs/InputSchedule.csv')
    result = Parallel(n_jobs=10)(delayed(ChargeController.main)(inputs_table.loc[row, :], row) for row in range(inputs_table.shape[0]))
    results = pd.DataFrame(result, columns=['Case', 'Cost of Change', 'VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net'])
    results.to_csv('../Results/OutputScheduleMulti.csv')

    bigtoc = time.time()
    print('Multi done in {:.4f} seconds'.format(bigtoc - bigtic))
    return results


def pcs(TBM_results):

    PCS_returns = pd.DataFrame(columns=['Case', 'VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net', 'Cost of Change'])

    for case in set(TBM_results['Case']):
        case_mask = TBM_results['Case'] == case
        PCS_return = TBM_results.loc[case_mask, :].sum()
        PCS_cost = TBM_results.loc[case_mask, 'Cost of Change'].mean()
        PCS_results_list = list(PCS_return[2:])
        # PCS_payback_time = list(PCS_cost/PCS_results_list)

        PCS_results_list.insert(0, case)
        PCS_results_list.append(PCS_cost)
        # PCS_results_list = PCS_results_list + PCS_payback_time

        PCS_returns.loc[len(PCS_returns)] = PCS_results_list

    # PCS_payback_times = pd.DataFrame(columns=['Case', 'VRG Payback', 'V1G Payback', 'V2G Payback', 'VRH Payback', 'HEMAS Payback', 'Cost of Change'])

    datum_mask = PCS_returns['Case'] == 'Datum'
    # other_mask = ~datum_mask
    datum_values = PCS_returns.loc[datum_mask].iloc[:, 1:].values
    # datum_values = datum_values.iloc[:, 1:].values
    # test4 = test2.values
    all_values = PCS_returns.iloc[:, 1:]
    test = all_values['Cost of Change']

    PCS_payback = datum_values - all_values
    test2 = 1 / PCS_payback
    test3 = test2.mul(test, axis=0)
    test3.rename({'VRG Cost': 'VRG Payback', 'V1G Cost': 'V1G Payback', 'V2G Cost': 'V2G Payback', 'VRH Cost': 'VRH Payback'}, axis=1, inplace=True)
    # test4 = test.div(PCS_payback, axis=0)

    PCS_results = pd.concat([PCS_returns, test3.iloc[:, :-2]], axis=1)

    PCS_results.to_csv('../Results/PCSResults.csv')

    return PCS_results

# results = run_series()  # use for debug
results = run_multi()
PCS_results = pcs(results)
print(PCS_results)

