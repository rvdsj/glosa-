import shutil
from multiprocessing import Process
import multiprocessing as mp
from shlex import shlex
from shutil import copyfile
# import glosa
import os
import sys
import time
from xml.dom import minidom
from scipy.optimize import minimize
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

Pros = []

margins = []
delays = []
function_values=[]

def copy_files_and_start_sumo_UI(port, number_of_parallel_runs, begin_time, theta):
    for i in range(0, number_of_parallel_runs):
        # creating new directories and copy base files
        sample = "sample" + str(i)
        path = "C:\Users\Rajitha\Desktop\glosa\glosa" + sample
        os.mkdir(path)
        shutil.copy(r"C:\Users\Rajitha\Desktop\glosa\temp.py", path)
        shutil.copy("C:\Users\Rajitha\Desktop\glosa\example.net.xml", path)
        shutil.copy(r"C:\Users\Rajitha\Desktop\glosa\demo.sumo.cfg", path)


        datafile = r"C:\Users\Rajitha\Desktop\glosa\filename.xml"
        with open(datafile, 'r') as myfile:
            xml = myfile.read()
        xml = """""" + xml + """"""
        xml = xml.format(placeholder="\"" + str(begin_time[i]) + "\"")
        #print xml
        file = open(path + r"\filename.xml", "w")
        file.write(xml)
        file.close()


        os.chdir(path)
        import temp  # importing glosa module for each and every glosa instance

        p = Process(target=temp.starter, args=(i,port, theta[0],theta[1]))
        p.name = sample
        Pros.append(p)
        p.start()
        port = port + 1

    for t in Pros:
        t.join()

    for j in range(0, number_of_parallel_runs):
        altprocess = Pros[j]
        altprocess.terminate()

    file = open("C:\Users\Rajitha\Desktop\glosa\glosasample0\data.txt", "r")
    temp_data=file.read()
    margin_and_delay=temp_data.split(" ")
    margins.append(margin_and_delay[0])
    delays.append(margin_and_delay[1])

    os.chdir("C:\Users\Rajitha\Desktop\glosa")


def remove_files(number_of_parallel_runs):
    # time.sleep(120)

    for i in range(0, number_of_parallel_runs):
        sample = "sample" + str(i)
        dir = "C:\Users\Rajitha\Desktop\glosa\glosa" + sample

        shutil.rmtree(dir)


def calculate_Travel_Time(number_of_parallel_runs):
    trip_info_duration_data = []
    trip_info_depart_delay_data = []
    trip_info_route_length_data = []

    for x in range(0, number_of_parallel_runs):
        sample = "sample" + str(x)
        path = "C:\Users\Rajitha\Desktop\glosa\glosa" + sample + r"\tripinfo.xml"
        mydoc = minidom.parse(path)
        items = mydoc.getElementsByTagName('tripinfo')
        trip_info_duration = []
        for elem in items:
            trip_info_duration.append(elem.attributes['duration'].value)
        trip_info_duration_data.append(trip_info_duration)

        items = mydoc.getElementsByTagName('tripinfo')
        trip_info_depart_delay = []
        for elem in items:
            trip_info_depart_delay.append(elem.attributes['departDelay'].value)
        trip_info_depart_delay_data.append(trip_info_depart_delay)

        items = mydoc.getElementsByTagName('tripinfo')
        trip_info_route_length = []
        for elem in items:
            trip_info_route_length.append(elem.attributes['routeLength'].value)
        trip_info_route_length_data.append(trip_info_route_length)

    # accumulated_travel_time_for_eac_sim = []
    accumulated_travel_time = 0
    accumulated_route_length = 0

    for i in range(0, number_of_parallel_runs):
        depart_delay_single_sim = trip_info_depart_delay_data[i]
        duration_single_sim = trip_info_duration_data[i]
        route_length_single_sim = trip_info_route_length_data[i]

        depart_delay_all_vehicles = 0
        duration_all_vehicles = 0
        route_length_all_vehicles = 0
        for j in range(0, len(depart_delay_single_sim)):
            depart_delay_all_vehicles = depart_delay_all_vehicles + float(depart_delay_single_sim[j])

        for j in range(0, len(duration_single_sim)):
            duration_all_vehicles = duration_all_vehicles + float(duration_single_sim[j])

        for j in range(0, len(route_length_single_sim)):
            route_length_all_vehicles = route_length_all_vehicles + float(route_length_single_sim[j])

        accumulated_travel_time += depart_delay_all_vehicles + duration_all_vehicles
        accumulated_route_length += route_length_all_vehicles / 1000.
        # accumulated_travel_time_for_eac_sim.append(accumulated_travel_time)
    return accumulated_travel_time, accumulated_route_length


def calculate_emission(number_of_parallel_runs):
    emission_data = []
    for x in range(0, number_of_parallel_runs):
        sample = "sample" + str(x)
        path = "C:\Users\Rajitha\Desktop\glosa\glosa" + sample + r"\emission.xml"
        mydoc = minidom.parse(path)
        items = mydoc.getElementsByTagName('vehicle')
        CO2_emission = []
        for elem in items:
            CO2_emission.append(elem.attributes['CO2'].value)
        emission_data.append(CO2_emission)

    # accumulated_emission_for_sim = []
    accumulated_emission = 0.
    for i in range(0, number_of_parallel_runs):
        emission_all_vehicles = 0
        emission_data_single_sim = emission_data[i]
        for j in range(0, len(emission_data_single_sim)):
            emission_all_vehicles = emission_all_vehicles + float(emission_data_single_sim[j])
        # accumulated_emission_for_sim.append(emission_all_vehicles)
        accumulated_emission += emission_all_vehicles

    return accumulated_emission


class SUMOGlosaObjectiveFunction:

    def __init__(self, alpha=1., number_of_parallel_runs=mp.cpu_count()):
        # weight factor \in [0,1], TODO: dont parse emissions if ==1
        # alpha = 1 => only travel time matters
        # alpha = 0 => only emissions matter
        self._alpha = alpha
        # Number of parallel simulation runs
        self._number_of_parallel_runs = number_of_parallel_runs
        # Duration of flows in simulation

    def __call__(self, theta):
        # TODO: Reach appropriate parameters theta to the individual runners.

        port = 8873
        simulation_time = 2000
        begin_time = [5]
        begin_time.append(40)
        begin_time.append(40)
        begin_time.append(40)

        copy_files_and_start_sumo_UI(port, self._number_of_parallel_runs, begin_time, theta)
        total_travel_time, total_route_length = calculate_Travel_Time(self._number_of_parallel_runs)
        travel_time_per_km = total_travel_time / total_route_length
        total_emissions_in_mg = calculate_emission(self._number_of_parallel_runs)
        total_emissions_in_g = total_emissions_in_mg / 1000.
        emissions_per_km = total_emissions_in_g / total_route_length
        remove_files(self._number_of_parallel_runs)

        return travel_time_per_km, emissions_per_km


if __name__ == '__main__':
    # This is just a test call for the objective function
    # TODO: Add another script which uses scipy.minimize(..., F, ..., theta0) to obtain an optimal theta*


        F = SUMOGlosaObjectiveFunction(alpha=0.5, number_of_parallel_runs=2)
        margin_list= [0.1,1]
        delay_list = [0,5]
        travel_time_storage = defaultdict(dict)
        co2_storage = defaultdict(dict)
        for i in range(len(margin_list)):
            print i
            alt_list=[]
            alt_list.append(margin_list[i])
            alt_list.append(delay_list[i])
            acc_travel_time, acc_co2=F(alt_list)
            travel_time_storage[margin_list[i]][delay_list[i]]=acc_travel_time
            co2_storage[margin_list[i]][delay_list[i]]=acc_co2


        #print TRAVELTIME dictionary
        print "TRAVEL TIME"
        print 	"margin   density -------------->   values"
        for i in range (0,len(travel_time_storage)):
            print margin_list[i],"   ", delay_list[i],"---------------->",travel_time_storage[margin_list[i]][delay_list[i]]

        # print emission dictionary
        print "Emission"
        print    "margin   density -------------->   values"
        for i in range(0, len(co2_storage)):
            print margin_list[i], "   ", delay_list[i], "---------------->", co2_storage[margin_list[i]][delay_list[i]]

        #print "travel_time_dic", travel_time_storage
        #print "co2_dic", co2_storage



