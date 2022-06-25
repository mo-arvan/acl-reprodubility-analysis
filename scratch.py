import json
import os
import matplotlib.pyplot as plt
import numpy as np

data_dir = "data"
emnlp_dict = {}
for filename in os.listdir(data_dir):
    full_file_name = os.path.join(data_dir, filename)
    if filename.endswith(".json"):
        with open(full_file_name) as f:
            emnlp_dict[filename] = json.load(f)

keys_to_plot = ["Code",
                # "Software", "Data"
                ]

yearly_count = {}
for emnlp_year, emnlp_data in emnlp_dict.items():
    hist_data = {key: sum([1 for e in emnlp_data if key in e]) for key in keys_to_plot}
    hist_data["total"] = len(emnlp_data)
    yearly_count[emnlp_year] = hist_data

yearly_count = dict(sorted(yearly_count.items(), key=lambda x: x[0]))


def plot_count():
    # create data
    # create data
    plt.cla()
    x = np.arange(len(yearly_count))
    code_count = [r["Code"] for r in yearly_count.values()]
    # data_count = [r["Data"] for r in yearly_count.values()]
    # software_count = [r["Software"] for r in yearly_count.values()]
    width = 0.2

    # plot data in grouped manner of bar type
    # plt.bar(x - 0.2, code_count, width, color='cyan')
    # plt.bar(x, data_count, width, color='orange')
    # plt.bar(x + 0.2, software_count, width, color='green')
    plt.bar(x, code_count, width, color='cyan')

    plt.xticks(x, [k.split("_")[0] for k in list(yearly_count.keys())])
    plt.xlabel("Year")
    plt.ylabel("Count")
    plt.legend(["Code", "Data", "Software"])
    plt.title("EMNLP Code Submissions")
    plt.savefig("fig")

def plot_ratio():
    # create data
    # create data
    plt.cla()
    x = np.arange(len(yearly_count))
    code_count = [r["Code"] / r["total"] for r in yearly_count.values()]
    # data_count = [r["Data"]/ r["total"] for r in yearly_count.values()]
    # software_count = [r["Software"] / r["total"] for r in yearly_count.values()]
    width = 0.2

    # plot data in grouped manner of bar type
    # plt.bar(x - 0.2, code_count, width, color='cyan')
    # plt.bar(x, data_count, width, color='orange')
    # plt.bar(x + 0.2, software_count, width, color='green')
    plt.bar(x, code_count, width, color='cyan')

    plt.xticks(x, [k.split("_")[0] for k in list(yearly_count.keys())])
    plt.xlabel("Year")
    plt.ylabel("Count")
    plt.legend(["Code", "Data", "Software"])
    plt.title("EMNLP Code Submissions Ratio")
    plt.savefig("fig2")

plot_count()
plot_ratio()


keys_to_plot = ["Code",
                # "Software", "Data"
                ]

proceedings_list = list(filter(lambda x: x['ENTRYTYPE'] == "proceedings", acl_anthology_data))
inproceedings_list = list(filter(lambda x: x['ENTRYTYPE'] == 'inproceedings', acl_anthology_data))

else_list = list(filter(lambda x: x['ENTRYTYPE'] != "inproceedings" and
                                  x['ENTRYTYPE'] != "proceedings", acl_anthology_data))

venue_list = list(sorted(set([e["booktitle"] for e in acl_anthology_data if "booktitle" in e])))

emnlp_title = "Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing"
emnlp_papers = list(filter(lambda x: "booktitle" in x and
                                     x["booktitle"] == emnlp_title, acl_anthology_data))
yearly_count = {}
for emnlp_year, emnlp_data in emnlp_dict.items():
    hist_data = {key: sum([1 for e in emnlp_data if key in e]) for key in keys_to_plot}
hist_data["total"] = len(emnlp_data)
yearly_count[emnlp_year] = hist_data

yearly_count = dict(sorted(yearly_count.items(), key=lambda x: x[0]))


def plot_count():
    # create data
    # create data
    plt.cla()
    x = np.arange(len(yearly_count))
    code_count = [r["Code"] for r in yearly_count.values()]
    # data_count = [r["Data"] for r in yearly_count.values()]
    # software_count = [r["Software"] for r in yearly_count.values()]
    width = 0.2

    # plot data in grouped manner of bar type
    # plt.bar(x - 0.2, code_count, width, color='cyan')
    # plt.bar(x, data_count, width, color='orange')
    # plt.bar(x + 0.2, software_count, width, color='green')
    plt.bar(x, code_count, width, color='cyan')

    plt.xticks(x, [k.split("_")[0] for k in list(yearly_count.keys())])
    plt.xlabel("Year")
    plt.ylabel("Count")
    plt.legend(["Code", "Data", "Software"])
    plt.title("EMNLP Code Submissions")
    plt.savefig("fig")


def plot_ratio():
    # create data
    # create data
    plt.cla()
    x = np.arange(len(yearly_count))
    code_count = [r["Code"] / r["total"] for r in yearly_count.values()]
    # data_count = [r["Data"]/ r["total"] for r in yearly_count.values()]
    # software_count = [r["Software"] / r["total"] for r in yearly_count.values()]
    width = 0.2

    # plot data in grouped manner of bar type
    # plt.bar(x - 0.2, code_count, width, color='cyan')
    # plt.bar(x, data_count, width, color='orange')
    # plt.bar(x + 0.2, software_count, width, color='green')
    plt.bar(x, code_count, width, color='cyan')

    plt.xticks(x, [k.split("_")[0] for k in list(yearly_count.keys())])
    plt.xlabel("Year")
    plt.ylabel("Count")
    plt.legend(["Code", "Data", "Software"])
    plt.title("EMNLP Code Submissions Ratio")
    plt.savefig("fig2")


plot_count()
plot_ratio()
