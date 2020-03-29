import pandas as pd
import calendar
from datetime import timedelta, datetime
import statistics
import re

months = [1, 2, 3, 4, 5, 6, 10, 11, 12]
years = [2015, 2016]
start_at= "07-30"
end_at="20-30"
ignore_AP_regex='AP-jgora|AP-walbrzych|AP-Legnica|Ustka|-GEO-'

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
    td = timedelta(minutes=20)
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

def get_monthly_data(data,column):
    buildings_to_search= ['A1-', 'B4']
    summary= {}
    for month in months:
        summary["{:02d}".format(month)]={}
    data= data[['apName','dataPomiaru',column]]
    uniqueAP = data['apName'].unique()
    aps_to_search = [uap for uap in uniqueAP if type(uap) == str and any(bts in uap for bts in buildings_to_search)]
    for index, ap in enumerate(aps_to_search):
        print(index , 'out of' , len(aps_to_search))
        for month in months:
            current_month = "{:02d}".format(month)
            ap_data = data[data['apName'] == ap]
            ap_data = ap_data[ap_data['dataPomiaru'].str.contains(r"\d{4}-"+current_month+r"-\d{2}--")]
            column_values= ap_data[column].tolist()
            summary[current_month][ap] ={}
            summary[current_month][ap]['max'] = max(column_values) if len(column_values) else 0
            summary[current_month][ap]['min'] = min(column_values) if len(column_values) else 0
            summary[current_month][ap]['avg']= statistics.mean(column_values) if len(column_values) else 0
    with open(column+'-monthly.txt', 'w') as summary_file:
        for month in summary:
            summary_file.write(' Month: ' + month +'\n')
            for ap in summary[month]:
                summary_file.write('AP:   ' + ap 
                +"  max: " + str(summary[month][ap]['max'])
                +"  min: " + str(summary[month][ap]['min'])
                +"  avg: " + str(summary[month][ap]['avg'])
                + "\n")

try:
    data = pd.read_csv(filepath_or_buffer='complete_data.csv', index_col=False)
    get_monthly_data(data, 'NoOfUsers')
except FileNotFoundError:
    data = load_data_from_source()
    with open('complete_data.csv', 'w') as data_file:
        for index, data_day in enumerate(data.values()):
            if index == 0:
                data_file.write(data_day.to_csv(index=False))
            else:
                data_file.write(data_day.to_csv(index=False, header=None))
print(data)

