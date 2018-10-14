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
import time
from xml.dom import minidom
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
    #draw_graph(ids,mergedLIst)


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
        phaseSelector(veh_ids[x], traci.lane.getLength("gneE0_0"))

        # just for testing purpose. to draw the graphs
        if (veh_ids[x] in vehicle_list_left_lane) or (veh_ids[x] in vehicle_list_right_lane):
            d[veh_ids[x]].append(1)
        else:
            d[veh_ids[x]].append(0)
        logging.info(" \n")

def phaseSelector(veh_id, positionJunctionX):
    phrase = traci.trafficlight.getRedYellowGreenState("gneJ1")
    # get vehid  setup outsde func
    if phrase == "rrrrGGGgrrrrGGGg":
        phraseNo = 1

    elif phrase == "rrrryyygrrrryyyg":
        phraseNo = 2

    elif phrase == "rrrrrrrGrrrrrrrG":
        phraseNo = 3

    elif phrase == "rrrrrrryrrrrrrry":
        phraseNo = 4

    elif phrase == "GGGgrrrrGGGgrrrr":
        phraseNo = 5

    elif phrase == "yyygrrrryyygrrrr":
        phraseNo = 6

    elif phrase == "rrrGrrrrrrrGrrrr":
        phraseNo = 7

    elif phrase == "rrryrrrrrrryrrrr":
        phraseNo = 8

    remaining_green, nextGreenPhrase = calculate_RemainingGreen_and_NextGreen(veh_id, positionJunctionX, phraseNo)
    return remaining_green, nextGreenPhrase


def calculate_RemainingGreen_and_NextGreen(veh_id, positionJunctionX, phraseNo):
    remaining = (traci.trafficlight.getNextSwitch("gneJ1") - traci.simulation.getCurrentTime()) / 1000

    if phraseNo == 1:
        remaining_green = remaining
        nextGreenPhrase = 59 + remaining

    elif phraseNo == 2:
        nextGreenPhrase = 55 + remaining
        remaining_green = 0

    elif phraseNo == 3:
        nextGreenPhrase = 49 + remaining
        remaining_green = 0

    elif phraseNo == 4:
        nextGreenPhrase = 45 + remaining
        remaining_green = 0

    elif phraseNo == 5:
        nextGreenPhrase = 14 + remaining
        remaining_green = 0

    elif phraseNo == 6:
        nextGreenPhrase = 10 + remaining
        remaining_green = 0

    elif phraseNo == 7:
        nextGreenPhrase = 4 + remaining
        remaining_green = 0

    elif phraseNo == 8:
        nextGreenPhrase = (remaining)
        remaining_green = 0
    logging.info("////////////////////// %s", str(phraseNo))
    glosa(veh_id, positionJunctionX, phraseNo)
    return remaining_green, nextGreenPhrase


def glosa(veh_id, positionJunctionX, phaseNo):


    status = {}
    arrival_time = 0

    dmax = 0
    tmax = 0
    # ~ ignoreRedLight = 31 - 16 - 1 # speedMode

    global d
    vehcle_data = d[veh_id]
    logging.info("%s",str((traci.trafficlight.getNextSwitch("gneJ1") - traci.simulation.getCurrentTime()) / 1000))


    xPosition = traci.vehicle.getLanePosition(veh_id)
    speed = traci.vehicle.getSpeed(veh_id)
    distance = positionJunctionX - xPosition
    acceleration = traci.vehicle.getAcceleration(veh_id)
    acceleration = round(acceleration, 3)
    traci.vehicle.setSpeedMode(veh_id, 0b11111)

    # Whether this is aleft turner
    isLeftTurner = (traci.vehicle.getRouteID(veh_id) in LEFT_TURNER_ROUTES)

    if acceleration != 0:
        tmax = (MAX_SPEED - speed) / acceleration
        dmax = tmax * ((MAX_SPEED + speed) / 2)
        logging.info("length of the track %s", str(positionJunctionX))
        logging.info("distance %s", str(distance))
        logging.info("tmax %s", str(tmax))
        logging.info("dmax %s", str(dmax))
        if dmax > distance:
            arrival_time = -(speed / acceleration) + math.sqrt(
                ((speed * speed) / (acceleration * acceleration)) + ((2 * distance) / acceleration))

        else:
            arrival_time = tmax + ((distance - dmax) / MAX_SPEED)
            # print "executed"
            logging.info("executed2")
            logging.info("%s", str(arrival_time))

        if distance <= positionJunctionX / 10:
            # vehicle is travelling very slow next to the color light
            arrival_time = 1

    else:
        if (speed >= 0 and speed < 1):
            # executes for very small speeds like 0.1 ,0.0012 which is next to a traffic light.
            # Mainly to avoid unexpected stopping
            # cases when the speed is extremely low. (nearly 0)
            # consider last 100m for executing this command
            if distance <= positionJunctionX / 10:
                # vehicle is travelling very slow next to the color light
                arrival_time = 1
                print veh_id, "executed4"
                logging.info("executed4")

        elif speed != 0:
            arrival_time = distance / speed
            # print arrival_time
            logging.info("executed3")


    remaining = (traci.trafficlight.getNextSwitch("gneJ1") - traci.simulation.getCurrentTime()) / 1000

    logging.info("remaining time %s", str(remaining))
    logging.info("speed %s", str(speed))
    logging.info("distance %s", str(distance))
    logging.info("pos %s", str(xPosition))
    logging.info("posJ %s", str(positionJunctionX))
    logging.info("xPosition %s", str(xPosition))
    logging.info("accel %s", str(acceleration))
    logging.info("SpeedMode: %s" % traci.vehicle.getSpeedMode(veh_id))
    sys.stdout.flush()

    logging.info("arrival timeeeeeeeeeeeee  %s", str(arrival_time))
    if phaseNo == 1 or phaseNo == 3:
        # TODO: adjust for left turners

        if (remaining > arrival_time or (isLeftTurner and remaining + LEFT_TURN_SEPERATE_GREEN_TIME > arrival_time)):
            # ~ if (remaining >= arrival_time + ARRIVAL_MARGIN):
            # This vehicle will pass, let it go with desired max speed

            #traci.vehicle.setSpeed(veh_id, -1)
            advisedSpeed = MAX_SPEED
            traci.vehicle.setSpeed(veh_id, -1)
            logging.info("MAX SPEED %s ", str(veh_id))

        else:
            nextGreenPhase = 59 + remaining + ARRIVAL_MARGIN
            advisedSpeed = max(0, ((2 * distance) / (nextGreenPhase)) - speed)
            ##traci.vehicle.setColor(veh_id, (255, 0, 0))

            traci.vehicle.slowDown(veh_id, advisedSpeed, ((nextGreenPhase) * 1000))
            logging.info( "Arrive in NEXT GREEN PHASE %s %s", str(nextGreenPhase), str(np.ceil(arrival_time / 90)))
            status[veh_id] = 1

    else:
        # current state is not green
        ##traci.vehicle.setColor(veh_id, (255, 0, 0))
        # if status[veh_ids[x]] != 1:
        if phaseNo == 1:
            nextGreenPhase = 59 + remaining + ARRIVAL_MARGIN
        elif phaseNo == 2:
            nextGreenPhase = 55 + remaining + ARRIVAL_MARGIN
        elif phaseNo == 3:
            nextGreenPhase = 49 + remaining + ARRIVAL_MARGIN
        elif phaseNo == 4:
            nextGreenPhase = 45 + remaining + ARRIVAL_MARGIN
        elif phaseNo == 5:
            nextGreenPhase = 14 + remaining + ARRIVAL_MARGIN
        elif phaseNo == 6:
            nextGreenPhase = 10 + remaining + ARRIVAL_MARGIN
        elif phaseNo == 7:
            nextGreenPhase = 4 + remaining + ARRIVAL_MARGIN
        elif phaseNo == 8:
            nextGreenPhase = (remaining) + ARRIVAL_MARGIN

        assert (nextGreenPhase != 0)  # ARRIVAL_MARGIN > 0

        greenPhaseEnd = nextGreenPhase + GREEN_PHASE_DURATION - ARRIVAL_MARGIN
        if isLeftTurner:
            # left turner's green is longer
            greenPhaseEnd += LEFT_TURN_SEPERATE_GREEN_TIME

        if arrival_time > greenPhaseEnd:
            # Vehicle won't arrive in next green phase. Assume that it will in the one afterwards
            myGreenPhase = nextGreenPhase + CYCLE_LENGTH
            advisedSpeed = max(0, ((2 * distance) / (myGreenPhase)) - speed)
        else:
            # Vehicle will arrive in the next green phase
            myGreenPhase = nextGreenPhase
            advisedSpeed = max(0, ((2 * distance) / (myGreenPhase)) - speed)

        traci.vehicle.slowDown(veh_id, advisedSpeed, ((myGreenPhase) * 1000))
        logging.info( "Arrive in GREEN PHASE %s %s", str(myGreenPhase),  str(np.ceil(arrival_time / 90)))
        status[veh_id] = 1



    logging.info( "advised speed %s", str(advisedSpeed))
    # ~ print "new speed", traci.vehicle.getSpeed(veh_id)
    logging.info( "***************************")


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

def sendToEval(seed):
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
    sumoProcess = subprocess.Popen(
        [sumoBinary, "-S","-Q","--seed", str(seed),"-c", "concept.sumo.cfg",
         "--tripinfo-output",
         "data_tripinfo.xml", "--emission-output", "data_emission.xml", "--remote-port", str(PORT)], stdout=sys.stdout,
        stderr=sys.stderr)
    run(PORT)
    time.sleep(30)
    acc_travel_time, acc_route_length = calculate_Travel_Time(1)
    acc_emission=calculate_emission(1)
    sumoProcess.wait()
    return  acc_travel_time/acc_route_length, (acc_emission/1000)/acc_route_length

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
        [sumoBinary,"-S", "-Q","--seed", str(rand_num),"-c", "demo.sumo.cfg",
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



