import json
import os
import matplotlib.pyplot as plt
import numpy as np
import re
import random
import argparse
import datetime
import pandas as pd
import requests
import csv

import argparse
import concurrent
import csv
import json
import logging
import os
import time
from builtins import enumerate
from concurrent import futures

import bibtexparser
import bs4
import requests
import requests.utils
from bs4 import BeautifulSoup
from tqdm import tqdm
import functools
import seaborn as sns

MAJOR_CONFERENCES_ABBREVIATION_DICT = {
    "Annual Meeting of the Association for Computational Linguistics": "ACL",
    "Conference on Empirical Methods in Natural Language Processing": "EMNLP",
    # "European Chapter of the Association for Computational Linguistics": "EACL",
    "North American Chapter of the Association for Computational Linguistics": "NAACL",
    # "International Joint Conference on Natural Language Processing": "IJCNLP",
    "International Conference on Computational Linguistics": "COLING",
    "Language Resources and Evaluation": "LREC",
    "Findings of the Association for Computational Linguistics: ACL": "ACL",
    "Findings of the Association for Computational Linguistics: EMNLP": "EMNLP",
}


def load_anthology(file_name):
    with open(file_name) as f:
        acl_anthology_data = json.load(f)
    return acl_anthology_data


def has_code(acl_entry_dict):
    return "Code" in acl_entry_dict.keys()


def newer_than(acl_entry_dict, year):
    return acl_entry_dict["year"] > year


def is_major_conference(acl_entry_dict):
    # ACL, EMNLP, EACL, NAACL, IJCNLP, COLING
    major_conferences_list = list(MAJOR_CONFERENCES_ABBREVIATION_DICT.keys())

    is_workshop = "booktitle" in acl_entry_dict and "workshop" in acl_entry_dict["booktitle"].lower()
    is_tutorial = "booktitle" in acl_entry_dict and "tutorial" in acl_entry_dict["booktitle"].lower()
    is_major_conference = any([conference in acl_entry_dict["booktitle"]
                               for conference in major_conferences_list
                               if "booktitle" in acl_entry_dict])
    # emnlp_title = "Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing"
    # r = acl_entry_dict["booktitle"] == emnlp_title
    return is_major_conference and not is_workshop and not is_tutorial


def plot_major_conferences_code_submission_ratio_from_2014(acl_data, plot_dir):
    file_name = os.path.join(plot_dir, "major_conferences_code_submission_ratio_from_2016")

    filtered_data = acl_data

    filter_fn_list = [
        functools.partial(newer_than, year=2015),
        # has_code,
        is_major_conference
    ]
    # 10081 papers newer than 2016 and from major conferences
    for filter_fn in filter_fn_list:
        filtered_data = filter(filter_fn, filtered_data)

    filtered_data = list(filtered_data)
    pd.DataFrame(filtered_data).to_csv(file_name + "_full.csv", index=False)

    filtered_data_with_code = list(filter(has_code, filtered_data))

    filtered_data = [{"year": entry["year"],
                      "has_code": "Code" in entry,
                      "has_software": "Software" in entry or "Optional supplementary material" in entry,
                      "conference": entry["conference"] if "conference" in entry else entry["booktitle"]}
                     for entry in filtered_data
                     if "booktitle" in entry]
    papers_df = pd.DataFrame(filtered_data, columns=["year", "has_code", "has_software", "conference"])

    agg_result = papers_df.groupby(["year", "conference"]).agg(
        submissions_with_code=('has_code', 'sum'),
        submissions_with_software=('has_software', 'sum'),
        total_submissions=('has_code', 'count')).reset_index()
    agg_result["code_ratio"] = agg_result["submissions_with_code"] / agg_result["total_submissions"]
    agg_result["software_ratio"] = agg_result["submissions_with_software"] / agg_result["total_submissions"]
    year_set = list(sorted(set([entry["year"] for entry in filtered_data])))

    yearly_total_papers = {year: sum([entry["year"] == year for entry in filtered_data]) for year in year_set}
    yearly_total_papers_with_code = {year: sum([entry["year"] == year for entry in filtered_data_with_code]) for year in
                                     year_set}

    yearly_ratio = {year: yearly_total_papers_with_code[year] / yearly_total_papers[year] for year in year_set}

    plt_data = pd.DataFrame(yearly_ratio.items(), columns=["Year", "Ratio"])

    cat_plot = sns.catplot(data=plt_data, x="Year", y="Ratio", kind="bar")
    # cat_plot.set_title("Title test")
    plt_data.to_csv(file_name + "_plot.csv", index=False)
    # cat_plot.savefig(file_name + ".svg")
    import matplotlib.pyplot as plt
    submissions_with_code_plot = sns.relplot(data=agg_result,
                                             x="year",
                                             y="submissions_with_code",
                                             hue="conference",
                                             kind="line",
                                             facet_kws={'legend_out': True}) \
        .set(xlabel="Year", ylabel="Submissions with Code")
    submissions_with_code_plot._legend.set_title('Conference')
    # submissions_with_code_plot_legend = submissions_with_code_plot._legend
    # submissions_with_code_plot_legend.set_title('Conference')
    # submissions_with_code_plot_legend.set_loc('upper left')

    submissions_with_code_plot.savefig(file_name + "_1.svg")
    submission_with_code_ration_plot = sns.relplot(data=agg_result,
                                                   x="year",
                                                   y="code_ratio",
                                                   hue="conference",
                                                   kind="line",
                                                   facet_kws={'legend_out': True}) \
        .set(xlabel="Year", ylabel="Code Submission Ratio")
    submission_with_code_ration_plot._legend.set_title('Conference')
    submission_with_code_ration_plot.savefig(file_name + "_2.svg")

    # sns.relplot(data=agg_result,
    #             x="year",
    #             y="submissions_with_software",
    #             hue="conference",
    #             kind="line") \
    #     .set(xlabel="Year", ylabel="Submissions with Software") \
    #     .savefig(file_name + "_3.svg")
    # sns.relplot(data=agg_result,
    #             x="year",
    #             y="software_ratio",
    #             hue="conference",
    #             kind="line") \
    #     .set(xlabel="Year", ylabel="Software Submission Ratio") \
    #     .savefig(file_name + "_4.svg")


# def plot_conferences_code_submission_ratio_from_2018(acl_data, plot_dir):
#     filtered_data = acl_data
#     filter_fn_list = [
#         functools.partial(newer_than, year=2014),
#         # has_code,
#         is_major_conference
#     ]
#     # 10081 papers newer than 2014 and from major conferences
#     for filter_fn in filter_fn_list:
#         filtered_data = filter(filter_fn, filtered_data)
#     filtered_data = list(filtered_data)
#     filtered_data_with_code = list(filter(has_code, filtered_data))
#
#     # EACL, NAACL, IJCNLP, COLING
#
#     for conference in major_conference_list:
#         conference_papers = list(filter(lambda x: conference in x["booktitle"], filtered_data))
#         conference_papers_with_code = list(filter(lambda x: conference in x["booktitle"], filtered_data_with_code))
#
#         year_set = list(sorted(set([entry["year"] for entry in conference_papers])))
#
#         yearly_total_papers = {year: sum([entry["year"] == year for entry in conference_papers]) for year in year_set}
#         yearly_total_papers_with_code = {year: sum([entry["year"] == year for entry in conference_papers_with_code]) for
#                                          year in
#                                          year_set}
#
#         yearly_ratio = {year: yearly_total_papers_with_code[year] / yearly_total_papers[year] for year in year_set}
#
#         plt_data = pd.DataFrame(yearly_ratio.items(), columns=["Year", "Ratio"])
#
#         cat_plot = sns.catplot(data=plt_data, x="Year", y="Ratio", kind="bar")
#         conference_abr = conference_abr_dict[conference]
#         # cat_plot.set(title=conference_abr)
#         conference_file_name = conference_abr.lower().replace(" ", "_")
#         file_name = os.path.join(plot_dir, conference_file_name + "_code_submission_ratio_from_2014")
#         plt_data.to_csv(file_name + "_plot.csv", index=False)
#         cat_plot.savefig(file_name + ".svg")
# pd.DataFrame(filtered_data).to_csv(file_name + "_full.csv", index=False)


def preprocess_acl_data(acl_anthology_data):
    major_conferences_list = list(MAJOR_CONFERENCES_ABBREVIATION_DICT.keys())
    for acl_entry in acl_anthology_data:
        if "booktitle" in acl_entry:
            acl_entry["booktitle"] = acl_entry["booktitle"].replace("{", "").replace("}", "")

            conference_full_name = next(filter(lambda conference: conference in acl_entry["booktitle"],
                                               major_conferences_list),
                                        None)
            if conference_full_name is not None:
                acl_entry["conference"] = MAJOR_CONFERENCES_ABBREVIATION_DICT[conference_full_name]
        acl_entry["year"] = int(acl_entry["year"])


def main():
    parser = argparse.ArgumentParser(description='Downloading reproducibility data for ACL Anthology')
    parser.add_argument("--anthology_json_path", type=str)
    parser.add_argument("--plot_dir", type=str)
    parser.add_argument("--selected_papers", type=str)
    sns.set_theme()
    sns.set_style("darkgrid")

    args = parser.parse_args()
    anthology_json_path = args.anthology_json_path
    plot_dir = args.plot_dir
    selected_papers = args.selected_papers

    acl_anthology = load_anthology(anthology_json_path)
    preprocess_acl_data(acl_anthology)

    acl_anthology_df = pd.DataFrame(acl_anthology)
    selected_papers_id_df = pd.read_csv(selected_papers)

    emnlp_2021_df = acl_anthology_df[
        np.logical_and(
            np.logical_and(acl_anthology_df["conference"] == "EMNLP",
                           acl_anthology_df["year"] == 2021),
            acl_anthology_df["github_status"] == "success")
    ]
    emnlp_2021_df["days_since_last_update"] = emnlp_2021_df['updated_at'].apply(lambda x:
                                                                                (datetime.datetime(2022, 6, 15) -
                                                                                 datetime.datetime.strptime(x,
                                                                                                            "%Y-%m-%dT%H:%M:%SZ")).days)

    selected_papers_info_df = selected_papers_id_df.merge(emnlp_2021_df, on=["ID"], how="left")

    agg_dict = {
        "conference": ['count'],
        'stargazers_count': ['mean', 'std'],
        'forks_count': ['mean', 'std'],
        'open_issues_count': ['mean', 'std'],
        'days_since_last_update': ['mean', 'std']
    }
    emnlp_agg_df = emnlp_2021_df.groupby("conference").agg(agg_dict).reset_index()

    final_result = selected_papers_info_df[
        ["title", "stargazers_count", "forks_count", "open_issues_count", "days_since_last_update"]]

    emnlp_dict = {"title": "EMNLP"}
    for key in agg_dict.keys():
        if key == "conference":
            continue
        emnlp_dict[key] = str(round(emnlp_agg_df[(key, "mean")][0], 2)) + " +- " + str(round(emnlp_agg_df[(key, "std")][0]))
    final_result = final_result.append(emnlp_dict, ignore_index=True)
    final_result["title"] = final_result["title"].apply(lambda x: x.replace("{", "").replace("}", ""))

    pd.set_option('display.max_colwidth', None)
    print(final_result.to_latex(index=False))
    # plot_conferences_code_submission_ratio_from_2018(acl_anthology, plot_dir)


if __name__ == '__main__':
    main()
