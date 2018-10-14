#!/usr/bin/env python

import os
import sys
import optparse
import subprocess
import math
import random
from collections import defaultdict
import logging
from xml.dom import minidom
import time


# we need to import python modules from the $SUMO_HOME/tools directory
try:
    sys.path.append(os.path.join(os.path.dirname(
        __file__), '..', '..', '..', '..', "tools"))  # tutorial in tests
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(
        os.path.dirname(__file__), "..", "..", "..")), "tools"))  # tutorial in docs
    from sumolib import checkBinary
except ImportError:
    sys.exit(
        'please declare environment variable \'SUMO_HOME\' as the root directory of your sumo installation (it should contain folders \'bin\', \'tools\' and \'docs\')')

import traci

# the port used for communicating with your sumo instance
PORT = 8873
VERY_LARGE_FLOAT = 10000000.
GREEN_PHASE_DURATION = 31
LEFT_TURN_SEPERATE_GREEN_TIME = 6
CYCLE_LENGTH = 90
MAX_SPEED = 13.89
ARRIVAL_MARGIN = 2
LEFT_TURNER_ROUTES = ["route1"]
MAX_POOL_LEFT = 10
TOTAL_VEH_LIMIT = 30
LEFT_LANE_CONTROL_DISTANCE = 00
DISTANCE_CLOSEST_VEH=  20
d = defaultdict(list)
simulation_data = []



def run(port):
    """execute the TraCI control loop"""
    traci.init(port)
    simulation_steps = 0
    positionJunctionE0 = traci.lane.getLength("gneE0_0")
    positionJunctionE7 = traci.lane.getLength("gneE7_0")
    positionJunctionE6 = traci.lane.getLength("gneE6_0")
    positionJunctionE8 = traci.lane.getLength("gneE8_0")

    print " MAX_POOL %s Arrival margin %s \n", str(MAX_POOL_LEFT), str(ARRIVAL_MARGIN)
    print "\n"


    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        veh_ids_E0_0 = traci.lane.getLastStepVehicleIDs("gneE0_0")
        veh_ids1_E0_1 = traci.lane.getLastStepVehicleIDs("gneE0_1")
        veh_ids_E7_0 = traci.lane.getLastStepVehicleIDs("gneE7_0")
        veh_ids1_E7_1 = traci.lane.getLastStepVehicleIDs("gneE7_1")

        global d
        for x in range(0, len(veh_ids_E0_0)):
            d[veh_ids_E0_0[x]].append(traci.vehicle.getLaneIndex(veh_ids_E0_0[x]))

        for x in range(0, len(veh_ids1_E0_1)):
            d[veh_ids1_E0_1[x]].append(traci.vehicle.getLaneIndex(veh_ids1_E0_1[x]))

        for x in range(0, len(veh_ids_E7_0)):
            d[veh_ids_E7_0[x]].append(traci.vehicle.getLaneIndex(veh_ids_E7_0[x]))

        for x in range(0, len(veh_ids1_E7_1)):
            d[veh_ids1_E7_1[x]].append(traci.vehicle.getLaneIndex(veh_ids1_E7_1[x]))

        simulation_data.append(d)
        d = defaultdict(list)

        #check old lane index

        for x in range(0, len(veh_ids_E0_0)):
            veh_list_E0_0 = simulation_data[simulation_steps - 1]
            for d1 in veh_list_E0_0[veh_ids_E0_0[x]]:
                #print "veh", veh_ids_E0_0[x],"old lane", d1, "sim step", simulation_steps - 1
                if d1== 0:
                    traci.vehicle.changeLane(veh_ids_E0_0[x],0,50000)
                elif d1 == 1:
                    traci.vehicle.changeLane(veh_ids_E0_0[x], 1,50000)

        for y in range(0, len(veh_ids1_E0_1)):
            veh_list_E0_1 = simulation_data[simulation_steps - 1]
            for d1 in veh_list_E0_1[veh_ids1_E0_1[y]]:
                #print "veh", veh_ids1_E0_1[y],"old lane", d1, "sim step", simulation_steps - 1
                if d1== 0:
                    traci.vehicle.changeLane(veh_ids1_E0_1[y],0,50000)
                elif d1 == 1:
                    traci.vehicle.changeLane(veh_ids1_E0_1[y], 1,50000)
                    
        
        for x in range(0, len(veh_ids_E7_0)):
            veh_list_E7_0 = simulation_data[simulation_steps - 1]
            for d1 in veh_list_E7_0[veh_ids_E7_0[x]]:
                if d1== 0:
                    traci.vehicle.changeLane(veh_ids_E7_0[x],0,50000)
                elif d1 == 1:
                    traci.vehicle.changeLane(veh_ids_E7_0[x], 1,50000)
        
        for y in range(0, len(veh_ids1_E7_1)):
            veh_list_E7_1 = simulation_data[simulation_steps - 1]
            for d1 in veh_list_E7_1[veh_ids1_E7_1[y]]:
                #print "veh", veh_ids1_E0_1[y],"old lane", d1, "sim step", simulation_steps - 1
                if d1== 0:
                    traci.vehicle.changeLane(veh_ids1_E7_1[y],0,50000)
                elif d1 == 1:
                    traci.vehicle.changeLane(veh_ids1_E7_1[y], 1,50000)

        simulation_steps = simulation_steps + 1
    traci.close()
    sys.stdout.flush()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options

def initialize_logger(instance):
    filename= str(instance)+".log"
    os.remove(filename) if os.path.exists(filename) else None
    logging.basicConfig(filename=filename, level=logging.INFO)

def calculate_Travel_Time(number_of_parallel_runs):
    trip_info_duration_data = []
    trip_info_depart_delay_data = []
    trip_info_route_length_data = []

    for x in range(0, number_of_parallel_runs):

        path = "C:\Users\Rajitha\Desktop\glosa\data_tripinfo.xml"
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

        path = "C:\Users\Rajitha\Desktop\glosa\data_emission.xml"
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


def starter(instance, port, arriveMargin):
    options = get_options()
    initialize_logger(instance)

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    sumoProcess = subprocess.Popen(
        [sumoBinary, "-S", "-Q", "--seed", str(random.randint(1, 1000000000)), "-c", "demo.sumo.cfg",
         "--tripinfo-output",
         "tripinfo.xml", "--emission-output", "emission.xml", "--remote-port", str(port)], stdout=sys.stdout,
        stderr=sys.stderr)

    global MAX_POOL_LEFT
    ARRIVAL_MARGIN = arriveMargin
    run(port)
    sumoProcess.wait()
    return  0


# this is the main entry point of this script

def sendToEval():
    options = get_options()
    #initialize_logger("base")

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    rand_num=random.randint(1, 1000000000)
    print "seed", rand_num
    sumoProcess = subprocess.Popen(
        [sumoBinary, "-S","-Q","--seed", str(rand_num),"-c", "concept.sumo.cfg",
         "--tripinfo-output",
         "data_tripinfo.xml", "--emission-output", "data_emission.xml", "--remote-port", str(PORT)], stdout=sys.stdout,
        stderr=sys.stderr)
    run(PORT)
    time.sleep(30)
    acc_travel_time, acc_route_length = calculate_Travel_Time(1)
    acc_emission=calculate_emission(1)
    sumoProcess.wait()
    return  acc_travel_time/acc_route_length, (acc_emission/1000)/acc_route_length, rand_num

if __name__ == "__main__":
    options = get_options()
    initialize_logger("base")

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    rand_num=random.randint(1, 1000000000)
    print "seed", rand_num
    sumoProcess = subprocess.Popen(
        [sumoBinary, "-Q","--seed", str(rand_num),"-c", "concept.sumo.cfg",
         "--tripinfo-output",
         "data_tripinfo.xml", "--emission-output", "data_emission.xml", "--remote-port", str(PORT)], stdout=sys.stdout,
        stderr=sys.stderr)
    run(PORT)
    time.sleep(30)
    acc_travel_time, acc_route_length = calculate_Travel_Time(1)
    acc_emission=calculate_emission(1)

    print "travel time per km ", acc_travel_time/acc_route_length
    print " emission per km",(acc_emission/1000)/acc_route_length
    sumoProcess.wait()




