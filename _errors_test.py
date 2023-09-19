#################### Test on Eye Diagram in Local

from pyaedt import Circuit

circuit = Circuit()
n=1

for i in range(0,n):
    #  Resistor
    res1 = circuit.modeler.components.create_resistor("R"+str(i), "100")

    #  Diff eye source
    eye_source_1= circuit.modeler.components.components_catalog["Independent Sources:EYESOURCE_DIFF"].place("V_"+str(i))

    #  Diff eye probes
    eye_probe_1= circuit.modeler.components.components_catalog["Probes:EYEPROBE_DIFF"].place("V_DIFF_"+str(i))
    eye_probe_1.parameters["Name"] = "V_DIFF_"+str(i)

    eye_source_1.pins[0].connect_to_component(eye_probe_1.pins[0])
    eye_source_1.pins[1].connect_to_component(eye_probe_1.pins[1])

    res1.pins[1].connect_to_component(eye_source_1.pins[1])
    res1.pins[0].connect_to_component(eye_source_1.pins[0])

circuit.create_setup(setupname="EYE_diagram", setuptype=circuit.SETUPS.NexximQuickEye)
circuit.analyze_setup("EYE_diagram")


for i in range(0,n):
    eye_diagrem_1 = circuit.post.reports_by_category.eye_diagram("AEYEPROBE(V_DIFF_"+str(i)+")", "EYE_diagram")
    eye_diagrem_1.create("V_DIFF_"+str(i))
    print("AEYEPROBE(V_DIFF_" + str(i) + ")")


#################### Test in Minerva
def moduleAvailable():
    available = True
    try:
      import pyaedt
    except ImportError:
      available = False

    return available

if not moduleAvailable() :
    import subprocess
    pip = subprocess.Popen([r"C:\Program Files\AnsysEM\v221\Win64\commonfiles\Cpython\3_7\winx64\Release\python\python.exe","-m", "pip", "install", "--upgrade", "pip"])
    pip.wait()
    pyaedt = subprocess.Popen([r"C:\Program Files\AnsysEM\v221\Win64\commonfiles\Cpython\3_7\winx64\Release\python\Scripts\pip.exe", "install", "pyaedt"])
    pyaedt.wait()
    ipython = subprocess.Popen([r"C:\Program Files\AnsysEM\v221\Win64\commonfiles\Cpython\3_7\winx64\Release\python\Scripts\pip.exe", "install", "ipython", "-U"])
    ipython.wait

import sys
from pyaedt import Edb

arg = sys.argv
aedb_path = arg[1]
edb = Edb(edbpath=aedb_path, edbversion="2021.2")
f = open("net_list.txt", "w")
for item in list(edb.core_nets.signal_nets.keys()):
    # write each item on a new line
    f.write(item)
f.close()