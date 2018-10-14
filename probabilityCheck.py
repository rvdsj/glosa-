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

gap = 4
number_stright_left_lane=11
number_left_turn_left_lane=4
number_right_lane=10

opposite_number_stright_left_lane=10
opposite_number_left_turn_left_lane=3
opposite_number_right_lane=5


gap = 4
probability = 1. / ((number_stright_left_lane+number_left_turn_left_lane)*gap)
probability_opposite = 1. / ((opposite_number_stright_left_lane+opposite_number_left_turn_left_lane)*gap)


straight_counter = 1
left_turner_counter = 1
rightlane_counter = 1
opposite_straight_counter = 1
opposite_left_turner_counter = 1
opposite_rightlane_counter = 1


for x in range(0,number_stright_left_lane):
    ET.SubElement(routes, "flow", type="car", id="straight" + str(straight_counter), begin="0", end="200",probability=str(probability), route="route0", departLane="1")
    straight_counter = straight_counter + 1

for x in range(0,number_left_turn_left_lane):
    ET.SubElement(routes, "flow", type="car", id="left" + str(left_turner_counter), begin="0", end="200",probability=str(probability), route="route1", departLane="1", color="white")
    left_turner_counter = left_turner_counter + 1

for x in range(0,number_right_lane):
    ET.SubElement(routes, "flow", type="car", id="rightlane" + str(rightlane_counter), begin="0",end="200", probability=str(probability), route="route0", departLane="0", color="blue")
    rightlane_counter = rightlane_counter + 1

for x in range(0,opposite_number_stright_left_lane):
    ET.SubElement(routes, "flow", type="car", id="straight_opposite" + str(opposite_straight_counter),begin="0", end="200",probability=str(probability_opposite), route="route5", departLane="1")
    opposite_straight_counter = opposite_straight_counter + 1

for x in range(0,opposite_number_left_turn_left_lane):
    ET.SubElement(routes, "flow", type="car", id="left_opposite" + str(opposite_left_turner_counter),begin="0", end="200", probability=str(probability_opposite), route="route3", departLane="1",color="white")
    opposite_left_turner_counter = opposite_left_turner_counter + 1

for x in range(0,opposite_number_right_lane):
    ET.SubElement(routes, "flow", type="car", id="rightlane_opposite" + str(opposite_rightlane_counter),begin="0", end="200", probability=str(probability_opposite), route="route5", departLane="0", color="blue")
    opposite_rightlane_counter = opposite_rightlane_counter + 1

tree = ET.ElementTree(routes)
tree.write("filename.xml")

xml = xml.dom.minidom.parse("filename.xml")  # or xml.dom.minidom.parseString(xml_string)
pretty_xml_as_string = xml.toprettyxml()
print pretty_xml_as_string

f = open("filename.xml", "w")
f.write(pretty_xml_as_string)


