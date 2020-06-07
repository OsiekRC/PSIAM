import pandas as pd
import calendar
from datetime import timedelta, datetime

months = [1, 2, 3, 4, 5, 6, 10, 11, 12]
years = [2015, 2016]
start_at = "07-30"
end_at = "20-30"
hours = ["07-30", "08-30", "09-30", "10-30", "11-30", "12-30", "13-30", "14-30", "15-30", "16-30", "17-30",
         "18-30", "19-30", "20-30"]
hours = []
ignore_AP_regex = 'AP-jgora|AP-walbrzych|AP-Legnica|Ustka|-GEO-'
buildings = {
    "A": ["A1"],  # ,"A4","A5","A10"],
    "B": ["B4"]  # ["B1","B4","B5","B8", "B9"],
    # "C" : ["C2","C3","C4", "C6", "C7", "C11", "C13", "C16"],
    # "D" : ["D1","D2"]
}
# fields to generate stats from and also info if they're percentage value
fields = {
    'NoOfUsers': False,
    'PoorSNRClients': False,
    'LoadChannelUtilization': True,
    # 'LoadTxUtilization' : True,
    # 'LoadRxUtilization' : True,
    # 'Dot11FCSErrorCount': False,
    # 'Dot11FailedCount': False,
    # 'Dot11TransmittedFrameCount': False

}

def gen_hours():
    td = timedelta(minutes=20)
    curr_time = datetime.strptime(start_at, "%H-%M")
    end_time = datetime.strptime(end_at, "%H-%M")
    while curr_time <= end_time:
        hours.append("{:02d}".format(curr_time.hour) + "-" + "{:02d}".format(curr_time.minute))
        curr_time += td


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
                    date = datetime.strptime(numericdatetostringdate(year, month, day), '%Y-%m-%d')
                    if date.weekday() < 5:
                        data_file_name = data_location + '/' + numericdatetostringdate(year,
                                                                                       month) + '/statystyki-wifi-' + numericdatetostringdate(
                            year, month, day) + '.csv'
                        try:
                            start_time = datetime.strptime(
                                str(year) + "-" + str(month) + "-" + str(day) + "--" + start_at, "%Y-%m-%d--%H-%M")
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


def get_monthly_data(data, column, building_to_search, add=True):
    gen_hours()
    # buildings_to_search= ['A1-', 'B4']
    building_to_search += "-"
    summary = {}
    c = calendar.Calendar()
    for month in months:
        summary["{:02d}".format(month)] = {}
        for hour in hours:
            summary["{:02d}".format(month)][hour] = {}

    data = data[['apName', 'dataPomiaru', column]]
    uniqueAP = data['apName'].unique()
    aps_to_search = [uap for uap in uniqueAP if type(uap) == str and (building_to_search in uap)]
    for index, ap in enumerate(aps_to_search):
        print(index, '.' + ap, 'out of', len(aps_to_search))
        ap_data = data[data['apName'] == ap]
        for month in months:
            current_month = "{:02d}".format(month)
            for hour in hours:
                ap_data_hour = ap_data[ap_data['dataPomiaru'].str.contains(
                    r"\d{4}-" + current_month + r"-\d{2}" + "--" + hour)]
                column_values = [cv for cv in ap_data_hour[column].tolist() if str(cv) != 'nan']
                summary[current_month][hour][ap] = {}
                summary[current_month][hour][ap]["max"] = max(column_values) if len(column_values) else 0
                summary[current_month][hour][ap]['avg'] = (sum(column_values) / len(column_values)) if len(
                    column_values) else 0

                # print(month, 'h: ' , hour, column_values)
    return summary


def get_month_ratio_for_building(data, building_to_search, column_a, column_b):
    gen_hours()
    ratio_summary = {}
    data_a = get_or_generate_month_file_for_building(data, building_to_search, column_a)
    data_b = get_or_generate_month_file_for_building(data, building_to_search, column_b)
    for month in months:
        current_month = "{:02d}".format(month)
        ratio_summary[current_month] = {}
        monthly_data_a = data_a[data_a['month'] == month]
        monthly_data_b = data_b[data_b['month'] == month]
        ratios = []
        ratio_summary[current_month] = monthly_data_a.iloc[0]['avg'] / monthly_data_b.iloc[0]['avg'] if \
            monthly_data_b.iloc[0]['avg'] else 0
        """for index, row in monthly_data_a.iterrows():
            row_b= monthly_data_b[monthly_data_b['hour']== row['hour']]
            if len(row_b.index) and row_b.iloc[0]['avg'] !=0:
                ratios.append(row['avg']/row_b.iloc[0]['avg'])
        try:
            ratio_summary[current_month] ={}
            ratio_summary[current_month]['avg'] = sum(ratios) / len(ratios) if len(ratios) else 0
        except Exception as e:
                print(str(e))"""
    return ratio_summary


def get_hour_ratio_for_building(data, building_to_search, column_a, column_b):
    gen_hours()
    ratio_summary = {}
    data_a = get_or_generate_month_hour_file_for_buiding(data, building_to_search, column_a)
    data_b = get_or_generate_month_hour_file_for_buiding(data, building_to_search, column_b)
    for hour in hours:
        ratio_summary[hour] = {}
        monthly_data_a = data_a[data_a['hour'] == hour]
        monthly_data_b = data_b[data_b['hour'] == hour]
        ratios = []
        for index, row in monthly_data_a.iterrows():
            row_b = monthly_data_b[monthly_data_b['month'] == row['month']]
            if len(row_b.index) and row_b.iloc[0]['avg'] != 0:
                ratios.append(row['avg'] / row_b.iloc[0]['avg'])
        try:
            ratio_summary[hour] = {}
            ratio_summary[hour]['avg'] = sum(ratios) / len(ratios) if len(ratios) else 0
        except Exception as e:
            print(str(e))
    return ratio_summary


def get_month_hour_ratio_for_building(data, building_to_search, column_a, column_b):
    gen_hours()
    ratio_summary = {}
    data_a = get_or_generate_month_hour_file_for_buiding(data, building_to_search, column_a)
    data_b = get_or_generate_month_hour_file_for_buiding(data, building_to_search, column_b)
    for month in months:
        current_month = "{:02d}".format(month)
        ratio_summary[current_month] = {}
        monthly_data_a = data_a[data_a['month'] == month]
        monthly_data_b = data_b[data_b['month'] == month]
        for hour in hours:
            ratio_summary[current_month][hour] = {}
            monthly_hourly_data_a = monthly_data_a[monthly_data_a['hour'] == hour]
            monthly_hourly_data_b = monthly_data_b[monthly_data_b['hour'] == hour]
            try:
                ratio_summary[current_month][hour] = {}
                ratio_summary[current_month][hour]['avg'] = (
                    float(monthly_hourly_data_a.iloc[0]['avg']) / float(monthly_hourly_data_b.iloc[0]['avg'])
                    if (len(monthly_hourly_data_b.index) and monthly_hourly_data_b.iloc[0]['avg'] != 0) else 0)
            except Exception as e:
                print(str(e))
    return ratio_summary


# basic, monthly and hourly splitted data for a building
def get_month_hour_data_for_building(data, building_to_search, column, percentage_value=False):
    gen_hours()
    # buildings_to_search= ['A1-', 'B4']
    building_to_search += "-"
    summary = {}
    c = calendar.Calendar()
    for month in months:
        summary["{:02d}".format(month)] = {}
        for hour in hours:
            summary["{:02d}".format(month)][hour] = {}

    data = data[['apName', 'dataPomiaru', column]]
    uniqueAP = data['apName'].unique()
    aps_to_search = [uap for uap in uniqueAP if type(uap) == str and (building_to_search in uap)]
    aps_data = data[data['apName'].str.contains(building_to_search, na=False)]
    for month in months:
        current_month = "{:02d}".format(month)
        print(column, building_to_search, 'month:', current_month, ' aps: ', len(aps_to_search))
        for hour in hours:
            values = {}
            aps_data_hour = aps_data[
                aps_data['dataPomiaru'].str.contains(r"\d{4}-" + current_month + r"-\d{2}" + "--" + hour)]
            for index, adh in aps_data_hour.iterrows():
                if adh['dataPomiaru'] not in values:
                    values[adh['dataPomiaru']] = 0
                if str(adh[column]) != 'nan':
                    values[adh['dataPomiaru']] += adh[column]
            summary[current_month][hour]["avg"] = (sum([v for v in values.values()]) / len(values)) if len(
                values) else 0
            summary[current_month][hour]["max"] = max(values.values()) if len(values) else 0
            if percentage_value:
                summary[current_month][hour]["avg"] /= len(aps_to_search) if len(aps_to_search) else 0
                summary[current_month][hour]["max"] /= len(aps_to_search) if len(aps_to_search) else 0
    return summary


# **************************
# ***  DIVIDED BY MONTHS ***
# **************************

# months avg extracted
def get_or_generate_month_file_for_building(data, building_to_search, column_a, column_b=None):
    gen_hours()
    filename = column_a
    filename += ('-' + column_b) if not column_b is None else ''
    filename += "-" + building_to_search
    filename += '-monthly.csv'
    try:
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    except FileNotFoundError:
        if column_b is not None:
            return generate_month_ratio_file_for_building(data, building_to_search, column_a, column_b)
        generated_data = (get_or_generate_month_hour_file_for_buiding(data, building_to_search, column_a)
                          )
        modified_data = {}
        for month in months:
            current_month = "{:02d}".format(month)
            month_data = generated_data[generated_data['month'] == month]
            modified_data[current_month] = {}
            column_values = [cv for cv in month_data['avg'].tolist() if str(cv) != 'nan']
            modified_data[current_month]['max'] = month_data['max'].max()
            modified_data[current_month]['avg'] = (sum(column_values) / len(column_values)) if len(column_values) else 0
        with open(filename, 'w') as generated_file:
            generated_file.write('month' + ',' + 'max' + ',' + 'avg\n')
            for month in modified_data:
                generated_file.write(
                    month + ','
                    + str(modified_data[month]['max']) + ','
                    + str(modified_data[month]['avg'])
                    + "\n"
                )
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


# month avg for ratios are extracted
def generate_month_ratio_file_for_building(data, building_to_search, column_a, column_b=None):
    gen_hours()
    filename = column_a + "-" + column_b
    filename += "-" + building_to_search
    filename += '-monthly.csv'
    generated_data = get_month_ratio_for_building(data, building_to_search, column_a, column_b)
    with open(filename, 'w') as generated_file:
        generated_file.write('month' + ',' + 'avg\n')
        for month in generated_data:
            generated_file.write(
                month + ','
                + str(generated_data[month])
                + "\n"
            )
    file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


# **************************
# **** DIVIDED BY HOURS ****
# **************************

def get_or_generate_hour_file_for_building(data, building_to_search, column_a, column_b=None):
    gen_hours()
    filename = column_a
    filename += ('-' + column_b) if not column_b is None else ''
    filename += "-" + building_to_search
    filename += '-hourly.csv'
    try:
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    except FileNotFoundError:
        if column_b is not None:
            return generate_hour_ratio_file_for_building(data, building_to_search, column_a, column_b)
        generated_data = (get_or_generate_month_hour_file_for_buiding(data, building_to_search, column_a)
                          )
        modified_data = {}
        for hour in hours:
            hour_data = generated_data[generated_data['hour'] == hour]
            modified_data[hour] = {}
            column_values = [cv for cv in hour_data['avg'].tolist() if str(cv) != 'nan']
            modified_data[hour]['max'] = hour_data['max'].max()
            modified_data[hour]['avg'] = (sum(column_values) / len(column_values)) if len(column_values) else 0
        with open(filename, 'w') as generated_file:
            generated_file.write('hour' + ',' + 'max' + ',' + 'avg\n')
            for hour in modified_data:
                generated_file.write(
                    hour + ','
                    + str(modified_data[hour]['max']) + ','
                    + str(modified_data[hour]['avg'])
                    + "\n"
                )
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


def generate_hour_ratio_file_for_building(data, building_to_search, column_a, column_b=None):
    gen_hours()
    filename = column_a + "-" + column_b
    filename += "-" + building_to_search
    filename += '-hourly.csv'
    generated_data = get_hour_ratio_for_building(data, building_to_search, column_a, column_b)
    with open(filename, 'w') as generated_file:
        generated_file.write('month' + ',' + 'avg\n')
        for hour in generated_data:
            generated_file.write(
                hour + ','
                + str(generated_data[hour]['avg'])
                + "\n"
            )
    file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


# **************************
# * DIVIDED BY MONTH-HOUR **
# *** BASE GENERATION ***
# **************************


def get_or_generate_month_hour_file_for_buiding(data, building_to_search, column_a, column_b=None,
                                                percentage_value=False):
    gen_hours()
    filename = column_a
    filename += ('-' + column_b) if not column_b is None else ''
    filename += "-" + building_to_search
    filename += '-monthly-hourly.csv'
    try:
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    except FileNotFoundError:
        generated_data = (get_month_hour_data_for_building(data, building_to_search, column_a, percentage_value)
                          if column_b is None else get_month_hour_ratio_for_building(data, building_to_search, column_a,
                                                                                     column_b))
        with open(filename, 'w') as generated_file:
            generated_file.write('month' + "," + "hour" + ',' + (('max' + ',') if column_b is None else '') + 'avg\n')
            for month in generated_data:
                for hour in generated_data[month]:
                    generated_file.write(
                        month + ','
                        + hour + ','
                        + ((str(generated_data[month][hour]['max']) + ',') if column_b is None else "")
                        + str(generated_data[month][hour]['avg'])
                        + "\n"
                    )
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


def get_or_generate_number_of_aps(data):
    filename = "NoAPs.csv"
    try:
        file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    except FileNotFoundError:
        aps = {}
        for group in buildings:
            for building in buildings[group]:
                building_to_search = building + "-"
                data = data[['apName']]
                uniqueAP = data['apName'].unique()
                aps_in_building = [uap for uap in uniqueAP if type(uap) == str and (building_to_search in uap)]
                for aib in aps_in_building:
                    print(building, aib)
                print(building, len(aps_in_building))
                aps[building] = len(aps_in_building)

        with open(filename, 'w') as generated_file:
            generated_file.write('building' + "," + "NoAPs\n")
            for building in aps:
                generated_file.write(building + "," + str(aps[building]) + "\n")
    file_data = pd.read_csv(filepath_or_buffer=filename, index_col=False)
    return file_data


try:
    data = pd.read_csv(filepath_or_buffer='complete_data.csv', index_col=False)
    for group in buildings:
        for building in buildings[group]:
            for field in fields:
                get_or_generate_month_hour_file_for_buiding(data, building, field, percentage_value=fields[field])
                # get_or_generate_hour_file_for_building(data,building, field)
                # get_or_generate_month_file_for_building(data,building,field)
except FileNotFoundError:
    data = load_data_from_source()
    with open('complete_data.csv', 'w') as data_file:
        for index, data_day in enumerate(data.values()):
            if index == 0:
                data_file.write(data_day.to_csv(index=False))
            else:
                data_file.write(data_day.to_csv(index=False, header=None))
print(data)
