# -*- coding: utf-8 -*-
"""This code computes the coefficient of variation (CV) and some other stats for small samples (indicated by the * added to CV)
for a given set of measurements which are assumed to be for the same or similar object, using the same measurand.
Stats are adjusted for small sample size. Paper ref: Belz, Popovic & Mille (2022) Quantified Reproducibility Assessment of NLP Results,
ACL'22.

In this self-contained version, the set of measurements on which CV is computed is assigned to the variable set_of_set_of_measurements
(see examples in code below).

The reproducibility stats reported in the output are:
* the unbiased coefficient of variation
* the sample mean
* the unbiased sample standard deviation with 95% confidence intervals, estimated on the basis of the standard error of the unbiassed sample variance
* the sample size
* the percentage of measured valued within two standard deviations
* the percentage of measured valued within one standard deviation

Example narrative output:

The unbiased coefficient of variation is 1.5616560359100269 \
for a mean of 85.58285714285714 , \
unbiased sample standard deviation of 1.2904233075765223 with 95\% CI (0.4514829817654973, 2.1293636333875474) ,\
and a sample size of 7 . \
100.0 % of measured values fall within two standard deviations. \
71.429 % of measured values fall within one standard deviation.

NOTE:
* CV assumes all measurements are positive; if they're not, shift measurement scale to start at 0
* for fair comparison across studies, measurements on a scale that doesn't start at 0 need to be shifted to a scale that does start at 0

KNOWN ISSUES:

none
"""

import math
import numpy as np
import pandas as pd
from scipy.stats import t


def get_precision_results(set_of_measurements):
    if len(set_of_measurements) < 2:
        raise ValueError(set_of_measurements, ": set of measurements is smaller than 2")

    sample_mean = np.mean(set_of_measurements)
    if sample_mean <= 0:
        raise ValueError(set_of_measurements, ": mean is 0 or negative")

    sample_size = len(set_of_measurements)
    degrees_of_freedom = sample_size - 1
    sum_of_squared_differences = np.sum(np.square(sample_mean - set_of_measurements))

    # unbiassed sample variance s^2
    unbiassed_sample_variance = sum_of_squared_differences / degrees_of_freedom
    # corrected sample standard deviation s
    corrected_sample_standard_deviation = np.sqrt(unbiassed_sample_variance)
    # Gamma(N/2)
    gamma_N_over_2 = math.gamma(sample_size / 2)
    # Gamma((N-1)/2)
    gamma_df_over_2 = math.gamma(degrees_of_freedom / 2)
    # c_4(N)
    c_4_N = math.sqrt(2 / degrees_of_freedom) * gamma_N_over_2 / gamma_df_over_2
    # unbiassed sample std dev s/c_4
    unbiassed_sample_std_dev_s_c_4 = corrected_sample_standard_deviation / c_4_N
    # standard error of the unbiassed sample variance (assumes normally distributed population)
    standard_error_of_unbiassed_sample_variance = unbiassed_sample_variance * np.sqrt(2 / degrees_of_freedom)
    # estimated std err of std dev based on std err of unbiassed sample variance
    est_SE_of_SD_based_on_SE_of_unbiassed_sample_variance = standard_error_of_unbiassed_sample_variance / (
            2 * unbiassed_sample_std_dev_s_c_4)

    # COEFFICIENT OF VARIATION CV
    coefficient_of_variation = (unbiassed_sample_std_dev_s_c_4 / sample_mean) * 100
    # SMALL SAMPLE CORRECTED COEFFICIENT OF VARIATION CV*
    small_sample_coefficient_of_variation = (1 + (1 / (4 * sample_size))) * coefficient_of_variation

    # compute percentage of measured values within 1 and 2 standard deviations from the mean
    # initialise counts
    count_within_1_sd = 0
    count_within_2_sd = 0
    # for each measured value
    for m in set_of_measurements:
        # if it's within two std devs, increment count_within_2_sd
        if np.abs(m - sample_mean) < 2 * unbiassed_sample_std_dev_s_c_4:
            count_within_2_sd += 1
            # if it's also within one std devs, increment count_within_1_sd
            if np.abs(m - sample_mean) < unbiassed_sample_std_dev_s_c_4:
                count_within_1_sd += 1

    result_dict = {
        "sample size": sample_size,
        "mean": sample_mean,
        "unbiased stdev": unbiassed_sample_std_dev_s_c_4,
        "stdev 95% CI": "[{:.2f}, {:.2f}]".format(
            *t.interval(0.95, degrees_of_freedom, loc=unbiassed_sample_std_dev_s_c_4,
                        scale=est_SE_of_SD_based_on_SE_of_unbiassed_sample_variance)),
        "CV*": small_sample_coefficient_of_variation,
        # "% of measured values within two standard deviations": count_within_2_sd / sample_size * 100,
        # "% of measured values within one standard deviations": count_within_1_sd / sample_size * 100,
    }
    return result_dict


def main():
    # measurements from Belz et al. (2022)
    set_of_set_of_measurements = [[84.51, 84.5, 87.46, 85.6, 84.2, 86.61, 86.2, 84.51, 86.53, 88.81],
                                  # [30.65, 30.65, 29.13, 30.65, 29.96, 30.65, 29.96, 30.23],
                                  # [87.5, 80.75, 89.36, 88.1, 89.64, 88.8, 87.5, 89.4, 89.12, 88.01, 89.43, 87.04],
                                  # [31.11, 30.28, 31.11, 29.12, 31.11, 29.12, 29.58, 29.18, 29.8, 29.7]
                                  ]
    # --- Table 4: BLEU scores for 7 NTS_def repros ---
    # set_of_set_of_measurements = [[84.51, 84.50, 87.46, 85.60, 84.20, 86.61, 86.20]]  # 7, NTS_def, BLEU
    # --- Table 4: SARI scores for 5 NTS_def repros ---
    # set_of_set_of_measurements = [[30.65, 30.65, 29.13, 30.65, 29.96]] # 5, NTS_def, SARI
    # --- Table 4: BLEU scores for 6 NTS-w2v_def repros ---
    # set_of_set_of_measurements = [[87.50, 80.75, 89.36, 88.10, 89.64, 88.80]] # 6, NTS-w2v_def, BLEU
    # --- Table 4: SARI scores for 4 NTS_w2v_def repros ---
    # set_of_set_of_measurements = [[31.11, 30.28, 31.11, 29.12]] # 4, NTS-w2v_def, SARI
    # --- Table 5: blue highlights (i.e. subsets of BLEU scores from above where outputs were reused, not regenerated) ---
    # set_of_set_of_measurements = [[84.51, 84.50, 85.60, 84.20]] # 7, NTS_def, BLEU
    # set_of_set_of_measurements = [[87.50, 89.36, 88.10]] # 6, NTS-w2v_def, BLEU
    # --- Section 4.1, fourth paragraph: subset of scores where outputs were regenerated and Nisioi's BLEU script was used
    # set_of_set_of_measurements = [[84.51, 87.46, 86.61], # 7, NTS_def, BLEU
    #                              [30.65, 29.13, 29.96], # 5, NTS_def, SARI
    #                              [87.50, 80.75, 89.64], # 6, NTS-w2v_def, BLEU
    #                              [31.11, 30.28, 29.12]] # 4, NTS-w2v_def, SARI
    # --- Table 6: wF1 scores for 11 system variants ---
    # set_of_set_of_measurements = [[0.428, 0.493, 0.426, 0.574, 0.579, 0.590, 0.574, 0.600],
    #                              [0.721, 0.603, 0.605, 0.606, 0.720, 0.732, 0.606, 0.740],
    #                              [0.719, 0.604, 0.607, 0.607, 0.723, 0.733, 0.607, 0.736],
    #                              [0.726, 0.681, 0.680, 0.680, 0.722, 0.728, 0.680, 0.732],
    #                              [0.724, 0.680, 0.680, 0.681, 0.725, 0.729, 0.681, 0.731],
    #                              [0.703, 0.660, 0.650, 0.651, 0.699, 0.711, 0.651, 0.710],
    #                              [0.693, 0.661, 0.652, 0.653, 0.699, 0.712, 0.653, 0.716],
    #                              [0.449, 0.600, 0.433, 0.597, 0.635, 0.646, 0.597, 0.698],
    #                              [0.471, 0.647, 0.447, 0.647, 0.696, 0.711, 0.647, 0.726],
    #                              [0.693, 0.658, 0.683, 0.668, 0.692, 0.689, 0.659, 0.391],
    #                              [0.689, 0.662, 0.681, 0.659, 0.681, 0.684, 0.657, 0.401]]

    for set_of_measurements in set_of_set_of_measurements:
        if len(set_of_measurements) < 2:
            print(set_of_measurements, ": set of measurements is smaller than 2")
            break

        sample_mean = np.mean(set_of_measurements)
        if sample_mean <= 0:
            print(set_of_measurements, ": mean is 0 or negative")
            break

        sample_size = len(set_of_measurements)
        degrees_of_freedom = sample_size - 1
        sum_of_squared_differences = np.sum(np.square(sample_mean - set_of_measurements))

        # unbiassed sample variance s^2
        unbiassed_sample_variance = sum_of_squared_differences / degrees_of_freedom
        # corrected sample standard deviation s
        corrected_sample_standard_deviation = np.sqrt(unbiassed_sample_variance)
        # Gamma(N/2)
        gamma_N_over_2 = math.gamma(sample_size / 2)
        # Gamma((N-1)/2)
        gamma_df_over_2 = math.gamma(degrees_of_freedom / 2)
        # c_4(N)
        c_4_N = math.sqrt(2 / degrees_of_freedom) * gamma_N_over_2 / gamma_df_over_2
        # unbiassed sample std dev s/c_4
        unbiassed_sample_std_dev_s_c_4 = corrected_sample_standard_deviation / c_4_N
        # standard error of the unbiassed sample variance (assumes normally distributed population)
        standard_error_of_unbiassed_sample_variance = unbiassed_sample_variance * np.sqrt(2 / degrees_of_freedom)
        # estimated std err of std dev based on std err of unbiassed sample variance
        est_SE_of_SD_based_on_SE_of_unbiassed_sample_variance = standard_error_of_unbiassed_sample_variance / (
                2 * unbiassed_sample_std_dev_s_c_4)

        # COEFFICIENT OF VARIATION CV
        coefficient_of_variation = (unbiassed_sample_std_dev_s_c_4 / sample_mean) * 100
        # SMALL SAMPLE CORRECTED COEFFICIENT OF VARIATION CV*
        small_sample_coefficient_of_variation = (1 + (1 / (4 * sample_size))) * coefficient_of_variation

        # compute percentage of measured values within 1 and 2 standard deviations from the mean
        # initialise counts
        count_within_1_sd = 0
        count_within_2_sd = 0
        # for each measured value
        for m in set_of_measurements:
            # if it's within two std devs, increment count_within_2_sd
            if np.abs(m - sample_mean) < 2 * unbiassed_sample_std_dev_s_c_4:
                count_within_2_sd += 1
                # if it's also within one std devs, increment count_within_1_sd
                if np.abs(m - sample_mean) < unbiassed_sample_std_dev_s_c_4:
                    count_within_1_sd += 1

        # report results as described in code description above
        print("The unbiased coefficient of variation is", round(small_sample_coefficient_of_variation, 2))
        print("for a mean of", sample_mean, ", ")
        print("unbiased sample standard deviation of", round(unbiassed_sample_std_dev_s_c_4, 2),
              ", with 95% CI [{:.2f}, {:.2f}]".format(
                  *t.interval(0.95, degrees_of_freedom, loc=unbiassed_sample_std_dev_s_c_4,
                              scale=est_SE_of_SD_based_on_SE_of_unbiassed_sample_variance))
              , ",")
        print("and a sample size of", sample_size, ".")
        print(count_within_2_sd / sample_size * 100, "% of measured values fall within two standard deviations.")
        print(round(count_within_1_sd / sample_size * 100, 3),
              "% of measured values fall within one standard deviation.", )
        print("-------")


if __name__ == "__main__":
    # results_dict = {
    #     "bert-base": [5.78882882435848, 9.9],
    #     "reasonbertr": [34.796348398236205, 41.3],
    #     "reasonbertb": [5.819215474870902, 33.2],
    #     "sspt": [4.923973911007985, 10.8],
    #     "spanbert": [10.073525781680853, 15.7],
    #     # "": [, ],
    #     # "": [, ],
    #
    # }

    results_dict = {
        "E-SNLI": [87.723, 90.52],
        # "reasonbertr": [34.796348398236205, 41.3],
        # "reasonbertb": [5.819215474870902, 33.2],
        # "sspt": [4.923973911007985, 10.8],
        # "spanbert": [10.073525781680853, 15.7],
        # "": [, ],
        # "": [, ],

    }


    full_result_list = []
    for key, values in results_dict.items():

        precision_results = get_precision_results(values)
        precision_results["model"] = key
        precision_results["Ours"] = values[0]
        precision_results["Reported"] = values[1]
        full_result_list.append(precision_results)
    df = pd.DataFrame(full_result_list)
    # 10.3
    # 10.26
    # 33.2
    # 34.79
    main()
