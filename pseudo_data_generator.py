import csv # To create the CSV (built in)
import random # To randomly generate values
import numpy as np # Used to calculate the significant data

# Time
from datetime import date
from dateutil.relativedelta import relativedelta

from pymongo import MongoClient

cluster = MongoClient("mongodb+srv://jinkim:SJsknyu774!@session-data.my1fw.mongodb.net/session-data?retryWrites=true&w=majority")

database = cluster['gait']
sessions_collection = database['sessions']

'''
Method for generating data:

For this current iteration - Only a couple values in the CSV files (see left and right for example)
as a starting point. Further iterations will add more values and scope.

1. Pick a starting point given (each value will have a range)
2. Arrays will be generated for each of the rows separately
3. In the main function, the arrays will be spliced together
4. A CSV with the timestamp of the time the program was executed will be generated

Mathematically speaking, there should be no two CSV files generated that will be alike.
'''

def generate_timestamps():
    # Generating between 600 - 1200 timestamps
    session_length = random.randint(600, 1200)

    res = [0] * session_length

    for i in range(1, session_length):
        res[i] = res[i - 1] + 1000 + int(random.randint(-20, 80) + random.random())

    return res


def generate_stride_pace(timestamps):
    N = len(timestamps)
    res = [0] * N

    for i in range(1, N):
        time_diff = timestamps[i] - timestamps[i - 1]
        res[i] = time_diff / (random.randint(690, 760) + random.random())

    # Because the initial is 0 -> We simply assign it a random value
    res[0] = res[1] + (random.random() * (random.randint(-20, 20) / 100))

    return res


def generate_step_rate(stride_pace):
    N = len(stride_pace)
    res = [0] * N

    for i in range(N):
        res[i] = stride_pace[i] * (random.random() + random.randint(70, 90))

    return res


def generate_contact_time(step_rate):
    N = len(step_rate)
    res = [0] * N

    for i in range(N):
        res[i] = int(step_rate[i] * (random.randint(5, 6) + random.random()))

    return res


def generate_power(contact_time):
    N = len(contact_time)

    res = [0] * N

    res[0] = random.randint(120, 200)

    for i in range(1, N):
        slope = contact_time[i] - contact_time[i - 1]

        # Derivative (if sloping upwards, power also goes up)
        # There is also a random aspect but this is the key pattern
        if (slope > 0):
            k = random.randint(0, 10)
            if (k < 2):
                res[i] = res[i - 1] +  random.randint(7, 15)
            else:
                res[i] = res[i - 1] + random.randint(1, 5)
        else:
            k = random.randint(0, 10)
            if (k < 2):
                res[i] = res[i - 1] - random.randint(7, 15)
            else:
                res[i] = res[i - 1] - random.randint(1, 5)

    return res


def generate_stride_angle(N):
    res = [0] * N

    for i in range(N):
        res[i] = random.randint(4, 9) + random.random()

    return res


def generate_stride_length(stride, step):
    res = [0] * len(stride)

    for i in range(len(stride)):
        res[i] = (stride[i] * 60 * 2) / step[i]

    return res


def generate_elevation_gain(N):
    # First needs to generate range intervals
    interval = 1
    mode = 1

    res = [0] * N

    # Initial point
    res[0] = random.randint(-100, 100) + float(random.randint(0, 3) / 4)

    while (interval < N):
        interval_start = interval
        interval = interval + random.randint(300, 600) # New interval end

        # Edge case: If the 
        if (interval > N):
            interval = N

        for i in range(interval_start, interval):
            k = random.randint(0, 100)
            if (k < 5):
                res[i] = res[i - 1] + (mode * (random.randint(0, 1) + float(random.randint(0, 3) / 4)))
            else:
                res[i] = res[i - 1]

        mode *= -1 # Flip the mode

    return res


# Generates the csv
def generate_csv(tm, dir, timestamps, stride_pace, step_rate, 
                 contact_time, power, stride_angle, elevation_gain):
    with open('%s-%s.csv'%(tm, dir), 'w') as file: # generates the file
        writer = csv.writer(file)

        # These are the features we are looking to generate (Note: Order does matter)
        writer.writerow(["timestamp", "step", "stride_pace", "step_rate", 
                         "contact_time", "power", "stride_angle", 
                         "elevation_gain"])

        for i in range(0, len(timestamps)):
            writer.writerow([timestamps[i], i + 1, stride_pace[i], step_rate[i], contact_time[i],
                             power[i], stride_angle[i], elevation_gain[i]])


def calc(arr):
    q1 = np.quantile(arr, 0.25)
    med = np.quantile(arr, 0.5)
    q3 = np.quantile(arr, 0.75)
    inter = q3 - q1
    mi = q1 - 1.5 * inter
    ma = q1 + 1.5 * inter

    return { "q1": q1, "med": med, "q3": q3, "min": mi, "max": ma }


def generate_relevant(gait, step_rate, stride):
    # Needs to generate the MIN, MAX, Q1, Q3, and MED for both left and right to be stored in the database

    # Sorting all of the data
    gait.sort()
    step_rate.sort()
    stride.sort()

    # Gait calculations
    g_r = calc(gait)

    # Step rate calculations
    s_r = calc(step_rate)

    # Stride calculations
    st_r = calc(stride)

    res = {"gait_vel": g_r, "cadence": s_r, "stride_pace": st_r }
    
    return res

# Where the calculations are made
def main(s):

    timestamps = generate_timestamps()

    stride_pace = generate_stride_pace(timestamps)

    step_rate = generate_step_rate(stride_pace)

    stride_length = generate_stride_length(stride_pace, step_rate)

    # Generating the left foot side (gait velocity, stride length, step length)
    left = generate_relevant(stride_pace, step_rate, stride_length)

    # Generating different stats for the right side
    stride_pace = generate_stride_pace(timestamps)

    step_rate = generate_step_rate(stride_pace)

    stride_length = generate_stride_length(stride_pace, step_rate)

    # Generating the right foot side
    right = generate_relevant(stride_pace, step_rate, stride_length)

    d = date.today() + relativedelta(months=(random.randint(-6, 0))) + relativedelta(days=(random.randint(-28, 0)))
    d = '{:%m/%d/%Y}'.format(d)

    res = { "left": left, "right": right, "user": 1, "date": d }

    if (d not in s):
        try:
            sessions_collection.insert_one(res)
        except Exception as e:
            print("Error: ", e)

        s.add(d)

    # print(res)


if __name__ == "__main__":
    s = set()

    for i in range(100):
        main(s)

    # main(s)
    
