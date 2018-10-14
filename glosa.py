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
MAX_POOL_RIGHT = 5  # currently unlimited
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
                if len(vehicle_data) == 19:
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
    """
    for x in range(0, list_size0):
        print "vehicle Id >>>>>>>>>>>>>>>>>>>", veh_ids[x]
        for d1 in d[veh_ids[x]]:
            #if isinstance(d1, (list,)):
            #    for d2 in d1:
            #        print d2
            #else:
            print d1
    """

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

        leftlane_pool = 0
        rigtlane_pool = 0

        # rule if rule 3 executed keep  it all the time. here after straight going vehicle is alwys placed in route 0
        if flag2 == 1:
            traci.vehicle.changeLane(veh_ids[x], 0, 50000)

        if flag3 == 1:
            traci.vehicle.changeLane(veh_ids[x], 1, 50000)

        if (flag1 == -1) and (flag2 == -1) and (flag3 == -1):
            if traci.vehicle.getRouteID(veh_ids[x]) == 'route1':
                traci.vehicle.setColor(veh_ids[x], (0, 255, 0))  # green for left turners initially

            elif traci.vehicle.getRouteID(veh_ids[x]) == 'route2':
                traci.vehicle.setColor(veh_ids[x], (90, 102, 91))  # gray for right turners

        # rule1- chnage left all left turners to left lane
        if current_route == 'route1':
            # traci.vehicle.setColor(veh_ids[x], (31, 94, 163))
            traci.vehicle.changeLane(veh_ids[x], 1, 5000000)

        # rule2- chnage all right turners to lane 0
        if current_route == 'route2':
            # traci.vehicle.setColor(veh_ids[x], (31, 94, 163))
            traci.vehicle.changeLane(veh_ids[x], 0, 5000000)

        # rule3 - check left lange. check whether straight going is following a left turner. if then change it to right lane
        if current_route == 'route0':
            if (current_lane == 1):
                if len(leaders_leftlane_leftturn_list) > 0:
                    # if traci.vehicle.getRouteID(leaders_left_lane[0]) == 'route1':

                    traci.vehicle.setColor(veh_ids[x], (226, 11, 29))
                    traci.vehicle.changeLane(veh_ids[x], 0, 5000000)
                    flag2 = 1

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

                    traci.vehicle.setColor(veh_ids[x], (1, 255, 1))
                else:
                    traci.vehicle.setColor(veh_ids[x], (0, 255, 0))

                if leftlane_pool <= MAX_POOL_LEFT:
                    length = len(leaders_rightlane_straight_list)
                    check = length

                    while check > 0:
                        if (traci.vehicle.getRouteID(leaders_rightlane_straight_list[check - 1]) == 'route0'):
                            vehicle = leaders_rightlane_straight_list[check - 1]
                            traci.vehicle.setColor(vehicle, (0, 0, 255))
                            traci.vehicle.changeLane(vehicle, 1, 500000)
                        check = check - 1

        """
        if current_route == 'route0':
            if (current_lane == 0):

                length = len(leaders_right_lane)
                check = length
                vehicle = ''

                while check > 0:
                    if (traci.vehicle.getRouteID(leaders_right_lane[check - 1]) == 'route0'):
                        vehicle = leaders_right_lane[check - 1]
                        break
                    check = check - 1
                if vehicle != '':
                    # check if the lane 1 has already leading left turners.
                    candidate_vehicle_details = d[vehicle]
                    leaders_left_lane_for_candidate = candidate_vehicle_details[10]
                    lane_change_flag = 1  # 1 indicates straight going vehicle to chnage lane to 1

                    for s in range(0, len(leaders_left_lane_for_candidate)):
                        alt_vehicle = leaders_left_lane_for_candidate[s]
                        if traci.vehicle.getRouteID(alt_vehicle) == 'route1':
                            lane_change_flag = 0
                            break
                        else:
                            leftlane_pool = leftlane_pool + 1

                    if lane_change_flag == 1:
                        # can change lane 0 to 1 because there are no leading left turners on lane 1

                        if leftlane_pool <= MAX_POOL_LEFT:
                            distance_to_junction=traci.lane.getLength("gneE0_1") - traci.vehicle.getLanePosition(vehicle)
                            if distance_to_junction>LEFT_LANE_CONTROL_DISTANCE:
                                traci.vehicle.setColor(vehicle, (0, 0, 255))
                                traci.vehicle.changeLane(vehicle, 1, 500000)
                                print "hhhhhhhhhhhhhhhhh" , leftlane_pool
            """
        leftlane_pool_new = 0
        # rule - if there more straight going vehicles in left lane (than no of places) , switch to lane 0/ right lane
        if current_route == 'route0':
            if (current_lane == 1):
                length = len(leaders_left_lane)
                check = length
                vehicle = ''

                while check > 0:
                    if (traci.vehicle.getRouteID(leaders_left_lane[check - 1]) == 'route1'):
                        break
                    vehicle = leaders_left_lane[check - 1]
                    check = check - 1
                    leftlane_pool_new = leftlane_pool_new + 1
                    if (leftlane_pool_new > MAX_POOL_LEFT) and (flag2 != 1):
                        traci.vehicle.changeLane(veh_ids[x], 0, 500000)
                        traci.vehicle.setColor(veh_ids[x], (45, 89, 78))
                        break

        """
        leftlane_pool = 0
        #special rule to slow down left turners
        if current_route == 'route1':
            length = len(leaders_left_lane)
            check = length

            while check > 0:
                if (traci.vehicle.getRouteID(leaders_left_lane[check - 1]) == 'route1'):
                    break
                vehicle = leaders_left_lane[check - 1]
                check = check - 1
                leftlane_pool = leftlane_pool + 1

            if (leftlane_pool < MAX_POOL_LEFT+1) :
                #if number of stright going vehicles leading is less than the MAX POOL LIMIT left turner should lower the speed
                traci.vehicle.setColor(veh_ids[x], (1, 255, 1))

            else:
                traci.vehicle.setColor(veh_ids[x], (0, 255, 0))
        """

    # print d
    # print "///////////////////////////////////////"
    simulation_data.append(d)
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
    # NOTE: Perhaps, it could be beneficial to control left turners by GLOSA wrt their separate green phase only. (especially the green phase start)
    #       Currently we only consider a prolonged green phase for them. Its questionable whether delaying them by restricting them to pass
    #       exclusively at their separate green time is appropriate for allowing straight going vehicles to use both lanes.

    status = {}
    arrival_time = 0

    dmax = 0
    tmax = 0
    # ~ ignoreRedLight = 31 - 16 - 1 # speedMode

    global d
    vehcle_data = d[veh_id]
    slow_down_flag = vehcle_data[15]

    logging.info("%s %s",str(veh_id), str(slow_down_flag))
    logging.info("%s",str((traci.trafficlight.getNextSwitch("gneJ1") - traci.simulation.getCurrentTime()) / 1000))

    # print traci.trafficlight.getCompleteRedYellowGreenDefinition("gneJ1")
    # if veh_ids[x] != "flow1.1" : continue
    xPosition = traci.vehicle.getLanePosition(veh_id)
    speed = traci.vehicle.getSpeed(veh_id)
    distance = positionJunctionX - xPosition
    acceleration = traci.vehicle.getAcceleration(veh_id)
    acceleration = round(acceleration, 3)
    # traci.vehicle.setSpeedMode(veh_id, ignoreRedLight)
    traci.vehicle.setSpeedMode(veh_id, 0b11111)

    # For queued vehicles assume a positive acceleration to assure that a vehicle stopped
    # in front of the traffic light will continue at green

    standing_in_queue = (speed <= 5. / 3.6 and acceleration <= 0.5)
    if standing_in_queue:
        # Don't do GLOSA
        traci.vehicle.setSpeed(veh_id, -1)
        ##traci.vehicle.setColor(veh_id, (100, 100, 100))
        # ~ acceleration = traci.vehicle.getAccel(veh_id)*0.5
        return

    # Whether this is aleft turner
    isLeftTurner = (traci.vehicle.getRouteID(veh_id) in LEFT_TURNER_ROUTES)

    if acceleration > 0:
        tmax = (MAX_SPEED - speed) / acceleration
        dmax = tmax * ((MAX_SPEED + speed) / 2)
        logging.info ("length of the track %s", str(positionJunctionX))
        logging.info( "distance %s", str(distance))
        logging.info("tmax %s", str(tmax))
        logging.info("dmax %s", str(dmax))
        if dmax > distance:
            arrival_time = -(speed / acceleration) + math.sqrt(
                ((speed * speed) / (acceleration * acceleration)) + ((2 * distance) / acceleration))

        else:
            arrival_time = tmax + ((distance - dmax) / MAX_SPEED)
            # print "executed"
            logging.info("executed2")
            logging.info ("%s", str(arrival_time))

    elif acceleration < 0:
        # Don't take into account deceleration in extrapolation of arrival time
        assert (speed != 0)
        arrival_time = distance / speed

        # ~ # Take into account deceleration in extrapolation of arrival time
        # ~ tstop = -speed/acceleration
        # ~ dstop = tstop*speed*0.5
        # ~ if dstop > distance:
        # ~ # copied from previous case
        # ~ arrival_time = -(speed / acceleration) + math.sqrt(((speed * speed) / (acceleration * acceleration)) + ((2 * distance) / acceleration))
        # ~ else:
        # ~ arrival_time = VERY_LARGE_FLOAT

    else:
        if speed != 0:
            arrival_time = distance / speed
            # print arrival_time
            logging.info("executed3")
        if speed == 0:
            arrival_time = VERY_LARGE_FLOAT

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
    if phaseNo == 1:
        # TODO: adjust for left turners

        if (remaining > arrival_time or (isLeftTurner and remaining + LEFT_TURN_SEPERATE_GREEN_TIME > arrival_time)):
            # ~ if (remaining >= arrival_time + ARRIVAL_MARGIN):
            # This vehicle will pass, let it go with desired max speed

            traci.vehicle.setSpeed(veh_id, -1)
            advisedSpeed = MAX_SPEED
            logging.info("MAX SPEED %s ", str(veh_id))

        else:
            nextGreenPhase = 59 + remaining + ARRIVAL_MARGIN

            # if isLeftTurner:
            #     if slow_down_flag==1:
            #         nextGreenPhase=nextGreenPhase+GREEN_PHASE_DURATION

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
            if isLeftTurner:
                if slow_down_flag == 1:
                    myGreenPhase = nextGreenPhase + CYCLE_LENGTH + GREEN_PHASE_DURATION
                else:
                    myGreenPhase = nextGreenPhase + CYCLE_LENGTH
            else:

                myGreenPhase = nextGreenPhase + CYCLE_LENGTH
            advisedSpeed = max(0, ((2 * distance) / (myGreenPhase)) - speed)
        else:
            # Vehicle will arrive in the next green phase
            if isLeftTurner:
                if slow_down_flag == 1:
                    myGreenPhase = nextGreenPhase + GREEN_PHASE_DURATION
                else:
                    myGreenPhase = nextGreenPhase
            else:
                myGreenPhase = nextGreenPhase
            advisedSpeed = max(0, ((2 * distance) / (myGreenPhase)) - speed)

        traci.vehicle.slowDown(veh_id, advisedSpeed, ((myGreenPhase) * 1000))

        """
        if arrival_time > greenPhaseEnd:
            # Vehicle won't arrive in next green phase. Assume that it will in the one afterwards
            myGreenPhase = nextGreenPhase + CYCLE_LENGTH
            advisedSpeed = max(0, ((2 * distance) / (myGreenPhase)) - speed)
        else:
            # Vehicle will arrive in the next green phase
            myGreenPhase = nextGreenPhase
            advisedSpeed = max(0, ((2 * distance) / (myGreenPhase)) - speed)

        traci.vehicle.slowDown(veh_id, advisedSpeed, ((myGreenPhase) * 1000))
        """
        # if advisedSpeed > MAX_SPEED:
        #    advisedSpeed =MAX_SPEED

        logging.info( "Arrive in GREEN PHASE %s %s", str(myGreenPhase),  str(np.ceil(arrival_time / 90)))
        status[veh_id] = 1

    if advisedSpeed == 0 and speed != 0:
        # cannot ensure arrival with uniform deceleration until next green at time tG,
        # i.e. got to perform a stop at remaining distance at time tstop = - v0/a < tG.
        # distance = t_stop*(2*v0 + a*tstop)*0.5 = -0.5*v0*v0/a
        # Thus, a = -v0*v0/(2*distance) and tstop = 2*distance/v0
        tstop = 2 * distance / speed
        traci.vehicle.slowDown(veh_id, advisedSpeed, (tstop * 1000))

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
    global ARRIVAL_MARGIN
    ARRIVAL_MARGIN = arriveMargin
    run(port)
    sumoProcess.wait()


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    rand_int=random.randint(1, 1000000000)
    sumoProcess = subprocess.Popen(
        [sumoBinary, "--seed", str(531450532), "-c", "demo.sumo.cfg",
         "--tripinfo-output",
         "tripinfo.xml", "--emission-output", "emission.xml", "--remote-port", str(PORT)], stdout=sys.stdout,
        stderr=sys.stderr)
    run(PORT)
    sumoProcess.wait()




"""
def caller(veh_ids,positionJunctionX):
    arraySize = len(veh_ids)
    for x in range(0, arraySize):
        print "vehicle Id", veh_ids[x]
        xPosition, yPosition = traci.vehicle.getPosition(veh_ids[x])
        distance = positionJunctionX - xPosition

        # if distance > 240:
        #    status[veh_ids[x]] = 0
        phrase = traci.trafficlight.getRedYellowGreenState("gneJ1")
        # get vehid  setup outsde func
        if phrase == "rrrrGGGgrrrrGGGg":
            #print ">>>PHRASE 1<<<"
            phraseNo = 1
            algo(veh_ids[x], positionJunctionX, phraseNo)

        elif phrase == "rrrryyygrrrryyyg":
            #print ">>>PHRASE 2<<<"
            phraseNo = 2
            algo(veh_ids[x], positionJunctionX, phraseNo)

        elif phrase == "rrrrrrrGrrrrrrrG":
            #print ">>>PHRASE 3<<<"
            phraseNo = 3
            algo(veh_ids[x], positionJunctionX, phraseNo)

        elif phrase == "rrrrrrryrrrrrrry":
            #print ">>>PHRASE 4<<<"
            phraseNo = 4
            algo(veh_ids[x], positionJunctionX, phraseNo)

        elif phrase == "GGGgrrrrGGGgrrrr":
            #print ">>>PHRASE 5<<<"
            phraseNo = 5
            algo(veh_ids[x], positionJunctionX, phraseNo)

        elif phrase == "yyygrrrryyygrrrr":
            #print ">>>PHRASE 6<<<"
            phraseNo = 6
            algo(veh_ids[x], positionJunctionX, phraseNo)

        elif phrase == "rrrGrrrrrrrGrrrr":
            #print ">>>PHRASE 7<<<"
            phraseNo = 7
            algo(veh_ids[x], positionJunctionX, phraseNo)

        elif phrase == "rrryrrrrrrryrrrr":
            #print ">>>PHRASE 8<<<"
            phraseNo = 8
            algo(veh_ids[x], positionJunctionX, phraseNo)
    print "-----------------------------------------------------------------------------------------------------------------------------"

"""
