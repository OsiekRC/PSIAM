import pandas as pd
import calendar
from datetime import timedelta, datetime

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
    td = timedelta(minutes=20)
    start_at= "07-30"
    end_at="20-30"
    ignore_AP_regex='AP-jgora|AP-walbrzych'
    c = calendar.Calendar()
    for year in years:
        for month in months:
            for day in c.itermonthdays(year, month):
                # print(day)
                if day:
                    data_file_name = data_location + '/'+numericdatetostringdate(year, month)+'/statystyki-wifi-'+numericdatetostringdate(year, month, day)+'.csv'
                    try:
                        start_time = datetime.strptime(str(year)+"-"+str(month)+"-" + str(day)+"--" + start_at , "%Y-%m-%d--%H-%M")
                        end_time = datetime.strptime(str(year)+"-"+str(month)+"-" + str(day) +"--" + end_at, "%Y-%m-%d--%H-%M")
                        data = pd.read_csv(filepath_or_buffer=data_file_name, sep=';', index_col=False, header=0, names=data_column_names)
                        extracted_data = None
                        curr_date= start_time
                        while curr_date <= end_time:
                            curr_time_data =  data[data['dataPomiaru'] == datetime.strftime(curr_date,"%Y-%m-%d--%H-%M")]
                            curr_time_data = curr_time_data[~curr_time_data['apName'].str.contains(ignore_AP_regex, na=False)]
                            extracted_data = curr_time_data if extracted_data is None else extracted_data.append(curr_time_data)
                            curr_date+= td
                        data_dict[numericdatetostringdate(year, month, day)] = extracted_data
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
    data = load_data_from_source()
    with open('complete_data.csv', 'w') as data_file:
        for data_day in data.values():
            data_file.write(data_day.to_csv(index=False))
print(data)

