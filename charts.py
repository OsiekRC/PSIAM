from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from main2 import get_or_generate_month_file_for_building, get_or_generate_hour_file_for_building, \
    get_or_generate_month_hour_file_for_buiding, load_data_from_source, get_or_generate_number_of_aps

buildings ={
    "A" : ["A1","A4","A5","A10"],
    "B" : ["B1","B4","B5","B8", "B9"],
    "C" : ["C2","C3","C4", "C6", "C7", "C11", "C13", "C16"],
    "D" : ["D1","D2"]
}

buildings_arr = ["A1","A4","A5","A10", "B1","B4","B5","B8", "B9", "C2","C3","C4","C5", "C6", "C7", "C11", "C13", "C16", "D1","D2"]

ignore_buildings = ["A4","A5","B8","C4","C13"]

stats_type_title_mapping = {
    "NoOfUsers": "liczba użytkowników",
    "PoorSNRClients": "liczba słabych połączeń",
    "LoadChannelUtilization": "wartość wykorzystania kanału",
    "PoorSNRClients-NoOfUsers": "Średni stosunek słabych połączeń do pozostałych"
}

time_interval_title_mapping = {
    "hourly": "godzin",
    "monthly": "miesiąca",
    "monthly-hourly": "godzin dla każdego miesiąca",
}

value_type_title_mapping = {
    "max": "Maksymalna",
    "avg": "Średnia",
    "combine": None,
}

column_verbosity_mapping = {
    "max": "Maksimum",
    "avg": "Średnia",
    "month": "Miesiąc",
    "hour": "Godzina",
}

month_verbosity_mapping = {
    1: "Styczeń",
    2: "Luty",
    3: "Marzec",
    4: "Kwiecień",
    5: "Maj",
    6: "Czerwiec",
    10: "Październik",
    11: "Listopad",
    12: "Grudzień",
}

time_interval_dimensions_mapping = {
    "hourly": {"left": 0.07, "bottom": 0.12, "right": 0.93, "top": 0.95},
    "monthly": {"left": 0.07, "bottom": 0.2, "right": 0.93, "top": 0.95},
    "monthly-hourly": {"left": 0.03, "bottom": 0.14, "right": 0.97, "top": 0.95},
}

def get_title(value, stats_type, building, interval):
    value_title = value_type_title_mapping[value]
    stats_type_title = stats_type_title_mapping[stats_type]
    interval_title = time_interval_title_mapping[interval]
    if value_title is None or stats_type == "PoorSNRClients-NoOfUsers":
        stats_type_title = stats_type_title.capitalize()
        return f"{stats_type_title} dla budynku {building} w skali {interval_title}"
    return f"{value_title} {stats_type_title} dla budynku {building} w skali {interval_title}"

def generate_chart_for_building(data, title, kind, figsize, dimensions, savedir, label=None):
    show_legend = not len(data.columns) == 2
    if label is not None:
        data.plot(title=title, x=label, kind=kind, figsize=figsize, legend=show_legend)
    else:
        data.plot(title=title, kind=kind, figsize=figsize, legend=show_legend)
    Path(savedir).mkdir(parents=True, exist_ok=True)
    plt.subplots_adjust(**dimensions)
    plt.savefig(f'{savedir}/{title}.png')
    plt.close()
    print(f"Processed chart: {title}")

def extract_data_from_csv(stat_type, building, interval):
    try:
        return pd.read_csv(filepath_or_buffer=f'{stat_type}-{building}-{interval}.csv', index_col=False)
    except FileNotFoundError:
        return None

def verbose_data(data):
    if "hour" in data.columns:
        data.rename(columns={"hour": column_verbosity_mapping["hour"]}, inplace=True)
    if "month" in data.columns:
        data.replace({'month': month_verbosity_mapping.keys()}, {"month": month_verbosity_mapping.values()}, inplace=True)
        data.rename(columns={"month": column_verbosity_mapping["month"]}, inplace=True)
    if "avg" in data.columns:
        data.rename(columns={"avg": column_verbosity_mapping["avg"]}, inplace=True)
    if "max" in data.columns:
        data.rename(columns={"max": column_verbosity_mapping["max"]}, inplace=True)
    return data

def generate_charts_for_building_stats():
    for stat_type in stats_type_title_mapping.keys():
        for building in buildings_arr:
            for interval in time_interval_title_mapping.keys():
                extracted_data = extract_data_from_csv(stat_type, building, interval)
                if extracted_data is not None:
                    kind = 'line' if interval == 'hourly' else 'bar'
                    label = 'month' if interval == 'monthly' else 'hour'
                    for value in value_type_title_mapping.keys():
                        if interval == "monthly-hourly":
                            if value != "combine":
                                chart_data = extracted_data.copy(deep=True)
                                chart_data = verbose_data(chart_data)
                                chart_data = chart_data.groupby(
                                    [column_verbosity_mapping['hour'], column_verbosity_mapping['month']]
                                ).mean().unstack(level=-1)[column_verbosity_mapping[value]]
                                generate_chart_for_building(
                                    chart_data[month_verbosity_mapping.values()],
                                    get_title(value, stat_type, building, interval),
                                    kind,
                                    (15, 8),
                                    time_interval_dimensions_mapping[interval],
                                    f"exported_charts/{building}",
                                )
                        else:
                            if value != "combine" and stat_type != "PoorSNRClients-NoOfUsers":
                                chart_data = extracted_data.filter(items=[label, value])
                            else:
                                chart_data = extracted_data.copy(deep=True)
                            chart_data = verbose_data(chart_data)
                            generate_chart_for_building(
                                chart_data,
                                get_title(value, stat_type, building, interval),
                                kind,
                                (7, 5),
                                time_interval_dimensions_mapping[interval],
                                f"exported_charts/{building}",
                                column_verbosity_mapping[label],
                            )

def show_no_aps_per_building(data):
    nr_of_aps = {}
    nr_of_aps_data = get_or_generate_number_of_aps(data)
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                nr_of_aps[building] = nr_of_aps_data[nr_of_aps_data['building'] == building].iloc[0]['NoAPs']
    y_pos = np.arange(len(nr_of_aps.keys()))
    plt.bar(y_pos, nr_of_aps.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, nr_of_aps.keys())
    plt.ylabel('Liczba AP')
    plt.title('Liczba AccessPointów dla budynków PWr')
    for index, value in enumerate(nr_of_aps.values()):
        plt.text(index -0.5 , value,  str(value))
    plt.show()

def show_avg_users_per_building(data):
    nr_of_users = {}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                nr_of_users[building] = get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
    vals = []
    for building in nr_of_users:
        vals_for_building = [cv for cv in nr_of_users[building]['avg'].tolist() if str(cv) != 'nan']
        vals.append(sum(vals_for_building) / len(vals_for_building))
    y_pos = np.arange(len(nr_of_users.keys()))
    plt.bar(y_pos, vals, align='center', alpha=0.5)
    plt.xticks(y_pos, nr_of_users.keys())
    plt.ylabel('Liczba użytkowników')
    plt.title('Średnia liczba użytkowników dla budynków PWr')
    for index, value in enumerate(vals):
        plt.text(index - 0.5, value, str(value).split('.')[0])
    plt.show()

def show_ratio_max_avg_users_per_building(data):

    ratio={}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                nr_of_users_data = get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                vals_for_building = [cv for cv in nr_of_users_data['avg'].tolist() if str(cv) != 'nan']
                nr_of_users = sum(vals_for_building) / len(vals_for_building)
                max_vals_for_building=[cv for cv in nr_of_users_data['max'].tolist() if str(cv) != 'nan']
                max_nr_of_users= max(max_vals_for_building)
                ratio[building] = max_nr_of_users / nr_of_users
    y_pos = np.arange(len(ratio.keys()))
    plt.bar(y_pos, ratio.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, ratio.keys())
    plt.ylabel('')
    plt.title('Stosunek max liczby użytkowników do średniej liczby użytkowników dla budynków PWr')
    for index, value in enumerate(ratio.values()):
        plt.text(index - 0.5, value, str(value).split('.')[0])
    plt.show()

def show_max_users_per_building(data):
    nr_of_users = {}
    max_nr_of_users={}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                nr_of_users_data = get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                vals_for_building = [cv for cv in nr_of_users_data['avg'].tolist() if str(cv) != 'nan']
                nr_of_users[building] = sum(vals_for_building) / len(vals_for_building)
                max_vals_for_building=[cv for cv in nr_of_users_data['max'].tolist() if str(cv) != 'nan']
                max_nr_of_users[building] = max(max_vals_for_building)
    vals = []

    fig, ax = plt.subplots()
    index = np.arange(len(nr_of_users.keys()))
    bar_width = 0.35
    opacity = 0.8
    rects1 = plt.bar(index, nr_of_users.values(), bar_width,
                     alpha=opacity,
                     color='b',
                     label='Użytkownicy - średnia')

    rects2 = plt.bar(index + bar_width, max_nr_of_users.values(), bar_width,
                     alpha=opacity,
                     color='g',
                     label='Użytkownicy - max')

    plt.xlabel('Budynek')
    plt.ylabel('Liczba użytkowników')
    plt.title('Średnia i maksymalna liczba użytkowników dla budynków PWr')
    plt.xticks(index + bar_width, nr_of_users.keys())
    plt.legend()
    plt.tight_layout()
    for index, value in enumerate(nr_of_users.values()):
        plt.text(index - 0.2, value, str(value).split('.')[0] )
    for index, value in enumerate(max_nr_of_users.values()):
        plt.text(index + 0.2, value, str(value).split('.')[0])
    plt.show()


def show_avg_users_and_poor_connection_users(data):
    nr_of_users = {}
    nr_of_poor_users={}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                nr_of_users[building] = get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                nr_of_poor_users[building] = get_or_generate_month_file_for_building(data, building, 'PoorSNRClients')
    # data to plot

    vals_users = []
    vals_poor_users=[]
    for building in nr_of_users:
        vals_for_building = [cv for cv in nr_of_users[building]['avg'].tolist() if str(cv) != 'nan']
        vals_users.append(sum(vals_for_building) / len(vals_for_building))
    for building in nr_of_poor_users:
        vals_for_building = [cv for cv in nr_of_poor_users[building]['avg'].tolist() if str(cv) != 'nan']
        vals_poor_users.append(sum(vals_for_building) / len(vals_for_building))
    n_groups = 4
    means_frank = (90, 55, 40, 65)
    means_guido = (85, 62, 54, 20)

    # create plot
    fig, ax = plt.subplots()
    index = np.arange(len(nr_of_users.keys()))
    bar_width = 0.35
    opacity = 0.8
    rects1 = plt.bar(index, vals_users, bar_width,
                     alpha=opacity,
                     color='b',
                     label='Użytkownicy')

    rects2 = plt.bar(index + bar_width, vals_poor_users, bar_width,
                     alpha=opacity,
                     color='g',
                     label='Użytkownicy o słabym SNR')

    plt.xlabel('Budynek')
    plt.ylabel('Liczba użytkowników')
    plt.title('Średnia liczba użytkowników i użytkowników o słabym SNR')
    plt.xticks(index + bar_width, nr_of_users.keys())
    plt.legend()
    plt.tight_layout()
    for index, value in enumerate(vals_users):
        plt.text(index - 0.2, value,  str(value).split('.')[0] + '.' + str(value).split('.')[1][:1])
    for index, value in enumerate(vals_poor_users):
        plt.text(index + 0.2, value,  str(value).split('.')[0] + '.' + str(value).split('.')[1][:1])
    plt.show()

def show_user_per_ap(data):
    user_per_ap = {}
    nr_of_aps_data = get_or_generate_number_of_aps(data)
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                month_data= get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                vals_for_building = [cv for cv in month_data['avg'].tolist() if str(cv) != 'nan']
                nr_of_users = sum(vals_for_building) / len(vals_for_building)
                nr_of_aps =  nr_of_aps_data[nr_of_aps_data['building'] == building].iloc[0]['NoAPs']
                user_per_ap[building] = nr_of_users / nr_of_aps

    y_pos = np.arange(len(user_per_ap.keys()))
    plt.bar(y_pos, user_per_ap.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, user_per_ap.keys())
    plt.ylabel('Liczba użytkowników na 1 AP')
    plt.title('Średnia liczba użytkowników na 1 AP dla budynków PWr')
    for index, value in enumerate(user_per_ap.values()):
        plt.text(index - 0.5, value, str(value).split('.')[0] + '.' + str(value).split('.')[1][:2])
    plt.show()

def show_max_user_per_ap(data):
    user_per_ap = {}
    nr_of_aps_data = get_or_generate_number_of_aps(data)
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                month_data= get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                vals_for_building = [cv for cv in month_data['max'].tolist() if str(cv) != 'nan']
                max_users = max(vals_for_building)
                nr_of_aps =  nr_of_aps_data[nr_of_aps_data['building'] == building].iloc[0]['NoAPs']
                user_per_ap[building] = max_users / nr_of_aps

    y_pos = np.arange(len(user_per_ap.keys()))
    plt.bar(y_pos, user_per_ap.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, user_per_ap.keys())
    plt.ylabel('Liczba użytkowników na 1 AP')
    plt.title('Maksymalna liczba użytkowników na 1 AP dla budynków PWr')
    for index, value in enumerate(user_per_ap.values()):
        plt.text(index - 0.5, value, str(value).split('.')[0] + '.' + str(value).split('.')[1][:2])
    plt.show()

def show_aps_with_max_utilization():
    filename = 'max-utilization.csv'
    file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    max_util={}
    for index, fd in file_data.iterrows():
        max_util[fd['apName']] = fd['utilization']

    y_pos = np.arange(len(max_util.keys()))
    plt.bar(y_pos, max_util.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, [k.replace('AP-' ,'')[:8] for k in max_util.keys()], rotation=70)
    plt.ylabel('Wykorzystanie kanału %')
    plt.title('Najbardziej obciążone AP')
    for index, value in enumerate(max_util.values()):
        plt.text(index - 0.5, value, str(value).split('.')[0] + '.' + str(value).split('.')[1][:2])
    plt.show()

def show_users_user_per_ap_and_ap_utilization(data):
    filename = 'max-utilization.csv'
    util_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    nr_of_aps_data = get_or_generate_number_of_aps(data)
    max_util_count = {}
    nr_of_users = {}
    user_per_ap = {}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                nr_of_users_building = get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                vals_for_building = [cv for cv in nr_of_users_building['avg'].tolist() if str(cv) != 'nan']
                nr_of_users[building] = sum(vals_for_building) / len(vals_for_building)
                nr_of_aps = nr_of_aps_data[nr_of_aps_data['building'] == building].iloc[0]['NoAPs']
                user_per_ap[building] = nr_of_users[building] / nr_of_aps
                util_per_building=util_data[util_data['apName'].str.contains(building, na=False)]
                max_util_count[building] =len(util_per_building.index)
    # data to plot
    # create plot
    fig, ax = plt.subplots()
    index = np.arange(len(nr_of_users.keys()))
    bar_width = 0.35
    opacity = 0.8
    """rects1 = plt.bar(index - bar_width, nr_of_users.values(), bar_width,
                     alpha=opacity,
                     color='b',
                     label='Użytkownicy')"""

    rects2 = plt.bar(index, user_per_ap.values(), bar_width,
                     alpha=opacity,
                     color='g',
                     label='Użytkownicy na 1 AP')
    rects3 = plt.bar(index + bar_width, max_util_count.values(), bar_width,
                     alpha=opacity,
                     color='y',
                     label='Obciążone AP')

    plt.xlabel('Budynek')
    plt.title('Użytkownicy, użytkownicy na 1 AP i obiciążone AP dla budynków PWr')
    plt.xticks(index + bar_width, nr_of_users.keys())
    plt.legend()
    #plt.tight_layout()
    """for index, value in enumerate(zip(vals_users, vals_poor_users)):
        plt.text(index - 0.5, value, str(value).split('.')[0])"""
    plt.show()

def show_ratio_poor_to_all_users(data):
    ratio = {}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                ratio_data = get_or_generate_month_file_for_building(data,building,'PoorSNRClients', 'NoOfUsers')
                ratio_building=[cv for cv in ratio_data['avg'].tolist() if str(cv) != 'nan']
                ratio[building] = (sum(ratio_building)/len(ratio_building) ) *100
    y_pos = np.arange(len(ratio.keys()))
    plt.bar(y_pos, ratio.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, ratio.keys())
    plt.ylabel('Uż. o słabym SNR do wszystkich uż. %')
    plt.title('Stosunek liczby użytkowników ze słabym SNR do liczby wszystkich użytkowników')
    for index, value in enumerate(ratio.values()):
        plt.text(index - 0.5, value, str(value).split('.')[0] + '.' + str(value).split('.')[1][:2])
    plt.show()

def show_channel_utilization(data):
    channel_utilization={}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                nr_of_users_data = get_or_generate_month_file_for_building(data, building, 'LoadChannelUtilization')
                vals_for_building = [cv for cv in nr_of_users_data['avg'].tolist() if str(cv) != 'nan']
                channel_utilization[building] = sum(vals_for_building) / len(vals_for_building)

    y_pos = np.arange(len(channel_utilization.keys()))
    plt.bar(y_pos, channel_utilization.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, channel_utilization.keys())
    plt.ylabel('Wykorzystanie kanału %')
    plt.title('Średnie wykorzystanie kanału w AP dla budynków PWr')
    for index, value in enumerate(channel_utilization.values()):
        plt.text(index - 0.5, value, str(value).split('.')[0])
    plt.show()


# try:
#     data = pd.read_csv(filepath_or_buffer='complete_data.csv', index_col=False)
#     # show_avg_users_per_building(data)
#     # show_avg_users_and_poor_connection_users(data)
#     # show_no_aps_per_building(data)
#     # show_user_per_ap(data)
#     # show_aps_with_max_utilization()
#     # show_users_user_per_ap_and_ap_utilization(data)
#     # show_ratio_poor_to_all_users(data)
#     # show_max_users_per_building(data)
#     # show_max_user_per_ap(data)
#     # show_ratio_max_avg_users_per_building(data)
#     # show_channel_utilization(data)
#
#
# except FileNotFoundError:
#     data = load_data_from_source()
#     with open('complete_data.csv', 'w') as data_file:
#         for index, data_day in enumerate(data.values()):
#             if index == 0:
#                 data_file.write(data_day.to_csv(index=False))
#             else:
#                 data_file.write(data_day.to_csv(index=False, header=None))
# print(data)
generate_charts_for_building_stats()
