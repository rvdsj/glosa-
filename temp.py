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
import time
from xml.dom import minidom
import traci

# the port used for communicating with your sumo instance
PORT = 8873
VERY_LARGE_FLOAT = 10000000.
GREEN_PHASE_DURATION = 31
LEFT_TURN_SEPERATE_GREEN_TIME = 6
CYCLE_LENGTH = 90
MAX_SPEED = 13.89
ARRIVAL_MARGIN = 2.0
LEFT_TURNER_ROUTES = ["route1"]
MAX_POOL_LEFT = 10
TOTAL_VEH_LIMIT = 30
LEFT_LANE_CONTROL_DISTANCE = 00
DISTANCE_CLOSEST_VEH=  20
CONTROL_PHASE_DURATION = 31
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

    print "margin", ARRIVAL_MARGIN
    print "control phase", CONTROL_PHASE_DURATION


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
                if len(vehicle_data) == 20:
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
    for x in range(0, list_size0):
        # print "vehicle Id >>>>>>>>>>>>>>>>>>>", veh_ids[x]

        list_vehicle_details = d[veh_ids[x]]
        distance = list_vehicle_details[3]
        current_lane = list_vehicle_details[4]
        current_route = list_vehicle_details[9]
        leaders_leftlane_leftturn_list = list_vehicle_details[5]
        leaders_leftlane_stright_list = list_vehicle_details[6]
        leaders_rightlane_rightturn_list = list_vehicle_details[7]
        leaders_rightlane_straight_list = list_vehicle_details[8]
        leaders_left_lane = list_vehicle_details[10]
        leaders_right_lane = list_vehicle_details[11]

        # print "leaders_left_lane", leaders_left_lane
        # print "leaders right_lane", leaders_right_lane

        flag1 = list_vehicle_details[12]
        flag2 = list_vehicle_details[13]
        flag3 = list_vehicle_details[14]
        slow_down_flag = list_vehicle_details[15]
        slow_down_flag_straight_veh = list_vehicle_details[16]
        remaining_green=list_vehicle_details[18]
        leftlane_pool = 0
        rigtlane_pool = 0

        # rule if rule 3 executed keep  it all the time. here after straight going vehicle is alwys placed in route 0
        if flag2 == 1:
            if ((traci.lane.getLength("gneE0_1") - traci.vehicle.getLanePosition(veh_ids[x])) > LEFT_LANE_CONTROL_DISTANCE):
                traci.vehicle.changeLane(veh_ids[x], 0, 50000)

        if flag3 == 1:
            if ((traci.lane.getLength("gneE0_1") - traci.vehicle.getLanePosition(veh_ids[x])) > LEFT_LANE_CONTROL_DISTANCE):
                traci.vehicle.changeLane(veh_ids[x], 1, 50000)

        if (flag1 == -1) and (flag2 == -1) and (flag3 == -1):

            if traci.vehicle.getRouteID(veh_ids[x]) == 'route1':
                traci.vehicle.setColor(veh_ids[x], (0, 255, 0))  # green for left turners initially

            elif traci.vehicle.getRouteID(veh_ids[x]) == 'route2':
                traci.vehicle.setColor(veh_ids[x], (90, 102, 91))  # gray for right turners
        #print veh_ids[x], " ", flag1," ",flag2," ",flag3

        # rule1- chnage left all left turners to left lane
        if current_route == 'route1':
            #traci.vehicle.setColor(veh_ids[x], (31, 94, 163))
            if ((traci.lane.getLength("gneE0_1") - traci.vehicle.getLanePosition(veh_ids[x])) > LEFT_LANE_CONTROL_DISTANCE):
                traci.vehicle.changeLane(veh_ids[x], 1, 5000000)

        # rule2- chnage all right turners to lane 0
        if current_route == 'route2':
            # traci.vehicle.setColor(veh_ids[x], (31, 94, 163))
            if ((traci.lane.getLength("gneE0_1") - traci.vehicle.getLanePosition(veh_ids[x])) > LEFT_LANE_CONTROL_DISTANCE):
                traci.vehicle.changeLane(veh_ids[x], 0, 5000000)

        # rule3 - check left lange. check whether straight going is following a left turner. if then change it to right lane
        if current_route == 'route0':
            if (current_lane == 1):
                if len(leaders_leftlane_leftturn_list) > 0:
                    # if traci.vehicle.getRouteID(leaders_left_lane[0]) == 'route1':
                    if ((traci.lane.getLength("gneE0_1") - traci.vehicle.getLanePosition(veh_ids[x]))>LEFT_LANE_CONTROL_DISTANCE):
                        traci.vehicle.setColor(veh_ids[x], (226, 11, 29))
                        traci.vehicle.changeLane(veh_ids[x], 0, 5000000)
                        flag2 = 1
                    else:
                        traci.vehicle.changeLane(veh_ids[x], 1, 5000000)

        # Rule grab the leading vehicle which is travelling straight and change it to lane 1
        # First count number of leading straight going vehicles for the first left turner in left lane

        if current_route == 'route1':
            if (current_lane == 1):
                length_all_vehicles_left_lane = len(veh_ids1_E0_1)
                check = length_all_vehicles_left_lane
                leftlane_pool = 0
                while check > 0:
                    if (traci.vehicle.getRouteID(veh_ids1_E0_1[check - 1]) == 'route1'):
                        vehicle = veh_ids1_E0_1[check - 1]  # first left turner
                        break
                    leftlane_pool = leftlane_pool + 1
                    check = check - 1
            # left_lane_pool has no of leading straght going vehicles to the first left turner
            if vehicle == veh_ids[x]:
                if (leftlane_pool < MAX_POOL_LEFT + 1):
                    #first left turner slow down
                    traci.vehicle.setColor(veh_ids[x], (1, 255, 1))
                else:
                    traci.vehicle.setColor(veh_ids[x], (0, 255, 0))

                if leftlane_pool <= MAX_POOL_LEFT:
                    length = len(leaders_rightlane_straight_list)
                    check = length

                    while check > 0:
                        if (traci.vehicle.getRouteID(leaders_rightlane_straight_list[check - 1]) == 'route0'):

                            vehicle = leaders_rightlane_straight_list[check - 1]
                            if ((traci.lane.getLength("gneE0_1") - traci.vehicle.getLanePosition(vehicle))>100):
                                if leftlane_pool <=MAX_POOL_LEFT:
                                    traci.vehicle.setColor(vehicle, (0, 0, 255))
                                    traci.vehicle.changeLane(vehicle, 1, 500000)
                                    leftlane_pool=leftlane_pool+1
                                else:
                                    break
                            else:
                                traci.vehicle.changeLane(vehicle, 0, 500000)
                        check = check - 1


    # print d
    #print "///////////////////////////////////////"
    #simulation_data.append(d)
    d = defaultdict(list)


def save_observations(veh_ids, positionJunctionX, vehicle_list_right_lane, vehicle_list_left_lane):
    arraySize = len(veh_ids)

    for x in range(0, arraySize):
        # print "vehicle Id", veh_ids[x]

        xPosition = traci.vehicle.getLanePosition(veh_ids[x])
        distance_for_x = positionJunctionX - xPosition
        leaders_leftlane_leftturn_list = []
        leaders_leftlane_stright_list = []
        leaders_rightlane_rightturn_list = []
        leaders_rightlane_straight_list = []
        flag1 = -1  # flag for inidicatin that this vehicle was travelling on lane 0 and now in 1 (left turning)
        flag2 = -1  # flag for indicating that this vehicle move from lane 1 t 0 (staright going vehicle)
        flag3 = -1  # flag for indicating that this vehicle move from 0 to 1 (straight going vehicle)
        slow_down_flag = -1
        slow_down_flag_straight_veh=-1
        slow_down_right_lane = -1
        for y in range(0, arraySize):
            if veh_ids[y] != veh_ids[x]:
                # x current vehicle y=other vehicles
                lane = traci.vehicle.getLaneIndex(veh_ids[y])
                xPositionForOther = traci.vehicle.getLanePosition(veh_ids[y])
                distance_for_y = positionJunctionX - xPositionForOther
                if lane == 1:
                    if distance_for_y < distance_for_x:
                        if traci.vehicle.getRouteID(veh_ids[y]) == 'route1':
                            leaders_leftlane_leftturn_list.append(veh_ids[y])
                        if traci.vehicle.getRouteID(veh_ids[y]) == 'route0':
                            leaders_leftlane_stright_list.append(veh_ids[y])

                if lane == 0:
                    if distance_for_y < distance_for_x:
                        if traci.vehicle.getRouteID(veh_ids[y]) == 'route2':
                            leaders_rightlane_rightturn_list.append(veh_ids[y])
                        if traci.vehicle.getRouteID(veh_ids[y]) == 'route0':
                            leaders_rightlane_straight_list.append(veh_ids[y])

        alt_left_lane = vehicle_list_left_lane[:]
        alt_right_lane = vehicle_list_right_lane[:]
        leaders_right_lane = []
        leaders_left_lane = []

        if traci.vehicle.getLaneIndex(veh_ids[x]) == 0:
            length = len(alt_right_lane)
            start = 0
            for z in range(0, length):
                if alt_right_lane[z] == veh_ids[x]:
                    start = z
                    break

            leaders_right_lane = alt_right_lane[(start + 1):length]

            counter = 0
            if len(alt_left_lane) > 0:
                while counter < len(alt_left_lane):
                    if traci.vehicle.getLanePosition(alt_left_lane[counter]) > traci.vehicle.getLanePosition(
                            veh_ids[x]):
                        break
                    counter = counter + 1
                leaders_left_lane = alt_left_lane[counter: len(alt_left_lane)]
                # print "zzzzzzzzzzzzzzzzzzzzz" , veh_ids[x]," ", counter ,alt_left_lane, " ",  leaders_left_lane

        elif traci.vehicle.getLaneIndex(veh_ids[x]) == 1:

            length = len(alt_left_lane)
            start = 0
            for z in range(0, length):
                if alt_left_lane[z] == veh_ids[x]:
                    start = z
                    break

            leaders_left_lane = alt_left_lane[(start + 1):length]

            counter = 0
            if len(alt_right_lane) > 0:
                while counter < len(alt_right_lane):
                    if traci.vehicle.getLanePosition(alt_right_lane[counter]) > traci.vehicle.getLanePosition(
                            veh_ids[x]):
                        break
                    counter = counter + 1
                leaders_right_lane = alt_right_lane[counter: len(alt_right_lane)]

        colorR, colorG, colorB, alpha = traci.vehicle.getColor(veh_ids[x])

        if (colorR == 31) and (colorG == 94) and (colorB == 163):
            flag1 = 1
        elif (colorR == 226) and (colorG == 11) and (colorB == 29):
            flag2 = 1
        elif (colorR == 0) and (colorG == 0) and (colorB == 255):
            flag3 = 1
        elif (colorR == 1) and (colorG == 255) and (colorB == 1):
            slow_down_flag = 1
        elif (colorR == 0) and (colorG == 255) and (colorB == 0):
            slow_down_flag = -1
        elif (colorR == 244) and (colorG == 164) and (colorB ==44):
            slow_down_flag_straight_veh=1
        elif (colorR == 197) and (colorG == 66) and (colorB == 244):
            slow_down_right_lane = 1

        global d
        d[veh_ids[x]].append(traci.vehicle.getSpeed(veh_ids[x]))
        d[veh_ids[x]].append(traci.vehicle.getAcceleration(veh_ids[x]))
        d[veh_ids[x]].append(xPosition)
        d[veh_ids[x]].append(distance_for_x)
        d[veh_ids[x]].append(traci.vehicle.getLaneIndex(veh_ids[x]))
        d[veh_ids[x]].append(leaders_leftlane_leftturn_list)
        d[veh_ids[x]].append(leaders_leftlane_stright_list)
        d[veh_ids[x]].append(leaders_rightlane_rightturn_list)
        d[veh_ids[x]].append(leaders_rightlane_straight_list)
        d[veh_ids[x]].append(traci.vehicle.getRouteID(veh_ids[x]))
        d[veh_ids[x]].append(leaders_left_lane)
        d[veh_ids[x]].append(leaders_right_lane)
        d[veh_ids[x]].append(flag1)
        d[veh_ids[x]].append(flag2)
        d[veh_ids[x]].append(flag3)
        d[veh_ids[x]].append(slow_down_flag)  # slow down
        d[veh_ids[x]].append(slow_down_flag_straight_veh)
        d[veh_ids[x]].append(slow_down_right_lane)

        remaining_green, nextGreenPhrase = phaseSelector(veh_ids[x], traci.lane.getLength("gneE0_0"))

        d[veh_ids[x]].append(remaining_green)
        d[veh_ids[x]].append(nextGreenPhrase)

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
    slow_down_flag = vehcle_data[15]

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
                #print veh_id, "executed4", speed, " ",acceleration
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

            traci.vehicle.setSpeed(veh_id, advisedSpeed)
            #print "MAXSPEED", veh_id

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
            if slow_down_flag == 1:
                myGreenPhase = nextGreenPhase + CYCLE_LENGTH + CONTROL_PHASE_DURATION
                advisedSpeed = max(0, ((2 * distance) / (myGreenPhase)) - speed)
            else:
                myGreenPhase = nextGreenPhase + CYCLE_LENGTH
                advisedSpeed = max(0, ((2 * distance) / (myGreenPhase)) - speed)
        else:
            # Vehicle will arrive in the next green phase
            if slow_down_flag == 1:
                myGreenPhase = nextGreenPhase+ CONTROL_PHASE_DURATION
                advisedSpeed = max(0, ((2 * distance) / (myGreenPhase)) - speed)
            else:
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
    return ARRIVAL_MARGIN

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


def starter(instance, port, arriveMargin, controlphase):
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
	rand_num=random.randint(1, 1000000000)
    sumoProcess = subprocess.Popen(
        ["sumo", "-S", "-Q", "--seed", str(983777225), "-c", "demo.sumo.cfg",
         "--tripinfo-output",
         "tripinfo.xml", "--emission-output", "emission.xml", "--remote-port", str(port)], stdout=sys.stdout,
        stderr=sys.stderr)

    global MAX_POOL_LEFT
    global ARRIVAL_MARGIN
    ARRIVAL_MARGIN = arriveMargin
    global CONTROL_PHASE_DURATION
    CONTROL_PHASE_DURATION= controlphase
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



