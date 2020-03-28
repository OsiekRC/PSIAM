import pandas as pd
import calendar


def numericdatetostringdate(year, month, day=0):
    if month < 10:
        string_month = '0' + str(month)
    else:
        string_month = str(month)
    if day:
        if day < 10:
            string_day = '0'+str(day)
        else:
            string_day = str(day)
        string_date = str(year)+'-'+string_month+'-'+string_day
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
    years = [2015, 2016]
    months = [1, 2, 3, 4, 5, 6, 10, 11, 12]
    c = calendar.Calendar()
    for year in years:
        for month in months:
            for day in c.itermonthdays(year, month):
                # print(day)
                if day:
                    data_file_name = data_location + '/'+numericdatetostringdate(year, month)+'/statystyki-wifi-'+numericdatetostringdate(year, month, day)+'.csv'
                    try:
                        data_dict[numericdatetostringdate(year, month, day)] = pd.read_csv(filepath_or_buffer=data_file_name, sep=';', index_col=False, header=0, names=data_column_names)
                        data_dict[numericdatetostringdate(year, month, day)]['dataPomiaru'] = pd.to_datetime(data_dict[numericdatetostringdate(year, month, day)]['dataPomiaru'], format="%Y-%m-%d--%H-%M")
                    except FileNotFoundError:
                        print(numericdatetostringdate(year, month, day)+" is missing")
    return data_dict


def concatenate_tables(data_dict):
    data = None
    for data_day in data_dict.values():
        if data is None:
            data = data_day
        else:
            data.append(data_day, ignore_index=True)
    return data


try:
    data = pd.read_csv(filepath_or_buffer='complete_data.csv', index_col=False)
except FileNotFoundError:
    data = concatenate_tables(load_data_from_source())
    data_file = open('complete_data.csv', 'w')
    data_file.write(data.to_csv(index=False))
    data_file.close()
print(data)
