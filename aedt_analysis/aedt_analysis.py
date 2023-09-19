from pyaedt.modules.report_templates import EyeDiagram
from eye_diagram_modified import EyeDiagramMod
from pyaedt.generic import ibis_reader
from pyaedt import Circuit
from ibis_second import *
from functions import *
from math import pi
import ibis_second
import tempfile
import pyaedt
import json
import sys
import os
import re

args = sys.argv

if args:
    json_path = os.path.abspath(args[1])
    s_param_path = os.path.abspath(args[2])
    _, project_edb = os.path.split(s_param_path)
    project_name = project_edb.split(".")
    project_name = project_name[0] if isinstance(project_name, list) else project_name
    project_path = os.path.abspath(args[3])
    Version = args[4]

# s_param_path = "C:\\Users\\wcharles\\OneDrive - ANSYS, Inc\\Documents\\Wendjel Files\\Milestone_1\\_pcie_cut_out(f).s8p"
# project_path = r"D:\Temp\aedt_ana"
# json_path = r"input.json"

"""
    # INPUT
"""
## Open json file
j_file = open(json_path, "r")
jsonFile = json.load(j_file)
j_file.close()
# Make sure the first dictionary/keys in the .json file is "Sim Scan" (with space).
# It was done so that you can do different types of simulations
# in a single script with only one .json file
input_file = jsonFile["AEDT"]
imported_parameters = input_file["Parameters"]
default_parameters = {"Voltage source":
    {
        "vlow": "0V",
        "vhigh": "1V",
        "trise": "50ps",
        "tfall": "50ps",
        "UIorBPS": "UnitInterval",
        "UIorBPSValue": "1e-9s",
        "BitPattern": "random_bit_count=2.5e5 random_seed=1"
    }, "Eye diagram": {
    "eye_time_start": "0fs",
    "eye_time_stop": "200ns",
    "offset": "0ms",
    "manual_delay": "0ps",
    "cross_amplitude": "0mV",
    "eye_meas_pont": "5e-10s"
}, "Transient": {
    "trans_step": "0.1ns",
    "trans_stop": "10ns"
}
}

used_parameters = {}
for param_type in default_parameters.keys():
    sub_used_parameters = {}
    for param in default_parameters[param_type].keys():
        sub_used_parameters[param] = define_value(default_parameters[param_type][param],
                                                  imported_parameters, param)
    used_parameters[param_type] = sub_used_parameters

print(used_parameters)
# NETS  To be modified
Nets = {}
ext_keyword = "_EXT"
# first elements of each extended
# nets should be the shortest = full extended net name
# even if there are 4 pieces of an extended net that connect two components,
# we will consider only the two that are directly connected to these components
Nets["SingleEnded"] = input_file["SingleEnded Nets"] if "SingleEnded Nets" in input_file.keys() else []
Nets["Differential"] = input_file["Differential Nets"] if "Differential Nets" in input_file.keys() else []
Nets["Extended"] = input_file["Extended Nets"] if "Extended Nets" in input_file.keys() else []
# refDes = input_file["Components"]
refDes ={}
refDes["DriverComponents"] = input_file["Components"]["DriverComponents"][0]
refDes["ReceiverComponents"] = input_file["Components"]["ReceiverComponents"][0]
idealistic = True if input_file["Ideal"] == "False" else False
#######################################

perm_folder = os.path.join(project_path, "Aedt_sim")
if not os.path.exists(perm_folder):
    os.makedirs(perm_folder)

reports = os.path.join(perm_folder, "Html-reports")
if not os.path.exists(reports):
    os.makedirs(reports)
circuit = Circuit(specified_version=Version, projectname=os.path.join(perm_folder, project_name+".aedt"))
oEditor = circuit.modeler.oeditor

"""
    # INSERT COMPONENTS
"""

# Import S-parameters
s_param = NPortsComp(Nets, ext_keyword, refDes, s_param_path, circuit)
sparam_component = s_param.insert_get_from_touchstone("PCIE_Express 1X", location=[0.09, 0.02])
s_info = s_param.components_pins_info()
print(s_info)
io = s_param.identify_in_out_ports()
print(io)
n_s_e, n_diff = s_param.count_nets()
print(n_s_e, n_diff)
# Display as json, useless
with open('io_visual.json', 'w') as f:
    json.dump(io, f, indent=2)

list_y_pins=[]
for pin in sparam_component.pins:
    x,y = pin.location
    list_y_pins.append(y)

y_port_s_param_max= max(list_y_pins)
y_port_s_param_min= min(list_y_pins)

x_s_param, y_s_param = sparam_component.location
x_s_param = x_s_param.split("mil")
x_s_param = float(x_s_param[0]) * 0.000025  # convert mil to meter
y_s_param = y_s_param.split("mil")
y_s_param = float(y_s_param[0]) * 0.000025  # convert mil to meter

components=input_file["Components"]

if not idealistic:
    ibis_path = r"C:\Program Files\AnsysEM\AnsysEM21.2\Win64\buflib\IBIS\u26a_800.ibs"
    if "IBIS_driver_file" in  input_file["Components"].keys():
        ibis_path = input_file["Components"]["IBIS_driver_file"]
    # Read Ibis file, create class without using Aedt/circuit -
    # juste read it nothing more
    ibis = ibis_reader.IbisReader(ibis_path, None)  # circuit = None
    ibis.parse_ibis_file()
    ibis = ibis.ibis_model
    ibis_with_diff = ibis_second.IbisInsertPinExt(ibis, circuit, ibis_path)
    ibis_with_diff.assign_diff_list(["MT47H16M16BG-3_25", 'F7', 'E8'])

#### Trigger
    trig_io = circuit.modeler.components.components_catalog["Independent Sources:EYESOURCE"].\
        place(inst_name="io_trigger",location=[x_s_param+0.01, y_port_s_param_max+0.03], angle=0)
    print(trig_io)
    for param in used_parameters["Voltage source"].keys():
        trig_io.parameters[param] = used_parameters["Voltage source"][param]
    [x_pin, y_pin] = trig_io.pins[0].location
    port_name = "io_trig"
    port_io = circuit.modeler.components.create_page_port(port_name, [x_pin, y_pin])
else:
    gnd = circuit.modeler.components.create_gnd([x_s_param+0.01, y_port_s_param_max+0.03])
    page_port_wire(circuit, gnd, gnd.pins[0], gnd.name.split("GPort@")[1], 0)


# Connect Components with page_port
all_eye = {}
all_ibis = {}
all_eye_sources = {}
page_port_to_transfer = []
for type_of_nets in ["Differential", "SingleEnded"]:
    if Nets[type_of_nets]:
        io_ibis = {}
        io_eye = {}
        for io_type in ["outputs", "inputs"]:
            differential = True if type_of_nets == "Differential" else False

            n_times = n_diff if type_of_nets == "Differential" else n_s_e
            if io_type == "inputs":
                buffer_mode = "Output Buffer"
                x_ibis = 0.0
                x_eye = 0.03
            else:
                buffer_mode = "Input Buffer"
                x_ibis = 0.14
                x_eye = 0.09

            if not idealistic :
                model = "DQ_FULL_ODT50_800 "
                models = [model, model] if differential else [model]
                n_ibis_io = insert_n_type_buffer(start_x=x_ibis, start_y=10,
                                                 component=ibis.components["MT47H16M16BG-3_25"].pins[
                                                     "F7_MT47H16M16BG-3_25_u26a_800"],
                                                 ibisMod=ibis_with_diff, buffer_mode=buffer_mode, space=0.03,
                                                 nTimes=n_times,
                                                 diffN0=differential,
                                                 buffer_models=models)
                if buffer_mode == "Output Buffer":
                    for ibis_component in n_ibis_io.keys():
                        ibis_with_diff.excitation_port(n_ibis_io[ibis_component], port_name)

                page_ports_ibis = connect_components(circuit=circuit, port_info=s_info, port_io=io, component_1=n_ibis_io,
                                   component_2=sparam_component, type_net=type_of_nets, io=io_type)

                page_port_to_transfer += page_ports_ibis

            if idealistic and io_type == "inputs":
                io_eye_sources = insert_n_eye_source(circuit=circuit, type=type_of_nets, nTimes=n_times,
                                                     angle=pi, start_x=x_ibis, start_y=10, space=0.03)
                page_ports_eye_source = connect_components(circuit=circuit, port_info=s_info, port_io=io,
                                                           component_1=io_eye_sources,
                                                           component_2=sparam_component, type_net=type_of_nets,
                                                           io=io_type, eye_source=True)
                page_port_to_transfer += page_ports_eye_source

                    # circuit.modeler.components.create_resistor(compname=None, value=50, location=[x_res,y_res], angle=90, use_instance_id_netlist=False)


            eye_io = insert_n_eye_probe(circuit=circuit, type=type_of_nets,
                                        nTimes=n_times, angle=90, start_x=x_eye, start_y=10, space=0.03)
            rename_eye_probe(port_io=io, eye_probe=eye_io, type_net=type_of_nets, io=io_type)
            page_ports_eye_probe = connect_components(circuit=circuit, port_info=s_info, port_io=io, component_1=eye_io,
                                                      component_2=sparam_component, type_net=type_of_nets, io=io_type
                                                      , ports_on_component_2=False)
            if  idealistic and io_type == "outputs":
                y_res = 0
                resistor_dict = {}

                x_res = x_ibis
                eye_probe_list = list(eye_io.values())
                index=0
                if type_of_nets == "Differential":
                    for i in range(0, 2 * n_diff):
                        if not i%2 == 0:
                            v_r = "RES_" + str(i)
                            _, y_res = eye_probe_list[index].pins[1].location
                            resistor_dict[v_r] = circuit.modeler.components.components_catalog["Resistors:RES_"]. \
                                place(inst_name=None, angle=pi, location=[x_res, y_res])
                            v_r = "RES_" + str(i+1)
                            _, y_res = eye_probe_list[index].pins[0].location
                            resistor_dict[v_r] = circuit.modeler.components.components_catalog["Resistors:RES_"]. \
                                place(inst_name=None, angle=pi, location=[x_res, y_res])
                            index += 1
                elif type_of_nets == "SingleEnded":
                    for i in range(0, n_s_e):
                            v_r = "RES_" + str(i)
                            _, y_res = eye_probe_list[i].pins[0].location
                            resistor_dict[v_r] = circuit.modeler.components.components_catalog["Resistors:RES_"]. \
                                place(inst_name=None, angle=pi, location=[x_res, y_res])

                    # y_res += 0.02
                page_ports_res = connect_components(circuit=circuit, port_info=s_info, port_io=io,
                                                    component_1=resistor_dict,
                                                    component_2=sparam_component, type_net=type_of_nets,
                                                    io=io_type, resistor=True, ports_on_component_2=False)
                page_port_to_transfer += page_ports_res
                gnd_ports = {}
                i = 0
                for key in resistor_dict.keys():
                    gnd_ports[i] = page_port_wire(circuit, resistor_dict[key],
                                                  resistor_dict[key].pins[1], gnd.name.split("GPort@")[1], 0)
                    i += 1

            page_port_to_transfer += page_ports_eye_probe
            io_ibis[io_type] = n_ibis_io if not idealistic else {}
            io_eye[io_type] = eye_io

        all_eye_sources[type_of_nets] = io_eye_sources  if idealistic else {}
        all_ibis[type_of_nets] = io_ibis if not idealistic else {}
        all_eye[type_of_nets] = io_eye

list_resistor = list(resistor_dict.values()) if  idealistic else []
list_gnd_ports = list(gnd_ports.values()) if  idealistic else []
list_all_ibis = []
list_all_eye = []
list_eye_sources = []
print(all_ibis)

for type_ in ["Differential", "SingleEnded"]:
    if type_ in all_eye_sources.keys() and len(all_eye_sources[type_])  :
        list_eye_sources += list(all_eye_sources[type_].values())

    for type_io in ["outputs", "inputs"]:
        if type_ in all_eye.keys() and type_io in all_eye[type_].keys() and len(all_eye):
            list_all_eye  += list(all_eye[type_][type_io].values())
        if type_ in all_ibis.keys() and type_io in all_ibis[type_].keys() and len(all_ibis):
            list_all_ibis += list(all_ibis[type_][type_io].values())
        # list_eye_sources += list(all_eye_sources[type_][type_io].values())
print(list_all_ibis)
all_components_to_tranfer = page_port_to_transfer + list_eye_sources + list_all_eye \
                            + list_resistor + list_gnd_ports + list_all_ibis

selections = []
for comp in all_components_to_tranfer:
    selections.append(comp.composed_name)

print(selections)
oEditor.CreatePage("INPUTS/OUTPUTS")
oEditor.SelectPage(1)
oEditor.ChangeProperty(
    [
        "NAME:AllTabs",
        [
            "NAME:BaseElementTab",
            [
                "NAME:PropServers",
                "Page@1"
            ],
            [
                "NAME:ChangedProps",
                [
                    "NAME:Title",
                    "Value:=", "MODEL"
                ]
            ]
        ]
    ])
cut(oEditor,selections)
oEditor.SelectPage(2)
paste(oEditor)
oEditor.SelectPage(1)


list_y_pins_non_repetitive =[]
for y in list_y_pins:
    if y not in list_y_pins_non_repetitive:
        list_y_pins_non_repetitive.append(y)

componenst_associated_port = {}
temporary_info= s_info
for comp_type in ["DriverComponents", "ReceiverComponents"]:
    i = 0
    start_y = 0
    for comp in components[comp_type]:
        ports_list = []
        for port in list(temporary_info.keys()):
            if re.findall(".*" + comp + ".*", port):
                ports_list.append(port)
                del temporary_info[port]
        componenst_associated_port[comp] = ports_list

for nets_type in all_eye.keys():
    if all_eye[nets_type]:
        for io_type in all_eye[nets_type].keys():
            for comp in list(all_eye[nets_type][io_type].values()):
                create_text_box_io(oEditor, comp, io_type)

oEditor.SelectPage(2)
objs = oEditor.GetAllElements()
objs = [i for i in objs if "SchObj" in i[:6]]
print(objs)
cut(oEditor, objs)
paste(oEditor)


for comp_type in ["DriverComponents", "ReceiverComponents"]:
    i=0
    start_y = 0
    for comp in components[comp_type]:
        first = True if i ==0 else False
        start_y= create_text_box(circuit, comp_type, comp, list_y_pins_non_repetitive, componenst_associated_port[comp],
                    center_location=[x_s_param, y_s_param],start_y=start_y, space = 0.01, realistic_design= False, first_type_box=first)
        i += 1


if not idealistic:
    create_text_box_io(oEditor, trig_io, "inputs", name="VOLTAGE SOURCE", page_num=1)
else:
    create_text_box_io(oEditor, gnd, "inputs", name="REFERENCE GND", page_num=1)

### Setup
transient = circuit.create_setup(setupname="Transient analysis", setuptype="NexximTransient")
transient.props["TransientData"] = [used_parameters["Transient"]["trans_step"],
                                    used_parameters["Transient"]["trans_stop"]]
quick_eye = circuit.create_setup(setupname="Quick eye analysis", setuptype=circuit.SETUPS.NexximQuickEye)
circuit.analyze_setup("Quick eye analysis")
circuit.analyze_setup("Transient analysis")

"""
# POST-PROCESSING
"""

# Eye Diagram end EyeProbe  name list
eye_input_name = []
eye_output_name = []
id_count = 0
eye = EyeDiagramMod(circuit.post, "Eye Diagram", "Quick eye analysis")
eye.unit_interval = used_parameters["Voltage source"]["UIorBPSValue"]
eye.time_start = used_parameters["Eye diagram"]["eye_time_start"]
eye.time_stop = used_parameters["Eye diagram"]["eye_time_stop"]
eye.offset = used_parameters["Eye diagram"]["offset"]
eye.eye_meas_pont = used_parameters["Eye diagram"]["eye_meas_pont"]
eye.manual_delay= used_parameters["Eye diagram"]["manual_delay"]

for eye_type in all_eye.keys():
    for eye_io_type in all_eye[eye_type].keys():
        for eye_name in all_eye[eye_type][eye_io_type].keys():
            if eye_io_type == "inputs":
                eye_input_name.append(all_eye[eye_type][eye_io_type][eye_name].parameters["Name"])
            else:
                eye_output_name.append(all_eye[eye_type][eye_io_type][eye_name].parameters["Name"])
            eye.expressions = "AEYEPROBE(" + str(all_eye[eye_type][eye_io_type][eye_name].parameters["Name"]) + ")"
            eye.create(plot_name=str(all_eye[eye_type][eye_io_type][eye_name].parameters["Name"]),
                       component_class=all_eye[eye_type][eye_io_type][eye_name], int_id=id_count)
            id_count += 1

# Transient Plots
for i in range(0, len(eye_output_name)):
    circuit.post.create_report(
        expressions=["V(AEYEPROBE(" + eye_input_name[i] + ").out)", "V(AEYEPROBE(" + eye_output_name[i] + ").out)"],
        setup_sweep_name="Transient analysis",
        domain="Time", plot_type="Rectangular Plot", plotname="Transient " + eye_output_name[i].split()[0])

# circuit.modeler._odesign.GetModule("UserDefinedDocuments").AddDocument(
#     [
#         "NAME:Design Summary", "", "SysLib", "DesignSummary",
#         [
#             "NAME:Inputs"
#         ]
#     ],
#     [
#         "NAME:DocTraces"
#     ])
#
#
# circuit.modeler._odesign.GetModule("UserDefinedDocuments"). \
#     SaveHtmlDocumentAs("Design Summary", os.path.join(perm_folder, "Html-reports"))

## Save project
circuit.save_project(os.path.join(perm_folder, project_name+".aedt"))
circuit.release_desktop( close_projects=False, close_desktop=False)

