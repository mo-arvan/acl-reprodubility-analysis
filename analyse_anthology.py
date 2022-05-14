import json
import os
import matplotlib.pyplot as plt
import numpy as np
import re
import random
import argparse

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


def load_anthology(file_name):
    with open(file_name) as f:
        acl_anthology_data = json.load(f)
    return acl_anthology_data


def has_code(acl_entry_dict):
    return "Code" in acl_entry_dict.keys()


def newer_than(acl_entry_dict, year):
    return int(acl_entry_dict["year"]) > year


def is_major_conference(acl_entry_dict):
    # ACL, EMNLP, EACL, NAACL, IJCNLP, COLING
    major_conference_list = [
        "Annual Meeting of the Association for Computational Linguistics",
        "Conference on Empirical Methods in Natural Language Processing",
        "European Chapter of the Association for Computational Linguistics",
        "North American Chapter of the Association for Computational Linguistics",
        "International Joint Conference on Natural Language Processing",
        "International Conference on Computational Linguistics",
    ]
    is_workshop = "booktitle" in acl_entry_dict and "workshop" in acl_entry_dict["booktitle"].lower()
    is_tutorial = "booktitle" in acl_entry_dict and "tutorial" in acl_entry_dict["booktitle"].lower()
    is_major_conference = any([conference in acl_entry_dict["booktitle"]
                               for conference in major_conference_list
                               if "booktitle" in acl_entry_dict])
    # emnlp_title = "Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing"
    # r = acl_entry_dict["booktitle"] == emnlp_title
    return is_major_conference and not is_workshop and not is_tutorial


def plot_major_conferences_code_submission_ratio_from_2014(acl_data, plot_dir):
    filtered_data = acl_data

    filter_fn_list = [
        functools.partial(newer_than, year=2014),
        # has_code,
        is_major_conference
    ]
    # 10081 papers newer than 2016 and from major conferences
    for filter_fn in filter_fn_list:
        filtered_data = filter(filter_fn, filtered_data)
    filtered_data = list(filtered_data)

    filtered_data_with_code = list(filter(has_code, filtered_data))

    year_set = list(sorted(set([entry["year"] for entry in filtered_data])))

    yearly_total_papers = {year: sum([entry["year"] == year for entry in filtered_data]) for year in year_set}
    yearly_total_papers_with_code = {year: sum([entry["year"] == year for entry in filtered_data_with_code]) for year in
                                     year_set}

    yearly_ratio = {int(year): yearly_total_papers_with_code[year] / yearly_total_papers[year] for year in year_set}

    plt_data = pd.DataFrame(yearly_ratio.items(), columns=["Year", "Ratio"])

    cat_plot = sns.catplot(data=plt_data, x="Year", y="Ratio", kind="bar")

    # cat_plot.set_title("Title test")
    file_name = os.path.join(plot_dir, "major_conferences_code_submission_ratio_from_2016")
    pd.DataFrame(filtered_data).to_csv(file_name + "_full.csv", index=False)
    plt_data.to_csv(file_name + "_plot.csv", index=False)
    cat_plot.savefig(file_name + ".svg")


def plot_conferences_code_submission_ratio_from_2018(acl_data, plot_dir):
    filtered_data = acl_data
    filter_fn_list = [
        functools.partial(newer_than, year=2014),
        # has_code,
        is_major_conference
    ]
    # 10081 papers newer than 2014 and from major conferences
    for filter_fn in filter_fn_list:
        filtered_data = filter(filter_fn, filtered_data)
    filtered_data = list(filtered_data)
    filtered_data_with_code = list(filter(has_code, filtered_data))

    major_conference_list = [
        "Annual Meeting of the Association for Computational Linguistics",
        "Conference on Empirical Methods in Natural Language Processing",
        "European Chapter of the Association for Computational Linguistics",
        "North American Chapter of the Association for Computational Linguistics",
        "International Joint Conference on Natural Language Processing",
        "International Conference on Computational Linguistics",
    ]
    # EACL, NAACL, IJCNLP, COLING
    conference_abr_dict = {
        "Annual Meeting of the Association for Computational Linguistics":"ACL",
        "Conference on Empirical Methods in Natural Language Processing": "EMNLP",
        "European Chapter of the Association for Computational Linguistics": "EACL",
        "North American Chapter of the Association for Computational Linguistics": "NAACL",
        "International Joint Conference on Natural Language Processing": "IJCNLP",
        "International Conference on Computational Linguistics": "COLING",
    }
    for conference in major_conference_list:
        conference_papers = list(filter(lambda x: conference in x["booktitle"], filtered_data))
        conference_papers_with_code = list(filter(lambda x: conference in x["booktitle"], filtered_data_with_code))

        year_set = list(sorted(set([entry["year"] for entry in conference_papers])))

        yearly_total_papers = {year: sum([entry["year"] == year for entry in conference_papers]) for year in year_set}
        yearly_total_papers_with_code = {year: sum([entry["year"] == year for entry in conference_papers_with_code]) for
                                         year in
                                         year_set}

        yearly_ratio = {int(year): yearly_total_papers_with_code[year] / yearly_total_papers[year] for year in year_set}

        plt_data = pd.DataFrame(yearly_ratio.items(), columns=["Year", "Ratio"])

        cat_plot = sns.catplot(data=plt_data, x="Year", y="Ratio", kind="bar")

        conference_abr = conference_abr_dict[conference]
        cat_plot.set(title=conference_abr)
        conference_file_name = conference_abr.lower().replace(" ", "_")
        # cat_plot.set_title("Title test")
        file_name = os.path.join(plot_dir, conference_file_name + "_code_submission_ratio_from_2014")
        plt_data.to_csv(file_name + "_plot.csv", index=False)
        cat_plot.savefig(file_name + ".svg")
    # pd.DataFrame(filtered_data).to_csv(file_name + "_full.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description='Downloading reproducibility data for ACL Anthology')
    parser.add_argument("--anthology_json_path", type=str)
    parser.add_argument("--plot_dir", type=str)

    args = parser.parse_args()
    anthology_json_path = args.anthology_json_path
    plot_dir = args.plot_dir

    acl_anthology = load_anthology(anthology_json_path)

    for acl_entry in acl_anthology:
        if "booktitle" in acl_entry:
            acl_entry["booktitle"] = acl_entry["booktitle"].replace("{", "").replace("}", "")
    plot_major_conferences_code_submission_ratio_from_2014(acl_anthology, plot_dir)

    plot_conferences_code_submission_ratio_from_2018(acl_anthology, plot_dir)


if __name__ == '__main__':
    main()
