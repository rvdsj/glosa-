import xml.etree.cElementTree as ET

import xml.dom.minidom

routes = ET.Element("routes")
ET.SubElement(routes, "vType", id="car", sigma="0.0", vClass="passenger", guiShape="passenger", emergencyDecel="9")

ET.SubElement(routes, "route", id="route0", edges="gneE0 gneE1")
ET.SubElement(routes, "route", id="route1", edges="gneE0 gneE2")
ET.SubElement(routes, "route", id="route2", edges="gneE0 gneE3")

ET.SubElement(routes, "route", id="route3", edges="gneE7 gneE3")
ET.SubElement(routes, "route", id="route4", edges="gneE7 gneE2")
ET.SubElement(routes, "route", id="route5", edges="gneE7 gneE5")

ET.SubElement(routes, "route", id="route6", edges="gneE6 gneE5")
ET.SubElement(routes, "route", id="route7", edges="gneE6 gneE3")
ET.SubElement(routes, "route", id="route8", edges="gneE6 gneE1")

ET.SubElement(routes, "route", id="route9", edges="gneE8 gneE2")
ET.SubElement(routes, "route", id="route10", edges="gneE8 gneE1")
ET.SubElement(routes, "route", id="route11", edges="gneE8 gneE5")

left_lane_veh = [ 's1', 's2','l1' ,'s3', 's4','s5', 's6','l2','s7','s8','s9','l3','s10'z]
#left_lane_veh = [ 's1', 's2','s3', 's4','s5', 's6','s7','s8','s9','s10','l1','l2','l3']
right_lane_veh = ['s1', 's2','s3','s4','s5','s6']
left_lane_veh_opposite = [ 's1', 's2','l1' 'l2', 'l3','s3', 's4', 's5', 's6','s7','s8','s9','s10']
right_lane_veh_opposite = ['s1', 's2', 's3', 's4', 's5']

gap = 4
period = len(left_lane_veh) * gap
straight_counter = 1
left_turner_counter = 1
rightlane_counter = 1
opposite_straight_counter = 1
opposite_left_turner_counter = 1
opposite_rightlane_counter = 1

for x in range(0, len(left_lane_veh)):
    if left_lane_veh[x].find("s") != -1:
        ET.SubElement(routes, "flow", type="car", id="straight" + str(straight_counter), begin=str(x * gap), end="200",
                      period=str(period), route="route0", departLane="1")
        straight_counter = straight_counter + 1
    elif left_lane_veh[x].find("l") != -1:
        ET.SubElement(routes, "flow", type="car", id="left" + str(left_turner_counter), begin=str(x * gap), end="200",
                      period=str(period), route="route1", departLane="1", color="white")
        left_turner_counter = left_turner_counter + 1

    if (len(left_lane_veh_opposite) >= x + 1):
        if left_lane_veh_opposite[x].find("s") != -1:
            ET.SubElement(routes, "flow", type="car", id="straight_opposite" + str(opposite_straight_counter),
                          begin=str(x * gap), end="200", period=str(period), route="route5", departLane="1")
            opposite_straight_counter = opposite_straight_counter + 1
        elif left_lane_veh_opposite[x].find("l") != -1:
            ET.SubElement(routes, "flow", type="car", id="left_opposite" + str(opposite_left_turner_counter),
                          begin=str(x * gap), end="200", period=str(period), route="route3", departLane="1",
                          color="white")
            opposite_left_turner_counter = opposite_left_turner_counter + 1

    if (len(right_lane_veh) >= x + 1):
        ET.SubElement(routes, "flow", type="car", id="rightlane" + str(rightlane_counter), begin=str((x * gap)+2),
                      end="200", period=str(period), route="route0", departLane="0", color="blue")
        rightlane_counter = rightlane_counter + 1

    if (len(right_lane_veh_opposite) >= x + 1):
        ET.SubElement(routes, "flow", type="car", id="rightlane_opposite" + str(opposite_rightlane_counter),
                      begin=str((x * gap)+2), end="200", period=str(period), route="route5", departLane="0", color="blue")
        opposite_rightlane_counter = opposite_rightlane_counter + 1

tree = ET.ElementTree(routes)
tree.write("filename.xml")

xml = xml.dom.minidom.parse("filename.xml")  # or xml.dom.minidom.parseString(xml_string)
pretty_xml_as_string = xml.toprettyxml()
print pretty_xml_as_string

f = open("filename.xml", "w")
f.write(pretty_xml_as_string)


