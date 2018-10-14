#!/usr/bin/env python

import os
import sys
import optparse
import subprocess
import math
import random
from collections import defaultdict
import logging
import numpy as np
import matplotlib.pyplot as plt

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
LEFT_LANE_CONTROL_DISTANCE = 100
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

        mergedLIst = veh_ids_E0_0 + veh_ids1_E0_1
        save_observations(mergedLIst, positionJunctionE0, veh_ids_E0_0, veh_ids1_E0_1)

        rules(mergedLIst, veh_ids_E0_0, veh_ids1_E0_1)
        simulation_steps = simulation_steps + 1
        logging.info("---------------------------------------------------------------------------------------------------------------")
    traci.close()
    sys.stdout.flush()
    print "no of simulation_steps ", simulation_steps
    ids = ['flow1.0', 'flow1.1', 'flow1.3', 'flow1.7','flow2.0', 'flow2.1', 'flow2.3', 'flow2.7']
    #ids=['flow2.0','flow2.1','flow2.5', 'flow2.7']
    draw_graph(ids,mergedLIst)


    # thefile = open('test.txt', 'w')
    # for item in range(0,len(simulation_data)):
    #    print>> thefile, simulation_data[item]

def draw_graph(veh_ids, mergedList):
    speed_data=[]
    time_step_data=[]

    for ids in range(0, len(veh_ids)):
        display_list = []

        for item in range(0, len(simulation_data)):
            dictionary= simulation_data[item]
            vehicle_data=dictionary[veh_ids[ids]]
            if len(vehicle_data)>0:
                if len(vehicle_data) == 6:
                    speed=round(vehicle_data[0],1)
                    speed_data.append(speed)
                    time_step_data.append(item)

                    #alt_list=[]
                    #alt_list.append(item)
                    #alt_list.append(speed)
                    #display_list.append(alt_list)

        #print  display_list
        #print "len- speed data", len(speed_data)
        #print "len - step", len(time_step_data)
        plt.figure(ids).suptitle(veh_ids[ids])
        plt.plot(time_step_data, speed_data)
        speed_data[:]=[]
        time_step_data[:]=[]
    plt.show()


def rules(veh_ids, veh_ids_E0_0, veh_ids1_E0_1):
    global d
    list_size0 = len(veh_ids)

    simulation_data.append(d)
    d = defaultdict(list)


def save_observations(veh_ids, positionJunctionX, vehicle_list_right_lane, vehicle_list_left_lane):
    arraySize = len(veh_ids)

    for x in range(0, arraySize):
        # print "vehicle Id", veh_ids[x]

        xPosition = traci.vehicle.getLanePosition(veh_ids[x])
        distance_for_x = positionJunctionX - xPosition


        global d
        d[veh_ids[x]].append(traci.vehicle.getSpeed(veh_ids[x]))
        d[veh_ids[x]].append(traci.vehicle.getAcceleration(veh_ids[x]))
        d[veh_ids[x]].append(xPosition)
        d[veh_ids[x]].append(distance_for_x)
        d[veh_ids[x]].append(traci.vehicle.getLaneIndex(veh_ids[x]))
        # just for testing purpose. to draw the graphs
        if (veh_ids[x] in vehicle_list_left_lane) or (veh_ids[x] in vehicle_list_right_lane):
            d[veh_ids[x]].append(1)
        else:
            d[veh_ids[x]].append(0)
        logging.info(" \n")



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


# this is the main entry point of this script
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
        [sumoBinary,"--seed", str(256171225),"-c", "demo.sumo.cfg",
         "--tripinfo-output",
         "tripinfo.xml", "--emission-output", "emission.xml", "--remote-port", str(PORT)], stdout=sys.stdout,
        stderr=sys.stderr)
    run(PORT)
    sumoProcess.wait()



