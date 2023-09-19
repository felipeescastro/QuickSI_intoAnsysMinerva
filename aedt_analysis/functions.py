from ibis_second import *
import re
import math
from random import randint

def cut(oEditor, selections):
    oEditor.Cut(
        [
            "NAME:Selections",
            "Selections:=", selections
        ])

def paste(oEditor,Page= 2,X=0,Y=0, Angle=0):
    oEditor.Paste(
        [
            "NAME:Attributes",
            "Page:="	, Page,
            "X:="			, X,
            "Y:="			, Y,
            "Angle:="		, Angle,
            "Flip:="		, False
        ])
def create_page(circuit, page_name):
    circuit.modeler.oeditor.CreatePage(page_name)


def select_page(circuit, page_number):
    circuit.modeler._oeditor.SelectPage(page_number)


def cut_from_to(circuit, from_page, to_page, selections=[],
                                    location=[0, 0], angle=0):
    select_page(circuit, from_page)
    circuit.modeler._oeditor.Cut(
        [
            "NAME:Selections",
            "Selections:=", selections
        ])
    select_page(circuit, to_page)
    circuit.modeler._oeditor.Paste(
        [
            "NAME:Attributes",
            "Page:=", to_page,
            "X:="	, location[0],
            "Y:="			, location[1],
            "Angle:="		, angle,
            "Flip:="		, False
        ])
    select_page(circuit, from_page)

def define_value(default_value, parameters, parameter_name):
    if parameter_name in parameters.keys() and parameters[parameter_name]:
        return parameters[parameter_name]
    else:
        return default_value


def connect_components(circuit, port_info, port_io, component_1, component_2,
                       type_net, io, eye_source= False, resistor = False,
                       ports_on_component_2 = False):
    e = 0.02
    page_ports =[]
    count_comp1 = 0
    if port_io[type_net]:
        keys = list(component_1.keys())
        for key2 in port_io[type_net][io].keys():
            key1 = keys[count_comp1]
            print(key1)
            r_net_key = list(port_io[type_net][io][key2].keys())
            if eye_source:
                pos_pin =1
                neg_pin =0
            else:
                pos_pin = 0
                neg_pin = 1

            if type_net == "SingleEnded" or type_net == "Differential":
                positive_port = port_io[type_net][io][key2][r_net_key[0]]
                if type(positive_port) is dict:
                    buf = list(port_io[type_net][io][key2][r_net_key[0]].values())
                    positive_port = buf[0]
                # component_2.pins[port_info[positive_port]].connect_to_component(component_1[key1].pins[0])
                if not ports_on_component_2:
                    page_port_wire(circuit=circuit, component=component_2,
                                   pin=component_2.pins[port_info[positive_port]],
                                   name=component_2.pins[port_info[positive_port]].name, space=e)

                page_port1 = page_port_wire(circuit=circuit, component=component_1[key1],
                               pin=component_1[key1].pins[pos_pin],
                               name=component_2.pins[port_info[positive_port]].name, space=0)
                page_ports.append(page_port1)

            if type_net == "Differential" and not resistor: # to be verified
                negative_port = port_io[type_net][io][key2][r_net_key[1]]
                if type(negative_port) is dict:
                    buf = list(port_io[type_net][io][key2][r_net_key[1]].values())
                    negative_port = buf[0]
                # component_2.pins[port_info[negative_port]].connect_to_component(component_1[key1].pins[1])

                if not ports_on_component_2:
                    page_port_wire(circuit=circuit, component=component_2,
                                   pin=component_2.pins[port_info[negative_port]],
                                   name=component_2.pins[port_info[negative_port]].name, space=e)

                page_port2 = page_port_wire(circuit=circuit, component=component_1[key1],
                               pin=component_1[key1].pins[neg_pin],
                               name=component_2.pins[port_info[negative_port]].name, space=0)
                page_ports.append(page_port2)

            if type_net == "Differential" and resistor:
                count_comp1 +=1
                negative_port = port_io[type_net][io][key2][r_net_key[1]]
                if type(negative_port) is dict:
                    buf = list(port_io[type_net][io][key2][r_net_key[1]].values())
                    negative_port = buf[0]
                print(keys[count_comp1])
                page_port_res = page_port_wire(circuit=circuit, component=component_1[keys[count_comp1]],
                               pin=component_1[keys[count_comp1]].pins[pos_pin],
                               name=component_2.pins[port_info[negative_port]].name, space=0)
                page_ports.append(page_port_res)
            count_comp1 += 1
    return page_ports



def page_port_wire(circuit, component, pin, name, space=0.02):
    """ Draw wire to page port

    Parameters
    ----------
    circuit: object
    component: object
        the component whose pins are being connected
    pin: object
        Pin to which the page port will be connected
    name: str
        page port name
    space: float, optional
        Separation between several eye probes.  The default is ``0.2``.


    """
    [x_comp, _] = component.location
    x_comp = x_comp.split("mil")
    x_comp = float(x_comp[0]) * 0.000025  # convert mil to meter
    [x_pin, y_pin] = pin.location
    # We assume that the location of the components is in the center of the mass.
    if x_pin <= x_comp:
        angle = 0
        space = -1 * space
    else:
        angle = math.pi
    # the location of the page port is the same as its pin location
    page_port = circuit.modeler.components.create_page_port(name, [float(x_pin) + space, y_pin], angle)
    points_array = [[x_pin, y_pin], [x_pin + space, y_pin]]
    circuit.modeler.components.create_wire(points_array)
    return page_port


def insert_n_eye_probe(circuit, type, nTimes=1, angle=90, start_x=0.06, start_y=0, space=0.02):
    """ Insert n eye probes

    Parameters
    ----------
    circuit: object
    type: str
        'Differential' or 'SingleEnded'
    nTimes: int, optional
        number of times to insert eye probes
    angle: float, optional
        angle of the eye probe in the schematic
    start_x: float, optional
        X coordinate of the first eye probe
    start_y: float, optional
        Y coordinate of the first eye probe
    space:  float, optional
        Separation between several eye probes

    Parameters
    ----------
    probe_dict : dict
        class:`pyaedt.modeler.Object3d.CircuitComponent`

    """
    name = ''
    if type == "Differential":
        name = "Probes:EYEPROBE_DIFF"
    elif type == "SingleEnded":
        name = "Probes:EYEPROBE"
    probe_dict = {}
    for i in range(nTimes):
        v_r = "EYEPROBE" + str(i)
        probe_dict[v_r] = circuit.modeler.components.components_catalog[name]. \
            place(inst_name=None, angle=angle, location=[start_x, start_y])
        start_y += space
    return probe_dict


def rename_eye_probe(port_io, eye_probe, type_net, io):
    """Rename the eye probes

    Parameters
    ----------
    port_io : dict
        Dictionary containing information related to the NPort component imported, to which
        the eye probe will be connected
    eye_probe : object
        class:`pyaedt.modeler.Object3d.CircuitComponent`
        The eye probe component
    type_net: str
        The type of nets that will be connected to the eye probe
    io : dict
        input or output, to be added at the end of the probe name


    """
    count_comp1 = 0
    if port_io[type_net]:
        for key2 in port_io[type_net][io].keys():
            keys = list(eye_probe.keys())
            key1 = keys[count_comp1]
            count_comp1 += 1
            eye_probe[key1].parameters["Name"] = key2 + " " + io[:len(io) - 1]

def insert_n_eye_source(circuit, type, nTimes=1, angle=90, start_x=0.06, start_y=0, space=0.02):
    """ Insert n eye probes

    Parameters
    ----------
    circuit: object
    type: str
        'Differential' or 'SingleEnded'
    nTimes: int, optional
        number of times to insert eye probes
    angle: float, optional
        angle of the eye probe in the schematic
    start_x: float, optional
        X coordinate of the first eye probe
    start_y: float, optional
        Y coordinate of the first eye probe
    space:  float, optional
        Separation between several eye probes

    Parameters
    ----------
    source_dict : dict
        class:`pyaedt.modeler.Object3d.CircuitComponent`

    """
    name = ''
    if type == "Differential":
        name = "Independent Sources:EYESOURCE_DIFF"
    elif type == "SingleEnded":
        name = "Independent Sources:EYESOURCE"
    source_dict = {}
    for i in range(nTimes):
        v_r = "EYE_Source" + str(i)
        source_dict[v_r] = circuit.modeler.components.components_catalog[name]. \
            place(inst_name=None, angle=angle, location=[start_x, start_y])
        start_y += space
    return source_dict

def insert_n_type_buffer(start_x, start_y, component, ibisMod,
                         buffer_mode, space=0.02, nTimes=1, diffN0=False, buffer_models=["DQ_FULL_ODT50_800"]):
    """Insert one or more IBIS model as inputs or outputs

    Parameters
    ----------
    start_x: float
        Offset position on the X axis.
    start_y:
        Offset position on the Y axis.
    component: Ibis object
        Circuit Component Object.
    ibisMod: Ibis object
        Circuit Component Object.
    buffer_mode: str
        Input mode = "Input Buffer"
        Output mode = "Output Buffer"
    space: float, optional
        When inserting several IBIS models, the separation between them.
    nTimes: int, optional
        The number of times you want to insert the same IBIS model
    diffN0: bool , optional
        Differential Ibis model or not


    """
    x_i = start_x
    y_i = start_y
    buffer_dict = {}
    ibisMod.selected_pin(pins=component, diffNO=diffN0)
    # when copying the same component several times,
    # do it on the Y axis
    for i in range(nTimes):
        v_r = component.short_name + str(i)
        buffer_dict[v_r] = ibisMod.add_directly_to_aedt(pins=component, x=x_i, y=y_i, diffNo=diffN0)
        y_i += space
        if buffer_mode == "Input Buffer":
            ibisMod.set_as_input_buffer(buffer_dict[v_r])
            miror_component(ibisMod.circuit(), buffer_dict[v_r])
        elif buffer_mode == "Output Buffer":
            ibisMod.set_as_output_buffer(buffer_dict[v_r])
        ibisMod.buffer_model(buffer_dict[v_r], buffer_models)
    return buffer_dict


def miror_component(circuit, component):
    """mirror circuit components"""
    # in order to have the inputs on the lef and the outputs on the right
    circuit.modeler.schematic.oeditor.FlipHorizontal(
        ["NAME:Selections", "Selections:=", [component.composed_name]
         ],
        [
            "NAME:FlipParameters",
            "Disconnect:=", True,
            "Rubberband:=", False
        ])

def create_text_box_io(oEditor,eye_probe_component, io_type, height= 0.024, name="", page_num=2):
    x_eye_component, y_eye_component = eye_probe_component.location
    print(x_eye_component)
    x_eye_component = x_eye_component.split("mil")
    x_eye_component = float(x_eye_component[0]) * 0.000025  # convert mil to meter
    y_eye_component = y_eye_component.split("mil")
    y_eye_component = float(y_eye_component[0]) * 0.000025  # convert mil to meter
    text = eye_probe_component.parameters["Name"] if not len(name) else name
    if io_type=="inputs":
        width_left = 0.05
        width_right = 0.03
    if io_type=="outputs":
        width_left = 0.01
        width_right = 0.07

    X = x_eye_component - width_left +0.015
    Y = y_eye_component + 8*height/10
    X1 = x_eye_component - width_left
    Y1 = y_eye_component + 9*height/10
    X2 = x_eye_component + width_right
    Y2 = y_eye_component - height/3

    oEditor.CreateText(
	[
		"NAME:TextData",
		"X:="			, X,
		"Y:="			, Y,
		"Size:="		, 7,
		"Angle:="		, 0,
		"Text:="		, text,
		"Color:="		, 0,
		"Id:="			, 5598,
		"ShowRect:="		, True,
		"X1:="			, X1,
		"Y1:="			, Y1,
		"X2:="			, X2,
		"Y2:="			, Y2,
		"RectLineWidth:="	, 0,
		"RectBorderColor:="	, 0,
		"RectFill:="		, 0,
		"RectColor:="		, 0
	],
	[
		"NAME:Attributes",
		"Page:="		, page_num
	])

def create_text_box(circuit,  component_type, RefDes, y_list, ports_components_list,center_location=[],
                    start_y=0,  space = 0.01, realistic_design= False, first_type_box=True):
    oEditor = circuit.modeler.oeditor
    y_port_s_param_max= max(y_list)
    y_port_s_param_min= min(y_list)
    space_y_between_ports= (max(y_list)-min(y_list))/len(y_list)
    x_s_param = center_location[0]
    width = 0.08
    space_between_sqare= 0.07
    design_mode =" <IBIS> " if realistic_design else " <No Ibis>"
    if component_type=="DriverComponents":
        X=x_s_param-0.13
        Y= ((y_port_s_param_max+y_port_s_param_min )/ 2 )+0.002+start_y
        X1= x_s_param-width-space_between_sqare
        Y1= y_port_s_param_max-0.011+ start_y
        X2= x_s_param-space_between_sqare
        Y2= y_port_s_param_min + 0.011+start_y
        angle = math.pi

    elif component_type=="ReceiverComponents":
        space = -1* space
        X = x_s_param + 0.1
        Y = ((y_port_s_param_max + y_port_s_param_min) / 2) + 0.002 +start_y
        X1 = x_s_param + space_between_sqare
        Y1 = y_port_s_param_max - 0.011 +start_y
        X2 = x_s_param + width+ space_between_sqare
        Y2 = y_port_s_param_min + 0.011 +start_y
        angle = 0
    oEditor.CreateText(
        [
            "NAME:TextData",
            "X:="			, X,
            "Y:="			, Y,
            "Size:="		, 12,
            "Angle:="		, 0,
            "Text:="		, RefDes+ " "+ design_mode,
            "Color:="		, 0,
            "Id:="			, 5598,
            "ShowRect:="		, True,
            "X1:="			, X1,
            "Y1:="			, Y1,
            "X2:="			, X2,
            "Y2:="			, Y2,
            "RectLineWidth:="	, 0,
            "RectBorderColor:="	, 0,
            "RectFill:="		, 0,
            "RectColor:="		, 0
        ],
        [
            "NAME:Attributes",
            "Page:="		, 1
        ])


    x_port = X2 if component_type=="DriverComponents" else X1
    space = 0
    i = 0
    if first_type_box:
        for port in ports_components_list:
            # x_port = x_s_param-0.07
            y_port =y_list[i]
            page_port = circuit.modeler.components.create_page_port(port, [x_port+ space,y_port], angle)
            points_array = [[x_port, y_port], [x_port+ space, y_port]]
            circuit.modeler.components.create_wire(points_array)
            i +=1
    else:
        y_port = y_port_s_param_min+ start_y
        for port in ports_components_list:
            # x_port = x_s_param - 0.07
            page_port = circuit.modeler.components.create_page_port(port, [x_port + space, y_port], angle)
            points_array = [[x_port, y_port], [x_port + space, y_port]]
            circuit.modeler.components.create_wire(points_array)
            y_port += space_y_between_ports +0.0008
            i += 1

    return Y2

class NPortsComp:
    """Manages circuit components imported from touchstone

    Parameters
    ----------
    Nets: dict
        Nets information
    extKeyword: str
        Keyword to identify the extended nets
    refDes: dict
        Names of the components, attached to the nets and
        communicating to the actual component
    path : str
            Full path to the Touchstone file.

    """

    def __init__(self, Nets, extKeyword, refDes, path, circuit):
        self._Nets = Nets
        self._refDes = refDes
        self._path = path
        self._circuit = circuit
        self._components = None
        self._ext_keyword = extKeyword

    def insert_get_from_touchstone(self, model_name=None, location=[], angle=0):
        """Insert a component from a Touchstone model.

        Parameters
        ----------
        model_name : str, optional
            Name of the model. The default is ``None``.
        location : list of float, optional
            Position on the X  and Y axis.
        angle : float, optional
            Angle rotation in degrees. The default is ``0``.
        Returns
        -------
        :class:`pyaedt.modeler.Object3d.CircuitComponent`
            Circuit Component Object.
        """
        model = self._circuit.modeler.components.create_model_from_touchstone \
            (touchstone_full_path=self._path, model_name=model_name)
        self._components = self._circuit.modeler.components.create_touchsthone_component \
            (model_name=model, location=location, angle=angle)
        return self._components

    def components_pins_info(self):
        """Get the s-parameters component pins real name

        Returns
        -------
        portinfo: dict
            dictionary

        Example:
        CompInst@PCIE_Express 1X_GS[0]=PCIE0_RX0_N_J2L1_23
        """
        portinfo = {}
        for i in range(0, len(self._components.pins)):
            portinfo[self._components.pins[i].name] = i
            # print(f'{self._components.name}[{i}]={self._components.pins[i].name}')
        return portinfo

    def identify_in_out_ports(self):
        """ Identify the inputs and outputs pins/ports
        of the component

        Returns
        -------
        io_port_dict: dict
            dictionary

        """
        # Consider all the extended nets as single ended ones
        # and the extended differentials  as simply differentials
        # and each nets within the extended differentials as single ended
        ports_info = self.components_pins_info()
        io_port_dict = {}
        ports_dict = {}
        for nettype in self._Nets.keys():
            if nettype == "Differential" and self._Nets[nettype]:
                for componentype in self._refDes.keys():
                    if componentype == "DriverComponents":
                        ports_dict["inputs"] = self.diff_NegPos_ports(self._Nets[nettype], self._refDes[componentype],
                                                                      ports_info)
                    elif componentype == "ReceiverComponents":
                        ports_dict["outputs"] = self.diff_NegPos_ports(self._Nets[nettype], self._refDes[componentype],
                                                                       ports_info)
            elif nettype == "SingleEnded":
                for componentype in self._refDes.keys() and self._Nets[nettype]:
                    if componentype == "DriverComponents":
                        ports_dict["inputs"] = self.signleEnd_NegPos_ports(self._Nets[nettype],
                                                                           self._refDes[componentype], ports_info)
                    elif componentype == "ReceiverComponents":
                        ports_dict["outputs"] = self.signleEnd_NegPos_ports(self._Nets[nettype],
                                                                            self._refDes[componentype], ports_info)
            if self._Nets[nettype] and nettype != "Extended":
                io_port_dict[nettype] = ports_dict

        return io_port_dict

    def diff_NegPos_ports(self, diff_nets, refDes, ports):
        """Identify the inputs and outputs port for differential pairs

        Parameters
        ----------
        diff_nets: dict
            differential nets
        refDes: str
            component type
        ports: dict
            ports/pins name and position extracted from component

        Returns
        -------
        dict

        """

        diffportdict = {}
        for diffnet in diff_nets.keys():
            diffportdict[diffnet] = self.signleEnd_NegPos_ports(diff_nets[diffnet], refDes, ports)
        return diffportdict

    def signleEnd_NegPos_ports(self, SEnets, refDes, ports):
        """Identify the inputs and outputs port for single ended nets

        Parameters
        ----------
        SEnets: list of str
            single ended nets
        refDes: str
            component type
        ports: dict
            ports/pins name and position extracted from component

        Returns
        -------
        se_portdict: dict

        """
        se_portdict = {}
        for sen in SEnets:
            # all the extended nets will have an added keyword
            # to identify them
            if re.findall(self._ext_keyword + r"$", sen):
                # each nets within the extended will be considered as single ended ones
                se_portdict[sen] = self.signleEnd_NegPos_ports(self._Nets["Extended"][sen], refDes, ports)
            else:
                portlist = []
                for port in ports.keys():
                    # 1- make sure that there is at least one name found
                    # 2- Example: an input port for a net is the name of the port,
                    # of the component, which contains the name of the driver component and
                    # the net name
                    if re.findall(".*" + sen + ".*", port) == re.findall(".*" + refDes + ".*", port) and \
                            re.findall(".*" + sen + ".*", port):
                        portlist.append(port)
                        # everytime an element is found, delete it from the port dictionary, like this
                        # there will be no repetition
                        del ports[port]
                        break
                # add element on the dictionary, if only a port name has been found
                if portlist:
                    se_portdict[sen] = portlist[0]
        return se_portdict

    def extended_NegPos_ports(self, extended_nets, refDes, ports):
        """Identify the inputs and outputs port for an extended net

        Parameters
        ----------
        extended_nets: dict
            extended nets
        refDes: str
            component type
        ports: dict
            ports/pins name and position extracted from component

        Returns
        -------
        dict

        """

        # the extended nets can be considered as differential ones because of the way they are
        # represented in the previous code,even if there are 4 pieces of an extended net
        # that connect two components,
        # we will consider only the two that are directly connected to these components
        return self.diff_NegPos_ports(extended_nets, refDes, ports)

    def count_nets(self):
        diff_nets = 0
        se_nets = 0
        for key_type in self._Nets.keys():
            if self._Nets[key_type]:
                if key_type == "Differential":
                    diff_nets = len(self._Nets[key_type])
                elif key_type == "SingleEnded":
                    se_nets = len(self._Nets[key_type])
        return se_nets, diff_nets
