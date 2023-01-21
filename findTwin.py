#!/usr/bin/python3

import csv
import json
from datetime import datetime
import matplotlib.pyplot as plt
import requests
import re
import os

def mapRange(value, leftMin, leftMax, rightMin, rightMax):
    leftSpan = (leftMax - leftMin) + 0.0000001
    rightSpan = (rightMax - rightMin) + 0.0000001
    valueScaled = float(value - leftMin) / float(leftSpan)
    return rightMin + (valueScaled * rightSpan)

class priceDay:
    def __init__(self, date, open, close, percent_change, data):
        self.date = date
        self.open = open
        self.close = close
        self.percent_change = percent_change
        self.data = data

    def __str__(self):
        return f"{self.date}: {self.data}"

    def to_json(self):
        data = {
            "date": self.date,
            "open": self.open,
            "close": self.close,
            "percent_change": self.percent_change,
            "data": self.data
        }
        return json.dumps(data)

def read_csv(file_name):
    data = []
    with open(file_name) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            date = row["date"].split(" ")[0]
            hour = row["date"].split(" ")[1].split(":")[0]
            price_day = next((x for x in data if x.date == date), None)
            if price_day is None:
                price_day = priceDay(date, float(row["open"]), float(row["close"]),
                                  round(((float(row["close"]) - float(row["open"])) / float(row["open"])) * 100, 2),
                                  {
                                        hour: {
                                            'open':float(row["open"]), 
                                            'close':float(row["close"]), 
                                            'percent_change_from_previous': round(((float(row["close"]) - float(row["open"])) / float(row["open"])) * 100, 2),
                                            'percent_change_from_open': round(((float(row["close"]) - float(row['open'])) / float(row["open"])) * 100, 2),
                                            }})
                data.append(price_day)
            else:
                price_day.data[hour] = {
                    'open':float(row["open"]), 
                    'close':float(row["close"]),
                    'percent_change_from_previous': round(((float(row["close"]) - price_day.open) / price_day.open) * 100, 2),
                    'percent_change_from_open': round(((float(row["close"]) - float(price_day.open)) / float(price_day.open)) * 100, 2),
                }
                price_day.close = float(row["close"])
                price_day.percent_change = round(((float(row["close"]) - price_day.open) / price_day.open) * 100, 2)
    return data

def find_latest_complete_day(data):
    complete_days = [day for day in data if len(day.data) == 24]
    complete_days.sort(key=lambda x: datetime.strptime(x.date, '%Y-%m-%d'))
    if len(complete_days)>0:
        return complete_days[-1]
    else:
        return None

def compare_hourly_deltas(day1, day2):
    deltas = []
    for hour in day1.data:
        if hour in day2.data:
            thisDelta = day1.data[hour]['percent_change_from_open'] - day2.data[hour]['percent_change_from_open']
            deltas.append(thisDelta * thisDelta)
    return sum(deltas)

def find_closest_matching_days(data, latest_complete_day):
    closest_days = []
    for day in data:
        if day != latest_complete_day:
            delta = abs(compare_hourly_deltas(day, latest_complete_day))
            closest_days.append({'priceDay':day, 'delta': delta})
    closest_days.sort(key=lambda x: x['delta'])
    return closest_days[:10]

def graph_price_days(day1, day2):
    hour = [str(h).zfill(2) for h in range(1,24)]
    close_price_day1 = [day1.data[h]['close'] for h in hour]
    close_price_day2 = [day2.data[h]['close'] for h in hour]
    fig, (ax1) = plt.subplots(1, sharey=False)
    ax2 = ax1.twinx()
    ax1.plot(hour, close_price_day1, "b", label=day1.date)
    ax2.plot(hour, close_price_day2, 'r', label=day2.date)
    
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    #plt.show()
    return plt

def compare_days(day1, day2):
    return (day1.percent_change - day2.percent_change) * (day1.percent_change - day2.percent_change)

def find_closest_days(data, reference_day, number_of_days):
    days_deltas = [(day, compare_days(reference_day, day)) for day in data if day != reference_day]
    closest_days = sorted(days_deltas, key=lambda x: abs(x[1]))[:number_of_days]
    return [day[0] for day in closest_days]

def save_graph_to_png(graph, file_name):
    graph.savefig(file_name)

def nostrBuildUpload(file_path, server_url):
    try:
        with open(file_path, 'rb') as f:
            formdata = {'submit': 'Upload'}
            files = {'fileToUpload': f}
            response = requests.post(server_url, data=formdata, files=files)
            response.raise_for_status()
            match = re.search(r'<span class=mono id="theList" style="color:#800080">(.+?)\s', response.text)
            if match:
                return match.group(1)
            else:
                return None
    except requests.exceptions.HTTPError as err:
        print(err)

if input('Do you want to download new data? (y/n)').lower() == 'y':
    # DOWNLOAD THE FILE
    url = "https://www.cryptodatadownload.com/cdd/Gemini_BTCUSD_1h.csv"
    response = requests.get(url)
    open("temp.csv", "wb").write(response.content)
    with open("temp.csv") as f:
        lines = f.readlines()
    with open("histdata.csv", "w") as f:
        f.writelines(lines[1:])
    os.remove("temp.csv")

# Select which day if you don't like one, 1-10
useDay = 0

# READ THE DATA AND PROCESS IT
data = read_csv("histdata.csv")
data = [day for day in data if len(day.data) == 24]
last_complete_day = find_latest_complete_day(data)
closest_days_daily_percent_change = find_closest_days(data, last_complete_day, 10)
closest_days = find_closest_matching_days(data, last_complete_day)
graph = graph_price_days(closest_days[useDay]['priceDay'], last_complete_day)
save_graph_to_png(graph, last_complete_day.date.replace('-','_') + '.png')

if input('A match has been found. Generated: ' + last_complete_day.date.replace('-','_') + '.png' + '        Upload? (y/n)').lower() == 'y':
    imageUrl = nostrBuildUpload(last_complete_day.date.replace('-','_') + '.png', 'http://nostr.build/upload.php')
else:
    imageUrl = 'ImageURLPlaceholder'

todayPrice = float(input("What is the price of bitcoin? "))

multiplier = str(round(todayPrice/closest_days[useDay]['priceDay'].data['23']['close'], 1)).replace(".0", "")

def get_percent(a, b):
    tmp = abs((a - b) / b * 100)
    if tmp > 50:
        tmp = str(round(tmp))
    else:
        tmp = str(round(tmp, 1)).replace('.0', '')
    return tmp

if closest_days[useDay]['priceDay'].data['00']['close'] < closest_days[useDay]['priceDay'].data['23']['close']:
    shorttermVerb = ' gaining ' + get_percent(closest_days[useDay]['priceDay'].data['00']['close'], closest_days[useDay]['priceDay'].data['23']['close']) + '%'
elif closest_days[useDay]['priceDay'].data['00']['close'] > closest_days[useDay]['priceDay'].data['23']['close']:
    shorttermVerb = ' losing ' + get_percent(closest_days[useDay]['priceDay'].data['00']['close'], closest_days[useDay]['priceDay'].data['23']['close']) + '%'
else:
    shorttermVerb = ' closing at the same price.'

if todayPrice > closest_days[useDay]['priceDay'].data['23']['close']:
    longtermVerb = ' increased in value by ' + get_percent(todayPrice, closest_days[useDay]['priceDay'].data['23']['close']) + '%'
elif todayPrice < closest_days[useDay]['priceDay'].data['23']['close']:
    longtermVerb = ' decreased in value by ' + get_percent(todayPrice, closest_days[useDay]['priceDay'].data['23']['close']) + '%'
else:
    longtermVerb = ' remained the same price.'

date_object = datetime.strptime(closest_days[useDay]['priceDay'].date, "%Y-%m-%d")
formatted_date = date_object.strftime("%B %d, %Y")
print('--------------------------------------------')
print("Yesterday's BTC Chart Twin was " + formatted_date + "\n\n"
    + "On that day, BTC opened at $" + str(closest_days[useDay]['priceDay'].data['00']['close']) 
    + " and closed at $" + str(closest_days[useDay]['priceDay'].data['23']['close']) + ","
    + shorttermVerb + ".\n\n"
    + "It has since" + longtermVerb + ".\n\n"
    + imageUrl)
print('--------------------------------------------')
