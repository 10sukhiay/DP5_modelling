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

    inputs_table = pd.read_excel('../Inputs/InputScheduleBC.xlsx')
    # inputs_table = pd.read_csv('../Inputs/InputSchedule.csv')
    results = Parallel(n_jobs=10)(delayed(ChargeController.main)(inputs_table.loc[row, :], row) for row in range(inputs_table.shape[0]))
    flat_list = [item for sublist in results for item in sublist]  # yet another bodge
    cost_result = flat_list[::2]
    carbon_result = flat_list[1::2]
    # test2 = result[0, :]

    cost_results = pd.DataFrame(cost_result, columns=['Case', 'Cost of Change', 'VRG Cost', 'V1G Cost', 'V2G Cost', 'VRH Cost', 'HEMAS Net'])
    cost_results.to_csv('../Results/OutputScheduleMultiCost.csv')

    carbon_results = pd.DataFrame(carbon_result, columns=['Case', 'Carbon of Change', 'VRG Carbon', 'V1G Carbon', 'V2G Carbon', 'VRH Carbon', 'HEMAS Net'])
    carbon_results.to_csv('../Results/OutputScheduleMultiCO2.csv')


    bigtoc = time.time()
    print('Multi done in {:.4f} seconds'.format(bigtoc - bigtic))
    return cost_results, carbon_results


def pcs(TBM_results, mode):

    PCS_returns = pd.DataFrame(columns=['Case', 'VRG ' + mode, 'V1G ' + mode, 'V2G ' + mode, 'VRH ' + mode, 'HEMAS Net', mode + ' of Change'])

    for case in set(TBM_results['Case']):
        case_mask = TBM_results['Case'] == case
        PCS_return = TBM_results.loc[case_mask, :].sum()
        PCS_cost = TBM_results.loc[case_mask, mode + ' of Change'].mean()
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
    change_cost = all_values[mode + ' of Change']

    PCS_annum_difference = datum_values - all_values + 0.000001  # BODGE to avoid /0 error
    PCS_five_years = (5 * all_values).add(change_cost.tolist(), axis='index')

    PCSrecip = 1 / PCS_annum_difference
    PCS_payback_years = PCSrecip.mul(change_cost, axis=0)

    PCS_payback_years.rename({'VRG ' + mode: 'VRG Payback', 'V1G ' + mode: 'V1G Payback', 'V2G ' + mode: 'V2G Payback', 'VRH ' + mode: 'VRH Payback'}, axis=1, inplace=True)
    PCS_five_years.rename({'VRG ' + mode: 'VRG 5yr', 'V1G ' + mode: 'V1G 5yr', 'V2G ' + mode: 'V2G 5yr', 'VRH ' + mode: 'VRH 5yr'}, axis=1, inplace=True)
    # test4 = test.div(PCS_payback, axis=0)

    PCS_results = pd.concat([PCS_returns, PCS_payback_years.iloc[:, :-2]], axis=1)
    PCS_results = pd.concat([PCS_results, PCS_five_years.iloc[:, :-2]], axis=1)

    PCS_results.to_csv('../Results/PCSResults' + mode + '.csv')

    return PCS_results

# results = run_series()  # use for debug
cost_results, carbon_results = run_multi()
PCS_cost_results = pcs(cost_results, 'Cost')
PCS_carbon_results = pcs(carbon_results, 'Carbon')
print(PCS_cost_results)

