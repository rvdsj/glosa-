import xml.etree.cElementTree as ET

import xml.dom.minidom

routes = ET.Element("routes")
ET.SubElement(routes, "vType", id="car",sigma="0.0",vClass="passenger",guiShape="passenger",emergencyDecel="9")

ET.SubElement(routes,"route", id="route0",edges="gneE0 gneE1")
ET.SubElement(routes,"route", id="route1",edges="gneE0 gneE2")
ET.SubElement(routes,"route", id="route2",edges="gneE0 gneE3")

ET.SubElement(routes,"route", id="route3",edges="gneE7 gneE3")
ET.SubElement(routes,"route", id="route4",edges="gneE7 gneE2")
ET.SubElement(routes,"route", id="route5",edges="gneE7 gneE5")

ET.SubElement(routes,"route", id="route6",edges="gneE6 gneE5")
ET.SubElement(routes,"route", id="route7",edges="gneE6 gneE3")
ET.SubElement(routes,"route", id="route8",edges="gneE6 gneE1")

ET.SubElement(routes,"route", id="route9",edges="gneE8 gneE2")
ET.SubElement(routes,"route", id="route10",edges="gneE8 gneE1")
ET.SubElement(routes,"route", id="route11",edges="gneE8 gneE5")


number_straight_vehicles=11
number_left_turners=4
gap = 4
period= (number_straight_vehicles+number_left_turners)*gap
for x in range(1,number_straight_vehicles+1):
    ET.SubElement(routes,"flow", type="car",id="straight"+str(x),begin=str(x*gap),end="200",period=str(period),route="route0",departLane="1")
    ET.SubElement(routes, "flow", type="car", id="rightlane" + str(x), begin=str(x * gap), end="200", period=str(period),route="route0", departLane="0")

    #for opposite direction
    ET.SubElement(routes, "flow", type="car", id="straight_opposite" + str(x), begin=str(x * gap), end="200", period=str(period),route="route5", departLane="1")
    ET.SubElement(routes, "flow", type="car", id="rightlane_opposite" + str(x), begin=str(x * gap), end="200",period=str(period), route="route5", departLane="0")

for y in range(1,number_left_turners+1):
    ET.SubElement(routes, "flow", type="car", id="left"+str(y), begin=str((number_straight_vehicles+y) * gap), end="200", period=str(period),route="route1", departLane="1", color="white")
    ET.SubElement(routes, "flow", type="car", id="left_opposite" + str(y), begin=str((number_straight_vehicles + y) * gap),end="200", period=str(period), route="route3", departLane="1", color="white")
    # generate flows - vehicles  right lane (rest)
    ET.SubElement(routes, "flow", type="car", id="rightlane" + str(number_straight_vehicles+y), begin=str((number_straight_vehicles+y) * gap), end="200", period=str(period),route="route0", departLane="0")
    #generate flows - vehicles opposite direction right lane (rest)
    ET.SubElement(routes, "flow", type="car", id="rightlane_opposite" + str(number_straight_vehicles+y), begin=str((number_straight_vehicles+y) * gap), end="200", period=str(period),route="route5", departLane="0")


tree = ET.ElementTree(routes)
tree.write("filename.xml")

xml = xml.dom.minidom.parse("filename.xml") # or xml.dom.minidom.parseString(xml_string)
pretty_xml_as_string = xml.toprettyxml()
print pretty_xml_as_string

f = open("filename.xml", "w")
f.write(pretty_xml_as_string)