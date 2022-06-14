import argparse
import concurrent
import csv
import json
import logging
import os
import time
from builtins import enumerate
from concurrent import futures
from datetime import datetime
from time import mktime
import bibtexparser
import bs4
import requests
import requests.utils
from bs4 import BeautifulSoup
from tqdm import tqdm

GLOBAL_HEADERS = requests.utils.default_headers()
GLOBAL_HEADERS.update({'User-Agent': 'Mozilla/5.0'})
GITHUB_RATE_LIMIT_REACHED = False

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def cache_load_acl_anthology_bib(bib_path, export_dir):
    json_export_file_name = os.path.join(export_dir, "anthology.json")
    if os.path.isfile(json_export_file_name):
        logging.info("Loading previously exported file, remove the files and rerun if you rather start fresh")
        with open(json_export_file_name, "r") as acl_json:
            acl_entries = json.load(acl_json)
    else:
        json_cache_file = bib_path + ".json"
        if os.path.isfile(json_cache_file):
            with open(json_cache_file, "r") as acl_json:
                acl_entries = json.load(acl_json)
        else:
            with open(bib_path) as acl_bib:
                bib_database = bibtexparser.bparser.BibTexParser(common_strings=True) \
                    .parse_file(acl_bib)
                acl_entries = bib_database.entries
                with open(json_cache_file, "w") as f:
                    json.dump(acl_entries, f)
    return acl_entries


# def try_get_webpage(url, headers, try_count=0):
#     response = None
#     request_failed = False
#     if try_count > 5:
#         return None
#     try:
#         response = requests.get(url=url, timeout=5, headers=headers)
#         if response.status_code == 404:
#             return None
#         if response.status_code != 200:
#             logging.error("status code {}".format(response.status_code))
#             request_failed = True
#     except Exception as e:
#         request_failed = True
#         logging.error("exception {}, {}".format(e, type(e)))
#     if request_failed:
#         logging.info("{} failed, fail count {}".format(url,
#                                                        try_count))
#         time.sleep(5)
#         try_get_webpage(url, headers, try_count + 1)
#
#     return response


def get_reproducibility_information(entry: dict):
    def parse_acl_anthology_webpage(response):
        soup = BeautifulSoup(response.content, "lxml")

        additional_information = []
        link_div_block = soup.find_all("div", {"class": "acl-paper-link-block"})
        table_div_block = soup.find_all("dl")

        if len(link_div_block) != 0 and hasattr(link_div_block[0], "children"):
            for c in link_div_block[0].children:
                if isinstance(c, bs4.element.Tag):
                    key, url = c.text, c.attrs["href"]
                    additional_information.append((key, url))

        if len(table_div_block) != 0:
            children_list = list(table_div_block[0].children)
            for i, c in enumerate(children_list):
                if c.text in ["PDF:", "Software:", "Code", "Data"]:
                    key = c.text.replace(":", "")
                    url = " ".join([c.attrs["href"] for c in children_list[i + 1].children if hasattr(c, "href")])

                    if "," in url:
                        logging.info("multi url {}".format(url))
                    additional_information.append((key, url))
        return additional_information

    result = entry.copy()

    if "acl_status" in result and result["acl_status"] == "success":
        return result

    global GLOBAL_HEADERS
    if "aclanthology.org" not in entry["url"]:
        result["acl_status"] = "missing"
        # This method only works on the aclanthology website
        return result
    acl_url = entry["url"]
    try:
        acl_page_response = requests.get(url=acl_url, timeout=2, headers=GLOBAL_HEADERS)
        if acl_page_response.status_code != 200:
            result["acl_status"] = "error {}".format(acl_page_response.status_code)
            return result
        # logging.info("{} success".format(acl_url))
        acl_info_tuple_list = parse_acl_anthology_webpage(acl_page_response)
        for key, value in acl_info_tuple_list:
            if key in result:
                if result[key] == value:
                    continue
                i = 1
                while key + "_{}".format(i) in result:
                    i = i + 1
                key = key + "_{}".format(i)
            result[key] = value
        result["acl_status"] = "success"

    except Exception as e:
        result["acl_status"] = "exception {}".format(type(e))
    return result


def get_entry_github_url(entry):
    code_url = next(filter(lambda x: "github.com/" in x, entry.values()), None)

    if code_url is not None:
        github_url = next(filter(lambda x: "github.com/" in x, code_url.split(" ")), None)
        github_url_api = github_url.replace("github.com/", "api.github.com/repos/")
        if len(github_url_api.split("/")) != 6:
            github_url_api = "/".join(github_url_api.split("/")[:6])
    else:
        github_url_api = None
    return github_url_api


def has_reached_github_api_limit(github_auth_token):
    rate_limit_url = "https://api.github.com/rate_limit"
    try:
        global GLOBAL_HEADERS
        headers = dict(GLOBAL_HEADERS)
        if github_auth_token != "":
            headers['Authorization'] = 'token ' + github_auth_token
        response = requests.get(rate_limit_url, headers=headers)
        if response.status_code != 200:
            return True
        r = response.json()
        if r["rate"]["remaining"] == 0:
            return True
        return False
    except Exception as e:
        return True


def get_github_api_rate_remaining_and_reset(github_auth_token):
    rate_limit_url = "https://api.github.com/rate_limit"
    remaining_requests, seconds_to_reset = 0, 5 * 60
    try:
        global GLOBAL_HEADERS
        headers = dict(GLOBAL_HEADERS)
        if github_auth_token != "":
            headers['Authorization'] = 'token ' + github_auth_token
        response = requests.get(rate_limit_url, headers=headers)
        if not response.status_code != 200:
            r = response.json()
            seconds_to_reset = (
                    datetime.fromtimestamp(mktime(time.gmtime(r["rate"]["reset"]))) - datetime.fromtimestamp(
                mktime(time.gmtime()))).total_seconds()
            remaining_requests = r["rate"]["remaining"]
    except Exception as e:
        pass
    return remaining_requests, seconds_to_reset


def get_entry_github_information(entry: dict, github_url_api, github_auth_token):
    def parse_github_webpage(response: requests.Response):
        response = response.json()
        github_tuple_list = []
        github_tuple_list.append(("stargazers_count", response["stargazers_count"]))
        github_tuple_list.append(("forks_count", response["forks_count"]))
        github_tuple_list.append(("open_issues_count", response["open_issues_count"]))
        github_tuple_list.append(("updated_at", response["updated_at"]))
        github_tuple_list.append(("created_at", response["created_at"]))
        github_tuple_list.append(("pushed_at", response["pushed_at"]))

        return github_tuple_list

    result = entry.copy()
    try:
        global GLOBAL_HEADERS
        headers = dict(GLOBAL_HEADERS)
        if github_auth_token != "":
            headers['Authorization'] = 'token ' + github_auth_token
        github_page_response = requests.get(url=github_url_api, timeout=2, headers=headers)
        if github_page_response.status_code != 200:
            result["github_status"] = "error {}".format(github_page_response.status_code)
        else:
            github_tuple_list = parse_github_webpage(github_page_response)
            for key, value in github_tuple_list:
                if key in result:
                    if result[key] == value:
                        continue
                    i = 1
                    while key + "_{}".format(i) in result:
                        i = i + 1
                    key = key + "_{}".format(i)
                result[key] = value
            result["github_status"] = "success"

    except Exception as e:
        result["github_status"] = "exception {}".format(type(e))

    return result


def export_acl(export_dir, acl_entries):
    export_file_name = os.path.join(export_dir, "anthology")
    json_file_name = export_file_name + ".json"
    with open(json_file_name, "w") as f:
        json.dump(acl_entries, f)

    keys = sorted(list(set([kk for k in acl_entries for kk in list(k.keys())])))

    csv_file_name = export_file_name + ".csv"
    with open(csv_file_name, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys,
                                     quoting=csv.QUOTE_ALL,
                                     doublequote=True)
        dict_writer.writeheader()
        dict_writer.writerows(acl_entries)


def run_func_in_parallel(func, inputs):
    number_of_entries = len(inputs)
    with tqdm(total=number_of_entries) as progress_bar:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_list = {executor.submit(func, entry):
                               index for index, entry in enumerate(inputs)}
            for future in concurrent.futures.as_completed(future_list):
                arg = future_list[future]
                inputs[arg] = future.result()
                progress_bar.update(1)
    return inputs


def get_acl_information(acl_entries):
    return run_func_in_parallel(get_reproducibility_information, acl_entries)


def get_github_information(acl_entries, github_auth_token):
    github_remaining_requests, github_time_to_reset = get_github_api_rate_remaining_and_reset(github_auth_token)
    for i in tqdm(range(len(acl_entries))):
        if github_remaining_requests == 0:
            logging.info("Waiting {} seconds for github reset".format(github_time_to_reset))
            time.sleep(github_time_to_reset + 5)
            github_remaining_requests, github_time_to_reset = get_github_api_rate_remaining_and_reset(github_auth_token)

        if "github_status" in acl_entries[i] and acl_entries[i]["github_status"] == "success":
            # we have already processed the entry
            continue
        github_url_api = get_entry_github_url(acl_entries[i])
        if github_url_api is None:
            acl_entries[i]["github_status"] = "missing"
            continue

        # We need to avoid sending too many get requests to github's api
        acl_entries[i] = get_entry_github_information(acl_entries[i], github_url_api, github_auth_token)
        github_remaining_requests -= 1

    return acl_entries


def main():
    parser = argparse.ArgumentParser(
        description='Downloading reproducibility data for ACL Anthology')
    parser.add_argument("--anthology_path", type=str)
    parser.add_argument("--export_dir", type=str)
    parser.add_argument("--github_auth_token", type=str, default="")

    args = parser.parse_args()
    anthology_file_path = args.anthology_path
    export_dir = args.export_dir
    github_auth_token = args.github_auth_token

    logging.info("Loading Bib")
    acl_entries = cache_load_acl_anthology_bib(anthology_file_path, export_dir)

    logging.info("Getting ACL Info")
    acl_entries = get_acl_information(acl_entries)

    logging.info("Exporting intermediate results")
    export_acl(export_dir, acl_entries)

    logging.info("Getting GitHub Info")
    acl_entries = get_github_information(acl_entries, github_auth_token)

    logging.info("Exporting Results")
    export_acl(export_dir, acl_entries)


if __name__ == '__main__':
    main()
