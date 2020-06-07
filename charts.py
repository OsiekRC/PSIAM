from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from main import get_or_generate_monthly_hour_counter_file, get_or_generate_monthly_counter_file, \
    get_or_generate_hourly_counter_file, get_or_generate_building_file, get_or_generate_top_aps_data, months
from main2 import get_or_generate_month_file_for_building, get_or_generate_hour_file_for_building, \
    get_or_generate_month_hour_file_for_buiding, load_data_from_source, get_or_generate_number_of_aps
from main3 import get_or_generate_file_fixed_date

buildings = {
    "A": ["A1", "A4", "A5", "A10"],
    "B": ["B1", "B4", "B5", "B8", "B9"],
    "C": ["C2", "C3", "C4", "C6", "C7", "C11", "C13", "C16"],
    "D": ["D1", "D2"]
}
#buildings = ["A1", "B4", "D1"]
buildings_arr = ["A1", "A4", "A5", "A10", "B1", "B4", "B5", "B8", "B9", "C2", "C3", "C4", "C5", "C6", "C7", "C11",
                 "C13", "C16", "D1", "D2"]

ignore_buildings = ["A4", "A5", "B8", "C4", "C13"]

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
dimensions = {"left": 0.12, "bottom": 0.14, "right": 0.99, "top": 0.95}
savedir = "/home/catalina/Documents/aaastudiaaa/psiam/charts/gen"

dates = ["2015-05-19", "2015-10-09", "2015-11-18"]


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
        data.replace({'month': month_verbosity_mapping.keys()}, {"month": month_verbosity_mapping.values()},
                     inplace=True)
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
        plt.text(index - 0.5, value, str(value))
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
    ratio = {}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                nr_of_users_data = get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                vals_for_building = [cv for cv in nr_of_users_data['avg'].tolist() if str(cv) != 'nan']
                nr_of_users = sum(vals_for_building) / len(vals_for_building)
                max_vals_for_building = [cv for cv in nr_of_users_data['max'].tolist() if str(cv) != 'nan']
                max_nr_of_users = max(max_vals_for_building)
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
    max_nr_of_users = {}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                nr_of_users_data = get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                vals_for_building = [cv for cv in nr_of_users_data['avg'].tolist() if str(cv) != 'nan']
                nr_of_users[building] = sum(vals_for_building) / len(vals_for_building)
                max_vals_for_building = [cv for cv in nr_of_users_data['max'].tolist() if str(cv) != 'nan']
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
        plt.text(index - 0.2, value, str(value).split('.')[0])
    for index, value in enumerate(max_nr_of_users.values()):
        plt.text(index + 0.2, value, str(value).split('.')[0])
    plt.show()


def show_avg_users_and_poor_connection_users(data):
    nr_of_users = {}
    nr_of_poor_users = {}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                nr_of_users[building] = get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                nr_of_poor_users[building] = get_or_generate_month_file_for_building(data, building, 'PoorSNRClients')
    # data to plot

    vals_users = []
    vals_poor_users = []
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
        plt.text(index - 0.2, value, str(value).split('.')[0] + '.' + str(value).split('.')[1][:1])
    for index, value in enumerate(vals_poor_users):
        plt.text(index + 0.2, value, str(value).split('.')[0] + '.' + str(value).split('.')[1][:1])
    plt.show()


def show_user_per_ap(data):
    user_per_ap = {}
    nr_of_aps_data = get_or_generate_number_of_aps(data)
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                month_data = get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                vals_for_building = [cv for cv in month_data['avg'].tolist() if str(cv) != 'nan']
                nr_of_users = sum(vals_for_building) / len(vals_for_building)
                nr_of_aps = nr_of_aps_data[nr_of_aps_data['building'] == building].iloc[0]['NoAPs']
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
                month_data = get_or_generate_month_file_for_building(data, building, 'NoOfUsers')
                vals_for_building = [cv for cv in month_data['max'].tolist() if str(cv) != 'nan']
                max_users = max(vals_for_building)
                nr_of_aps = nr_of_aps_data[nr_of_aps_data['building'] == building].iloc[0]['NoAPs']
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
    max_util = {}
    for index, fd in file_data.iterrows():
        max_util[fd['apName']] = fd['utilization']

    y_pos = np.arange(len(max_util.keys()))
    plt.bar(y_pos, max_util.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, [k.replace('AP-', '')[:8] for k in max_util.keys()], rotation=70)
    plt.ylabel('Wykorzystanie kanału %')
    plt.title('Najbardziej obciążone AP')
    for index, value in enumerate(max_util.values()):
        plt.text(index - 0.5, value, str(value).split('.')[0] + '.' + str(value).split('.')[1][:2])
    plt.show()


def show_aps_with_max_column(data, column, all_buildings_one_chart=False):
    all_buildings_data = None
    for building in buildings:
        building_data = get_or_generate_top_aps_data(data, column, building, 5, None)

        if all_buildings_one_chart:
            if all_buildings_data is None:
                all_buildings_data = building_data
            else:
                all_buildings_data = pd.concat([all_buildings_data, building_data])

        else:
            max_vals = {}
            for index, fd in building_data.iterrows():
                max_vals[fd['apName']] = fd[column]
            y_pos = np.arange(len(max_vals.keys()))
            plt.bar(y_pos, max_vals.values(), align='center', alpha=0.5)
            plt.xticks(y_pos, [k.replace('AP-', '') for k in max_vals.keys()], rotation=70)
            plt.title('AP o maksymalnym ' + column + ' w budynku ' + building)
            for index, value in enumerate(max_vals.values()):
                plt.text(index - 0.5, value, str(value).split('.')[0] + '.' + str(value).split('.')[1][:2])
            plt.show()

    if all_buildings_one_chart:
        max_vals = {}
        for index, fd in all_buildings_data.iterrows():
            max_vals[fd['apName']] = fd[column]
        y_pos = np.arange(len(max_vals.keys()))
        barlist = plt.bar(y_pos, max_vals.values(), align='center', alpha=0.5)
        for k in range(0, len(barlist)):
            if k < 5:
                barlist[k].set_color('r')
            elif k < 10:
                barlist[k].set_color('g')
            elif k < 15:
                barlist[k].set_color('y')
            elif k < 20:
                barlist[k].set_color('b')

        plt.xticks(y_pos, [k.replace('AP-', '').replace('acf2.', '') for k in max_vals.keys()], rotation=40)
        plt.title('AP o maksymalnym ' + column + " w budynkach " + ",".join(buildings))
        for index, value in enumerate(max_vals.values()):
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
                util_per_building = util_data[util_data['apName'].str.contains(building, na=False)]
                max_util_count[building] = len(util_per_building.index)
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
    # plt.tight_layout()
    """for index, value in enumerate(zip(vals_users, vals_poor_users)):
        plt.text(index - 0.5, value, str(value).split('.')[0])"""
    plt.show()


def show_ratio_poor_to_all_users(data):
    ratio = {}
    for group in buildings:
        for building in buildings[group]:
            if not building in ignore_buildings:
                ratio_data = get_or_generate_month_file_for_building(data, building, 'PoorSNRClients', 'NoOfUsers')
                ratio_building = [cv for cv in ratio_data['avg'].tolist() if str(cv) != 'nan']
                ratio[building] = (sum(ratio_building) / len(ratio_building)) * 100
    y_pos = np.arange(len(ratio.keys()))
    plt.bar(y_pos, ratio.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, ratio.keys())
    plt.ylabel('Uż. o słabym SNR do wszystkich uż. %')
    plt.title('Stosunek liczby użytkowników ze słabym SNR do liczby wszystkich użytkowników')
    for index, value in enumerate(ratio.values()):
        plt.text(index - 0.5, value, str(value).split('.')[0] + '.' + str(value).split('.')[1][:2])
    plt.show()


def show_channel_utilization(data):
    channel_utilization = {}
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

def show_aps_nr_users(data, column, limit=None, line=False, month=None, max_val=None):
    for building in buildings:
        building_data = get_or_generate_building_file(data, column, building, limit, month=month)
        max_nr_of_users_aps = get_or_generate_top_aps_data(data, 'NoOfUsers', building, 1, None)
        chart_data = {}
        avgs = {}
        aps = max_nr_of_users_aps['apName'].unique()
        for ap in aps:
            helper = []
            ap_data = building_data[building_data['apName'] == ap]
            chart_data[ap] = {}
            for index, b_data in ap_data.iterrows():
                chart_data[ap][b_data['hour']] = b_data['avg']
                helper.append(b_data['avg'])
            avgs[ap] = sum(helper) / len(helper)

        fig = plt.figure()
        for i in range(0, len(aps)):
            ap = (max(avgs, key=avgs.get))
            avgs[ap] = 0
            hours = [k for k in chart_data[ap].keys()]
            x = [h for i, h in enumerate(hours) if i % 2]
            vals = [chart_data[ap][hour] for hour in chart_data[ap]]
            color, pos = get_color(i, 0, 0)
            if line:
                plt.plot(hours, vals, color="r")
            else:
                bars = plt.bar(hours, vals)
                for bar in bars:
                    bar.set_color(color)
            if max_val is not None:
                plt.ylim(0.0, max_val)
            plt.gcf().autofmt_xdate()
            plt.xticks(x)
        plt.title((("Miesiąc " + str(month) + " ") if month is not None else "") + column + " dla " + aps[0])
        plt.legend(aps)
        # plt.ylabel("Wykorzystanie kanału %")
        # plt.show()

        title = str(month) + "-" + column + "-" + aps[0]
        title = title.replace('.', '_')
        title += "-line" if line else ""
        Path(savedir + "/" + str(month)).mkdir(parents=True, exist_ok=True)
        plt.subplots_adjust(**dimensions)

        fig.savefig(f'{savedir}/{str(month)}/{title}.png')
        # plt.show()
        plt.close()
        print(f"Processed chart: {title}", f'{savedir}/{title}.png')


def show_aps_fixed_date(data, column, line=False):
    for building in buildings:
        chart_data = {}
        hours = []
        max_nr_of_users_aps = get_or_generate_top_aps_data(data, 'NoOfUsers', building, 1, None)
        ap = max_nr_of_users_aps['apName'].unique()[0]
        avgs = {}
        for date in dates:
            helper = []
            building_data = get_or_generate_file_fixed_date(data, column, date, ap)
            chart_data[date] = []
            for index, b_data in building_data.iterrows():
                if not b_data['hour'] in hours:
                    hours.append(b_data['hour'])
                chart_data[date].append(b_data['avg'])
                helper.append(b_data['avg'])
            avgs[date] = sum(helper) / len(helper)
        x = [h if i % 2 else " " for i, h in enumerate(hours)]
        if not line:
            fig, ax = plt.subplots()
            print(hours)
            index = np.arange(len(hours))
            bar_width = 0.30
            opacity = 0.8
            for i, date in enumerate(chart_data.keys()):
                color, pos = get_color(i, index, bar_width)
                rects = plt.bar(
                    pos,
                    chart_data[date],
                    bar_width,
                    alpha=opacity,
                    color=color,
                    label=date)

            ax.xaxis_date()
            ax.autoscale(tight=False)
            plt.xticks(index, x)
            plt.gcf().autofmt_xdate()
            plt.legend()
        else:
            for index, date in enumerate(chart_data.keys()):
                vals = chart_data[date]
                color, pos = get_color(index, 0, 0)
                plt.plot(hours, vals, color=color, linewidth=2)
            plt.xticks(x)
        plt.title(column + " dla AP" + ap + " w budynku " + building)

        plt.gcf().autofmt_xdate()
        # plt.ylabel("Wykorzystanie kanału %")
        plt.show()


def show_counter_aps(data, column):
    for building in buildings:
        building_data = get_or_generate_hourly_counter_file(data, column, building)
        max_nr_of_users_aps = get_or_generate_top_aps_data(data, 'NoOfUsers', building, 1, None)
        chart_data = {}
        avgs = {}
        aps = max_nr_of_users_aps['apName'].unique()
        for ap in aps:
            helper = []
            ap_data = building_data[building_data['apName'] == ap]
            chart_data[ap] = {}
            for index, b_data in ap_data.iterrows():
                chart_data[ap][b_data['hour']] = b_data['avg']
                helper.append(b_data['avg'])
            avgs[ap] = sum(helper) / len(helper)

        for i in range(0, len(aps)):
            ap = (max(avgs, key=avgs.get))
            avgs[ap] = 0
            hours = [k for k in chart_data[ap].keys()]
            x = [h for i, h in enumerate(hours) if i % 2]
            vals = [chart_data[ap][hour] for hour in chart_data[ap]]
            color, pos = get_color(i, 0, 0)
            bars = plt.bar(hours, vals)
            for bar in bars:
                bar.set_color(color)
            plt.gcf().autofmt_xdate()
            plt.xticks(x)
        plt.title(column + " dla 5 najbardziej używanych AP w " + building)
        plt.legend(aps)
        plt.show()


def show_ratio_ap(data, column1, column2, counter=False, month=None, column_line=None, max_val=None):
    for building in buildings:
        if counter:
            data1 = get_or_generate_hourly_counter_file(data, column1, building)
            data2 = get_or_generate_hourly_counter_file(data, column2, building)
        else:
            data1 = get_or_generate_building_file(data, column1, building, month=month)
            data2 = get_or_generate_building_file(data, column2, building, month=month)
            if column_line is not None:
                data_line = get_or_generate_building_file(data, column_line, building, month=month)
        max_nr_of_users_aps = get_or_generate_top_aps_data(data, 'NoOfUsers', building, 1, None)
        aps = max_nr_of_users_aps['apName'].unique()
        chart_data = {}
        line_data = {}
        hours = []
        for i, ap in enumerate(aps):
            helper = []
            ap_data1 = data1[data1['apName'] == ap]
            ap_data2 = data2[data2['apName'] == ap]
            if column_line is not None:
                data_line_ap = data_line[data_line['apName'] == ap]
            chart_data[ap] = []
            line_data[ap] = []
            for index, a_data in ap_data1.iterrows():
                hour = a_data['hour']
                if not hour in hours:
                    hours.append(hour)
                b_data = ap_data2[ap_data2['hour'] == hour].iloc[0]
                chart_data[ap].append((a_data['avg'] / b_data['avg']))
                if column_line is not None:
                    row = data_line_ap[data_line['hour'] == hour].iloc[0]
                    line_data[ap].append(row['avg'] / 100)
                else:
                    line_data[ap].append(0)
                # helper.append(b_data['avg'])

        # create plot
        fig = plt.figure()
        for i, ap in enumerate(aps):
            x = [h for i, h in enumerate(hours) if i % 2]
            vals = chart_data[ap]
            # color, pos = get_color(i, 0, 0)
            bars = plt.bar(hours, vals)
            plt.gcf().autofmt_xdate()
            max_vals = [max(vals), max(line_data[ap])]
            if max_val is not None:
                plt.ylim(0.0, max_val)
            else:
                plt.ylim(0.0, max(max_vals) + 0.1)
            plt.xticks(x)
            plt.plot(hours, line_data[ap], color="r")
        plt_title = ("Miesiąc " + str(month) + " ") if month is not None else ""
        plt_title += column1 + ":" + column2
        plt_title += ", " + column_line if column_line is not None else ""
        plt_title += ' dla ' + aps[0]
        plt.title(plt_title)
        # plt.legend(aps)
        # plt.ylabel("Wykorzystanie kanału %")
        # plt.show()

        title = str(month) + "-" + column1 + "_" + column2
        title += ", " + column_line if column_line is not None else ""
        title += "-" + aps[0]
        title = title.replace('.', '_')
        Path(savedir + "/" + str(month)).mkdir(parents=True, exist_ok=True)
        plt.subplots_adjust(**dimensions)

        fig.savefig(f'{savedir}/{str(month)}/{title}.png')
        # plt.show()
        plt.close()
        plt.show()


def show_ratio_ap_fixed_date(data, column1, column2, counter=False):
    for building in buildings:
        max_nr_of_users_aps = get_or_generate_top_aps_data(data, 'NoOfUsers', building, 1, None)
        ap = max_nr_of_users_aps['apName'].unique()[0]
        chart_data = {}
        hours = []
        for date in dates:
            data1 = get_or_generate_file_fixed_date(data, column1, date, ap, counter)
            data2 = get_or_generate_file_fixed_date(data, column2, date, ap, counter)
            chart_data[date] = []
            for index, a_data in data1.iterrows():
                hour = a_data['hour']
                if not hour in hours:
                    hours.append(hour)
                b_data = data2[data2['hour'] == hour].iloc[0]
                chart_data[date].append((a_data['avg'] / b_data['avg']))
        x = [h if i % 2 else " " for i, h in enumerate(hours)]
        fig, ax = plt.subplots()
        index = np.arange(len(hours))
        bar_width = 0.30
        opacity = 0.8
        for i, date in enumerate(chart_data.keys()):
            color, pos = get_color(i, index, bar_width)
            rects = plt.bar(
                pos,
                chart_data[date],
                bar_width,
                alpha=opacity,
                color=color,
                label=date)

        ax.xaxis_date()
        ax.autoscale(tight=False)
        plt.xticks(index, x)
        plt.gcf().autofmt_xdate()
        plt.legend()
        plt.title("Stosunek " + column1 + " do " + column2 + " dla " + ap)
        plt.show()


def show_counter_ratio_month_data(data, column1, column2):
    for building in buildings:
        generated_data1 = get_or_generate_monthly_hour_counter_file(data, column1, building)
        generated_data2 = get_or_generate_monthly_hour_counter_file(data, column2, building)

        max_nr_of_users_aps = get_or_generate_top_aps_data(data, 'NoOfUsers', building, 1, None)
        ap = max_nr_of_users_aps['apName'].unique()[0]
        chart_data = {}
        hours = {}
        generated_data1 = generated_data1[generated_data1['apName'] == ap]
        generated_data2 = generated_data2[generated_data2['apName'] == ap]
        for month in months:

            month_data1 = generated_data1[generated_data1['month'] == month]
            month_data2 = generated_data2[generated_data2['month'] == month]
            chart_data["{:02d}".format(month)] = []
            hours["{:02d}".format(month)] = []
            for index, a_data in month_data1.iterrows():
                hour = a_data['hour']
                b_data = month_data2[month_data2['hour'] == hour].iloc[0]
                chart_data["{:02d}".format(month)].append((a_data['avg'] / b_data['avg']))
                if not hour in hours["{:02d}".format(month)]:
                    hours["{:02d}".format(month)].append(hour)
        fig = plt.figure()
        for month in chart_data:
            x = [h if i % 2 else " " for i, h in enumerate(hours[month])]
            vals = chart_data[month]
            # color, pos = get_color(i, 0, 0)
            bars = plt.bar(hours[month], vals)
            plt.gcf().autofmt_xdate()
            plt.xticks(x)
            plt.title("Miesiąc " + month + ", " + column1 + ": " + column2 + ", " + ap)
            # plt.legend()
            # plt.show()
            title = str(month) + "-" + column1 + "_" + column2 + "-" + ap
            title = title.replace('.', '_')
            Path(savedir + "/" + str(int(month))).mkdir(parents=True, exist_ok=True)
            plt.subplots_adjust(**dimensions)
            fig.savefig(f'{savedir}/{str(int(month))}/{title}.png')
            plt.close()
            print(f"Processed chart: {title}" + f'{savedir}/{title}.png')


def show_counter_month_data(data, column):
    for building in buildings:
        generated_data = get_or_generate_monthly_hour_counter_file(data, column, building)
        max_nr_of_users_aps = get_or_generate_top_aps_data(data, 'NoOfUsers', building, 1, None)
        ap = max_nr_of_users_aps['apName'].unique()[0]
        chart_data = {}
        hours = {}
        ap_data = generated_data[generated_data['apName'] == ap]
        for month in months:
            month_data = ap_data[ap_data['month'] == month]
            helper = []
            chart_data["{:02d}".format(month)] = []
            hours["{:02d}".format(month)] = []
            for index, b_data in month_data.iterrows():
                chart_data["{:02d}".format(month)].append(b_data['avg'])
                hour = b_data['hour']
                if not hour in hours["{:02d}".format(month)]:
                    hours["{:02d}".format(month)].append(hour)

        for month in chart_data:
            fig = plt.figure()
            x = [h if i % 2 else " " for i, h in enumerate(hours[month])]
            vals = chart_data[month]
            # color, pos = get_color(i, 0, 0)
            bars = plt.bar(hours[month], vals)
            print('*****', month, ' **** ', hours[month], vals)
            plt.gcf().autofmt_xdate()
            plt.xticks(x)
            plt.title("Miesiąc " + month + ", " + column + ", " + ap)
            # plt.legend()
            # plt.show()
            title = str(month) + "-" + column + "-" + ap
            title = title.replace('.', '_')
            Path(savedir + "/" + str(int(month))).mkdir(parents=True, exist_ok=True)
            plt.subplots_adjust(**dimensions)
            fig.savefig(f'{savedir}/{str(int(month))}/{title}.png')
            plt.close()
            print(f"Processed chart: {title}" + f'{savedir}/{title}.png')


def get_color(i, index, bar_width):
    """if i % 5 == 0:
        color = '#581845'
        color="m"
        pos = index + 2 * bar_width
    elif i % 4 == 0:
        color = '#900c3f'
        color="b"
        pos = index + bar_width
    elif i % 3 == 0:
        color = '#c70039'
        color="c"
        pos = index
    elif i % 2 == 0:
        color = '#ff5733'
        pos = index - bar_width
    else:
        color = '#ffc300'
        color="g"
        pos = index - 2 * bar_width"""
    if i == 0:
        color = "m"
        pos = index - bar_width
    elif i == 1:
        color = '#900c3f'
        color = "g"
        pos = index
    elif i == 2:
        color = '#c70039'
        color = "r"
        pos = index + bar_width

    return color, pos


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
# generate_charts_for_building_stats()

data = pd.read_csv(filepath_or_buffer='complete_data.csv', index_col=False)
# data = None
# show_aps_with_max_column(data,'NoOfUsers', True)
# show_aps_with_max_column(data,'LoadChannelUtilization', True)
for month in months:
    # show_aps_nr_users(data, 'NoOfUsers', month=month, max_val=45)
    show_aps_nr_users(data, 'LoadChannelUtilization', line=True, month=month)
    # show_aps_nr_users(data, 'PoorSNRClients', month=month,  max_val=20)
    show_ratio_ap(data, 'PoorSNRClients', 'NoOfUsers', False, month, column_line='LoadChannelUtilization', max_val=0.8)

# show_counter_month_data(data,'Dot11FailedCount')
# show_counter_month_data(data,'Dot11TransmittedFrameCount')
# show_counter_ratio_month_data(data,'Dot11FailedCount', 'Dot11TransmittedFrameCount')
# show_counter_month_data(data,'Dot11FCSErrorCount')
# show_counter_ratio_month_data(data,'Dot11FCSErrorCount', 'Dot11TransmittedFrameCount')
# show_ratio_poor_to_all_users_ap(data)
# show_counter_aps(data, 'Dot11FailedCount')
# show_counter_aps(data, 'Dot11TransmittedFrameCount')
# show_aps_fixed_date(data, 'NoOfUsers', line=False)
# show_aps_fixed_date(data, 'LoadChannelUtilization',  line=False)
# show_aps_fixed_date(data, 'PoorSNRClients', line=False)

# show_ratio_ap_fixed_date(data, 'Dot11FailedCount','Dot11TransmittedFrameCount' , True)
# show_ratio_ap_fixed_date(data, 'PoorSNRClients','NoOfUsers', False)
"""for building in buildings:
    mh = get_or_generate_monthly_hour_counter_file(data, 'Dot11FailedCount', building)
    m = get_or_generate_monthly_counter_file(data, 'Dot11FailedCount', building)
    h = get_or_generate_hourly_counter_file(data, 'Dot11FailedCount', building)"""
