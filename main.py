import sys

import pandas as pd
import calendar
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
import seaborn as sns

months = [1, 2, 3, 4, 5, 6, 10, 11, 12]
years = [2015, 2016]

start_at = "07-30"
end_at = "20-30"
ignore_AP_regex = 'AP-jgora|AP-walbrzych|AP-Legnica|Ustka|-GEO-'


def numericdatetostringdate(year, month, day=0):
    if month < 10:
        string_month = '0' + str(month)
    else:
        string_month = str(month)
    if day:
        if day < 10:
            string_day = '0' + str(day)
        else:
            string_day = str(day)
        string_date = str(year) + '-' + string_month + '-' + string_day
    else:
        string_date = str(year) + '-' + string_month
    return string_date


def load_data_from_source():
    file = open('data_location.cfg')
    data_location = file.readline()
    data_location = data_location.split(';')[0]
    data_column_names = file.readline().split(';')[:-1]
    file.close()
    data_dict = {}
    td = timedelta(minutes=20)
    c = calendar.Calendar()
    for year in years:
        for month in months:
            for day in c.itermonthdays(year, month):
                # print(day)
                if day:
                    data_file_name = data_location + '/' + numericdatetostringdate(year,
                                                                                   month) + '/statystyki-wifi-' + numericdatetostringdate(
                        year, month, day) + '.csv'
                    try:
                        start_time = datetime.strptime(str(year) + "-" + str(month) + "-" + str(day) + "--" + start_at,
                                                       "%Y-%m-%d--%H-%M")
                        end_time = datetime.strptime(str(year) + "-" + str(month) + "-" + str(day) + "--" + end_at,
                                                     "%Y-%m-%d--%H-%M")
                        data = pd.read_csv(filepath_or_buffer=data_file_name, sep=';', index_col=False, header=0,
                                           names=data_column_names)
                        extracted_data = None
                        curr_date = start_time
                        while curr_date <= end_time:
                            curr_time_data = data[
                                data['dataPomiaru'] == datetime.strftime(curr_date, "%Y-%m-%d--%H-%M")]
                            curr_time_data = curr_time_data[
                                ~curr_time_data['apName'].str.contains(ignore_AP_regex, na=False)]
                            extracted_data = curr_time_data if extracted_data is None else extracted_data.append(
                                curr_time_data)
                            curr_date += td
                        data_dict[numericdatetostringdate(year, month, day)] = extracted_data
                    except FileNotFoundError:
                        print(numericdatetostringdate(year, month, day) + " is missing")
    return data_dict


def concatenate_tables(data_dict):
    data = None
    for data_day in data_dict.values():
        if data is None:
            data = data_day
        else:
            data.append(data_day, ignore_index=True)
    return data


def get_monthly_data(data, column, building=None):
    # buildings_to_search= ['A1-', 'B4']
    buildings_to_search = ["A1-", "A4-", "A5-", "A10-",
                           "B1-", "B4-", "B5-", "B8-", "B9-",
                           "C2-", "C3-", "C4-", "C5-", "C6-", "C7-", "C11-", "C13-", "C16-",
                           "D1-", "D2-"]
    if not building is None:
        buildings_to_search = [building + "-"]
    summary = {}
    for month in months:
        summary["{:02d}".format(month)] = {}
    data = data[['apName', 'dataPomiaru', column]]
    uniqueAP = data['apName'].unique()
    aps_to_search = [uap for uap in uniqueAP if type(uap) == str and any(bts in uap for bts in buildings_to_search)]
    for index, ap in enumerate(aps_to_search):
        print(index, 'out of', len(aps_to_search))
        for month in months:
            current_month = "{:02d}".format(month)
            ap_data = data[data['apName'] == ap]
            ap_data = ap_data[ap_data['dataPomiaru'].str.contains(r"\d{4}-" + current_month + r"-\d{2}--")]
            column_values = [cv for cv in ap_data[column].tolist() if str(cv) != 'nan']
            summary[current_month][ap] = {}
            summary[current_month][ap]['max'] = max(column_values) if len(column_values) else 0
            summary[current_month][ap]['min'] = min(column_values) if len(column_values) else 0
            summary[current_month][ap]['avg'] = (sum(column_values) / len(column_values)) if len(column_values) else 0
    return summary


def get_hourly_data(data, column, building=None, month=None):
    building += "-"
    td = timedelta(minutes=20)
    curr_time = datetime.strptime(start_at, "%H-%M")
    end_time = datetime.strptime(end_at, "%H-%M")
    summary = {}
    hours = []
    while curr_time <= end_time:
        hours.append("{:02d}".format(curr_time.hour) + "-" + "{:02d}".format(curr_time.minute))
        curr_time += td
    data = data[['apName', 'dataPomiaru', column]]
    uniqueAP = data['apName'].unique()
    aps_to_search = [uap for uap in uniqueAP if type(uap) == str and building in uap]
    print(aps_to_search)
    if month is not None:
        data = data[data['dataPomiaru'].str.contains(r"\d{4}-" + "{:02d}".format(month) + r"-\d{2}--")]
    for index, ap in enumerate(aps_to_search):
        ap_data = data[data['apName'] == ap]
        print(index, 'out of', len(aps_to_search))
        summary[ap] = {}
        for hour in hours:
            hour_data = ap_data[ap_data['dataPomiaru'].str.contains(r"--" + hour)]
            column_values = [cv for cv in hour_data[column].tolist() if str(cv) != 'nan']
            summary[ap][hour] = {}
            summary[ap][hour]['max'] = max(column_values) if len(column_values) else 0
            summary[ap][hour]['min'] = min(column_values) if len(column_values) else 0
            summary[ap][hour]['avg'] = (sum(column_values) / len(column_values)) if len(column_values) else 0
    return summary


def get_monthly_counter_data(data, column, building):
    building += "-"
    data = data[['apName', 'dataPomiaru', column]]
    uniqueAP = data['apName'].unique()
    aps_to_search = [uap for uap in uniqueAP if type(uap) == str and building in uap]
    print(aps_to_search)
    summary = {}
    monthly_hourly = {}
    final_data = {}
    c = calendar.Calendar()
    for ap in aps_to_search:
        summary[ap] = {}
        for year in years:
            summary[ap][year] = {}
            for monthl in months:
                month = "{:02d}".format(monthl)
                summary[ap][year][month] = {}
                for dayl in c.itermonthdays(year, monthl):
                    # print(day)
                    day = "{:02d}".format(dayl)
                    summary[ap][year][month][day] = {}

    for index, ap in enumerate(aps_to_search):
        ap_data = data[data['apName'] == ap]
        for year in years:
            for monthl in months:
                month = "{:02d}".format(monthl)
                for dayl in c.itermonthdays(year, monthl):
                    day = "{:02d}".format(dayl)
                    curr_data = ap_data[ap_data['dataPomiaru'].str.contains(
                        str(year) + "-" + month + "-" + day)]
                    for i, row in curr_data.iterrows():
                        hour = row['dataPomiaru'].split("--")[1]
                        if str(row[column]) != 'nan':
                            summary[ap][year][month][day][hour] = row[column]
    for ap in summary:
        monthly_hourly[ap] = {}
        for year in summary[ap]:
            for month in summary[ap][year]:
                if not month in monthly_hourly[ap]:
                    monthly_hourly[ap][month] = {}
                for day in summary[ap][year][month]:
                    current_counter = 0
                    for index, hour in enumerate(summary[ap][year][month][day]):
                        if not current_counter == 0:
                            if not hour in monthly_hourly[ap][month]:
                                monthly_hourly[ap][month][hour] = []
                            monthly_hourly[ap][month][hour].append(
                                summary[ap][year][month][day][hour] - current_counter)
                        current_counter = summary[ap][year][month][day][hour]

    for ap in monthly_hourly:
        final_data[ap] = {}
        for month in monthly_hourly[ap]:
            final_data[ap][month] = {}
            for hour in monthly_hourly[ap][month]:
                final_data[ap][month][hour] = {}
                final_data[ap][month][hour]['avg'] = (
                            sum(monthly_hourly[ap][month][hour]) / len(monthly_hourly[ap][month][hour])) if len(
                    monthly_hourly[ap][month][hour]) else 0
                final_data[ap][month][hour]['max'] = max(monthly_hourly[ap][month][hour]) if len(
                    monthly_hourly[ap][month][hour]) else 0
    return final_data


def get_max_from_data(data, max_field='avg', no_of_max=10):
    data_max = {}
    for month in months:
        monthly_data = data[data['month'] == month]
        data_max[month] = {}
        for index, row in monthly_data.iterrows():
            try:
                curr_max = data_max[month].keys()
                val = row[max_field]
                if len(curr_max) < no_of_max:
                    data_max[month][val] = row['apName']
                else:
                    if any(float(cm) < val for cm in curr_max):
                        data_max[month][val] = row['apName']
                        del data_max[month][min(curr_max)]
            except KeyError as ke:
                print(str(ke))
    return data_max


def get_total_max_from_data(data, max_field='avg', edge_val=None, no_of_max=10):
    data_max = {}
    result = {}
    data = data[['apName', max_field]]
    for index, item in data.iterrows():
        if not item['apName'] in data_max:
            data_max[item['apName']] = item[max_field]
        elif item[max_field] > data_max[item['apName']]:
            data_max[item['apName']] = item[max_field]
    if edge_val is not None:
        for ap in data_max:
            if data_max[ap] >= edge_val:
                result[ap] = data_max[ap]
    else:
        for i in range(0, no_of_max):
            max_val = (max(data_max, key=data_max.get))
            result[max_val] = data_max[max_val]
            data_max[max_val] = 0
    return result


def get_ratio_of_columns(data, column_a, column_b):
    ratio_summary = {}
    data_a = get_or_generate_file(data, column_a)
    data_b = get_or_generate_file(data, column_b)
    for month in months:
        ratio_summary[month] = {}
        monthly_data_a = data_a[data_a['month'] == month]
        monthly_data_b = data_b[data_b['month'] == month]
        for index, row in monthly_data_a.iterrows():
            try:
                ap = row['apName']
                db = monthly_data_b[monthly_data_b['apName'] == ap]
                ratio_summary[month][ap] = {}
                ratio_summary[month][ap]['max'] = float(row['max']) / float(db['max']) if int(db['max']) != 0 else 0
                ratio_summary[month][ap]['min'] = float(row['min']) / float(db['min']) if int(db['min']) != 0 else 0
                ratio_summary[month][ap]['avg'] = float(row['avg']) / float(db['avg']) if int(db['avg']) != 0 else 0
            except Exception as e:
                print(str(e))
    return ratio_summary


def get_or_generate_file(data, column_a, column_b=None, building=None):
    filename = column_a + "-" + building
    # filename+= ('-'+ column_b) if not column_b == None else ''
    filename += '-monthly.csv'
    try:
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    except FileNotFoundError:
        generated_data = get_monthly_data(data, column_a, building) if column_b == None else get_ratio_of_columns(data,
                                                                                                                  column_a,
                                                                                                                  column_b)
        with open(filename, 'w') as generated_file:
            generated_file.write('month' + ',' + 'apName' + ',' + 'max' + ',' + 'min' + ',' + 'avg\n')
            for month in generated_data:
                for ap in generated_data[month]:
                    generated_file.write(
                        str(month) + ','
                        + ap + ','
                        + str(generated_data[month][ap]['max']) + ','
                        + str(generated_data[month][ap]['min']) + ','
                        + str(generated_data[month][ap]['avg'])
                        + "\n"
                    )
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


def get_or_generate_building_file(data, column_a, building, limit=None, month=None):
    filename = column_a + "-" + building
    filename += ("-month-" + str(month)) if month is not None else ""
    filename += ("-top_" + str(limit)) if limit is not None else ""
    filename += '-hourly.csv'
    try:
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    except FileNotFoundError:
        generated_data = get_hourly_data(data, column_a, building=building, month=month)
        aps_to_write = []
        if limit is not None:
            aps_avg = {}
            for ap in generated_data:
                helper = []
                for hour in generated_data[ap]:
                    helper.append(generated_data[ap][hour]['avg'])
                aps_avg[ap] = (sum(helper) / len(helper)) if len(helper) > 0 else 0
            for i in range(0, limit):
                ap_max = max(aps_avg, key=aps_avg.get)
                aps_to_write.append(ap_max)
                del aps_avg[ap_max]

        with open(filename, 'w') as generated_file:
            generated_file.write('apName' + ',' + 'hour' + ',' + 'max' + ',' + 'min' + ',' + 'avg\n')
            for ap in generated_data:
                for hour in generated_data[ap]:
                    if limit is None or ap in aps_to_write:
                        generated_file.write(
                            ap + ','
                            + hour + ','
                            + str(generated_data[ap][hour]['max']) + ','
                            + str(generated_data[ap][hour]['min']) + ','
                            + str(generated_data[ap][hour]['avg'])
                            + "\n"
                        )
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


def get_or_generate_building_file_each_month(data, column_a, building, limit=None):
    data = {}
    for month in months:
        data["{:02d}".format(month)] = get_or_generate_building_file(data, column_a, building, month=month)
    return data


def get_or_generate_monthly_hour_counter_file(data, column, building):
    filename = column + "-" + building
    filename += '-monthly-hourly.csv'
    try:
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    except FileNotFoundError:
        monthly_hourly = get_monthly_counter_data(data, column, building)
        with open(filename, 'w') as generated_file:
            generated_file.write('apName' + ',' + 'month' + ',' + 'hour' + ',' + 'max' + ',' + 'avg\n')
            for ap in monthly_hourly:
                for month in monthly_hourly[ap]:
                    for hour in monthly_hourly[ap][month]:
                        generated_file.write(
                            ap + ','
                            + month + ','
                            + hour + ','
                            + str(monthly_hourly[ap][month][hour]['max']) + ','
                            + str(monthly_hourly[ap][month][hour]['avg'])
                            + "\n"
                        )
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


def get_or_generate_monthly_counter_file(data, column, building):
    filename = column + "-" + building
    filename += '-monthly.csv'
    try:
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    except FileNotFoundError:
        monthly_hourly = get_monthly_counter_data(data, column, building)
        final_data = {}
        for ap in monthly_hourly:
            final_data[ap] = {}
            for month in monthly_hourly[ap]:
                final_data[ap][month] = []
                for hour in monthly_hourly[ap][month]:
                    final_data[ap][month].append(monthly_hourly[ap][month][hour])
        with open(filename, 'w') as generated_file:
            generated_file.write('apName' + ',' + 'month' + ',' + 'max' + ',' + 'avg\n')
            for ap in final_data:
                for month in final_data[ap]:
                    avg_vals = [v['avg'] for v in final_data[ap][month]]
                    max_vals = [v['max'] for v in final_data[ap][month]]
                    generated_file.write(
                        ap + ','
                        + month + ','
                        + str(max(max_vals) if len(max_vals) > 0 else 0) + ','
                        + str((sum(avg_vals) / len(avg_vals)) if len(avg_vals) > 0 else 0)
                        + "\n"
                    )
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


def get_or_generate_hourly_counter_file(data, column, building):
    filename = column + "-" + building
    filename += '-hourly.csv'
    try:
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    except FileNotFoundError:
        monthly_hourly = get_monthly_counter_data(data, column, building)
        final_data = {}
        for ap in monthly_hourly:
            final_data[ap] = {}
            for month in monthly_hourly[ap]:
                for hour in monthly_hourly[ap][month]:
                    if not hour in final_data[ap]:
                        final_data[ap][hour] = []
                    final_data[ap][hour].append(monthly_hourly[ap][month][hour])
        with open(filename, 'w') as generated_file:
            generated_file.write('apName' + ',' + 'hour' + ',' + 'max' + ',' + 'avg\n')
            for ap in final_data:
                for hour in final_data[ap]:
                    avg_vals = [v['avg'] for v in final_data[ap][hour]]
                    max_vals = [v['max'] for v in final_data[ap][hour]]
                    generated_file.write(
                        ap + ','
                        + hour + ','
                        + str(max(max_vals) if len(max_vals) > 0 else 0) + ','
                        + str((sum(avg_vals) / len(avg_vals)) if len(avg_vals) > 0 else 0)
                        + "\n"
                    )
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


def get_or_generate_top_aps_data(data, column, building, nr_of_max, edge_val):
    filename = 'APS-max-' + column + '-' + building + '.csv'
    try:
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    except FileNotFoundError:
        gen_data = get_or_generate_file(data, column, building=building)
        max_data = get_total_max_from_data(gen_data, no_of_max=nr_of_max, edge_val=edge_val)
        with open(filename, 'w') as report:
            report.write('apName,' + column + '\n')
            for ap in max_data:
                report.write(str(ap) + ',' + str(max_data[ap]) + '\n')
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


try:
    data = pd.read_csv(filepath_or_buffer='complete_data.csv', index_col=False)
    # no_users=get_or_generate_file(data, 'NoOfUsers')
    # poor_users = get_or_generate_file(data, 'PoorSNRClients')
    # ratio_users = get_or_generate_file(data, 'PoorSNRClients', 'NoOfUsers')
    # max_no_users = get_max_from_data(no_users)
    # max_poor_users = get_max_from_data(poor_users)
    # max_ratio_users = get_max_from_data(ratio_users)
    # with open('report.txt' , 'w') as report:
    #     for month in months:
    #         report.write('****  Month :  ' + str(month) +"\n")
    #         report.write(" AP with maximum average nr of users: \n")
    #         for mnu  in max_no_users[month]:
    #             report.write(str(max_no_users[month][mnu]) +" : " + str(mnu) +"\n")
    #         report.write("\n AP with maximum average nr of poor snr users : \n")
    #         for mpu  in max_poor_users[month]:
    #             report.write(str(max_poor_users[month][mpu]) +" : " + str(mpu) +"\n")
    #         report.write("\n AP with Max ratio of poor to all users: \n")
    #         for mru  in max_ratio_users[month]:
    #             report.write(str(max_ratio_users[month][mru]) +" : " + str(mru) +"\n")
    #         report.write('\n\n')

    # print(max_no_users)

except FileNotFoundError:
    data = load_data_from_source()
    with open('complete_data.csv', 'w') as data_file:
        for index, data_day in enumerate(data.values()):
            if index == 0:
                data_file.write(data_day.to_csv(index=False))
            else:
                data_file.write(data_day.to_csv(index=False, header=None))

# data['dataPomiaru'] = pd.to_datetime(data['dataPomiaru'])
# dupa = data['NoOfUsers'].resample('M', how='sum')
# print(dupa)
# print(type(dupa))
# print(type(data))
# data.factorplot("NoUsers")


poor_clients_monthly = pd.read_csv(filepath_or_buffer='PoorSNRClients-monthly.csv', index_col=False)
poor_clients_and_users_monthly = pd.read_csv(filepath_or_buffer='PoorSNRClients-NoOfUsers-monthly.csv', index_col=False)

users_monthly = pd.read_csv(filepath_or_buffer='NoOfUsers-monthly.csv', index_col=False)

usage_monthly = pd.read_csv(filepath_or_buffer='dupaMaryni.csv', index_col=False)
# Just so rows get sorted by the building
users_monthly = users_monthly.sort_values(by=['apName'])
poor_clients_monthly = poor_clients_monthly.sort_values(by=['apName'])
poor_clients_and_users_monthly = poor_clients_and_users_monthly.sort_values(by=['apName'])
usage_monthly = usage_monthly.sort_values(by=['apName'])

users_monthly = users_monthly.loc[users_monthly['apName'].isin(['AP-A1-acf2.c585.6e0f',
                                                                'AP-A1-acf2.c585.6c9f',
                                                                'AP-A1-acf2.c593.f1a7',
                                                                'AP-B4-acf2.c571.83c3',
                                                                'AP-B4-acf2.c573.28c0',
                                                                'AP-B4-acf2.c585.8483',
                                                                ])]

no_of_users_avg = sns.catplot(x='month', y='avg', data=users_monthly, hue='apName', legend_out=True, kind='bar')
# Setting new legend with columns
# handles, labels = catp.axes[0][0].get_legend_handles_labels()
# catp.axes[0][0].legend_.remove()
# catp.fig.legend(handles=handles, labels=labels, ncol=3, loc=8)
# Changing labels to something sensible
no_of_users_avg._legend.set_title('Identyfikator AP')
no_of_users_avg.set(title="Średnia ilość użytkowników na AP", xlabel='Miesiąc', ylabel='Średnia liczba użytkowników')

# # Melting data so now attributes 'avg' 'max' and 'min' are values of a new 'property' attribute
# filtered_users_monthly = users_monthly.filter(items=['month', 'apName', 'avg', 'max'])
# melted_users_monthly = filtered_users_monthly.melt(id_vars=['month', 'apName'], var_name='property', value_name='value')
# melted_users_monthly = melted_users_monthly.sort_values(by=['apName'])
#
# relp = sns.catplot(
#     x='month',
#     y='value',
#     col='property',
#     hue='apName',
#     col_wrap=2,
#     data=melted_users_monthly,
#     # facet_kws=dict(legend_out=False),
# )
# relp.set_axis_labels("Miesiąc", "")
# print(relp.__dict__)
# # Setting new legend with columns
# # handles, labels = relp.axes[0].get_legend_handles_labels()
# # relp.axes[0].legend_.remove()
# # relp.fig.legend(handles=handles, labels=labels, ncol=3, loc=9)#, bbox_to_anchor=(0., 0., 0., 0.))

poor_clients_monthly = poor_clients_monthly.loc[poor_clients_monthly['apName'].isin(['AP-B4-acf2.c571.83c3',
                                                                'AP-B4-acf2.c573.28c0',
                                                                'AP-B4-acf2.c585.8483',
                                                                'AP-A1-acf2.c593.f1a7',
                                                                'AP-B4-acf2.c573.3aae',
                                                                ])]

bad_connection_avg = sns.catplot(x='month', y='avg', data=poor_clients_monthly, hue='apName', legend_out=True, kind='bar')
# Setting new legend with columns
# handles, labels = catp.axes[0][0].get_legend_handles_labels()
# catp.axes[0][0].legend_.remove()
# catp.fig.legend(handles=handles, labels=labels, ncol=3, loc=8)
# Changing labels to something sensible
bad_connection_avg._legend.set_title('Identyfikator AP')
bad_connection_avg.set(title="Średnia liczba użytkowników ze słabym połączeniem", xlabel='Miesiąc', ylabel='Średnia ilość użytkowników na AP')

poor_clients_and_users_monthly = poor_clients_and_users_monthly.loc[poor_clients_and_users_monthly['apName'].isin([
    'AP-A1-acf2.c585.6e2a',
    'AP-B4-acf2.c571.83c3',
    'AP-B4-WIZ-p408',
    'AP-A1-acf2.c573.2a1a',
    'AP-B4-acf2.c573.28c0',
    'AP-B4-acf2.c573.39a8',
    'AP-B4-WIZ-p512',
    'AP-A1-centrala',
    'AP-A1-acf2.c585.6e2a',
    'AP-A1-acf2.c585.6e3c',
    'AP-A1-p64',
])]

conn_quality_avg = sns.catplot(x='month', y='avg', data=poor_clients_and_users_monthly, hue='apName', legend_out=True, kind='bar')
# Setting new legend with columns
# handles, labels = catp.axes[0][0].get_legend_handles_labels()
# catp.axes[0][0].legend_.remove()
# catp.fig.legend(handles=handles, labels=labels, ncol=3, loc=8)
# Changing labels to something sensible
conn_quality_avg._legend.set_title('Identyfikator AP')
conn_quality_avg.set(title="Awaryjność połączenia", xlabel='Miesiąc', ylabel='Awaryjność [%]')

usage_monthly = usage_monthly.loc[usage_monthly['apName'].isin([
    'AP-B4-WIZ-p448',
    'AP-DI-B4-osiecki',
    'AP-A1-acf2.c585.6c9f',
    'AP-B4-WIZ-c464.1338.bb10',
    'AP-A1-p64',
    'AP-A1-acf2.c585.6b5c',
    'AP-B4-acf2.c573.28c0',
])]

usage_avg = sns.catplot(x='month', y='avg', data=usage_monthly, hue='apName', legend_out=True, kind='bar')
# Setting new legend with columns
# handles, labels = catp.axes[0][0].get_legend_handles_labels()
# catp.axes[0][0].legend_.remove()
# catp.fig.legend(handles=handles, labels=labels, ncol=3, loc=8)
# Changing labels to something sensible
usage_avg._legend.set_title('Identyfikator AP')
usage_avg.set(title="Wykorzystanie kanału", xlabel='Miesiąc', ylabel='Wykorzystanie [%]')

# Show me the money!
plt.show()
