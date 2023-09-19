import pyaedt
from pyaedt.generic import ibis_reader


def io_diff_list():
    """ Register positive pin name list in a class variable """

    if IbisInsertPinExt.diff_dict:
        buf = list(IbisInsertPinExt.diff_dict.values())
        IbisInsertPinExt.io_diff_lst.append(buf[0][0])
    return IbisInsertPinExt.io_diff_lst


class IbisInsertPinExt:
    inserted_diff_list = []
    diff_dict = {}
    io_diff_lst = []
    inv_io_diff_lst = []

    def __init__(self, ibis, circuit, filename):
        self.ibis = ibis
        self._circuit = circuit
        self._filename = filename

    def circuit(self):
        return self._circuit

    def assign_diff_list(self, value_list):
        """ Assign inserted diff list using a method"""

        IbisInsertPinExt.inserted_diff_list.clear()
        IbisInsertPinExt.inserted_diff_list += value_list

    def diff_pin_selected(self):
        """ Save differential pin info in dictionary """

        if len(IbisInsertPinExt.inserted_diff_list) == 3:
            componentName = IbisInsertPinExt.inserted_diff_list[0]
            extension = "_" + componentName + "_" + self.ibis.name
            IbisInsertPinExt.diff_dict[IbisInsertPinExt.inserted_diff_list[0]] = \
                [IbisInsertPinExt.inserted_diff_list[1] + extension, IbisInsertPinExt.inserted_diff_list[2] + extension]

    def display_diff_dict(self):
        print(IbisInsertPinExt.diff_dict)

    def inv_io_diff_list(self):
        """ Register negative pin name list in a class variable """

        if IbisInsertPinExt.diff_dict:
            buf = list(IbisInsertPinExt.diff_dict.values())
            IbisInsertPinExt.inv_io_diff_lst.append(buf[0][1])
        return IbisInsertPinExt.inv_io_diff_lst

    def import_model_from_file(self):
        """Import from file IBIS info"""

        self.diff_pin_selected()
        args = [
            "NAME:Options",
            "Mode:=",
            4,
            "Overwrite:=",
            False,
            "SupportsSimModels:=",
            False,
            "LoadOnly:=",
            False,
        ]

        arg_buffers = ["NAME:Buffers"]
        for buffer in self.ibis.buffers.keys():
            arg_buffers.append("{}:=".format(self.ibis.buffers[buffer].short_name))
            arg_buffers.append([True, "IbisSingleEnded"])

        arg_components = ["NAME:Components"]
        for component in self.ibis.components.keys():
            arg_component = ["NAME:{}".format(self.ibis.components[component].name)]
            for pin in self.ibis.components[component].pins.keys():
                if pin in io_diff_list():
                    arg_component.append("{}:=".format(self.ibis.components[component].pins[pin].short_name))
                    arg_component.append([True, False])
                    arg_component.append("{}:=".format(self.ibis.components[component].pins[pin].short_name))
                    arg_component.append([True, True])
                elif pin in self.inv_io_diff_list():
                    arg_component.append("{}:=".format(self.ibis.components[component].pins[pin].short_name))
                    arg_component.append([True, True])
                else:
                    arg_component.append("{}:=".format(self.ibis.components[component].pins[pin].short_name))
                    arg_component.append([True, False])
            arg_components.append(arg_component)

        args.append(arg_buffers)
        args.append(arg_components)

        self._circuit.modeler.schematic.o_component_manager.ImportModelsFromFile(self._filename, args)

    def selected_pin(self, pins, diffNO=False):
        """Add a pin to the list of components in the Project Manager."""
        self.import_model_from_file()
        if diffNO:
            diffornot = '_diff'
        else:
            diffornot = ''

        self._circuit.modeler.schematic.o_component_manager.AddSolverOnDemandModel(
            pins.name.replace(pins.short_name, pins.signal) + diffornot,
            [
                "NAME:CosimDefinition",
                "CosimulatorType:=",
                7,
                "CosimDefName:=",
                "DefaultIBISNetlist",
                "IsDefinition:=",
                True,
                "Connect:=",
                True,
                "Data:=",
                [],
                "GRef:=",
                [],
            ],
        )

    def add_directly_to_aedt(self, pins, x, y, angle=0.0, diffNo=False):
        """Insert a pin at a defined location inside the graphical window.

            Parameters
            ----------
            diffNo : bool
                differential pair or not
            x : float
                X position of the pin.
            y : float
                Y position of the pin.
            angle : float, optional
                Angle of the pin. The default value is ``"0.0"``.

            Returns
            -------
            :class:`pyaedt.modeler.Object3d.CircuitComponent`
                Circuit Component Object.

            """

        if diffNo:
            diffornot = '_diff'
        else:
            diffornot = ''

        return self._circuit.modeler.schematic.create_component(
            component_library=None,
            component_name=pins.name.replace(pins.short_name, pins.signal) + diffornot,
            location=[x, y],
            angle=angle,
        )

    def pin_import_edt(self, componentName, PinShortame, x, y, angle=0.0, diffNo=False):
        self.add_directly_to_aedt \
            (pins=self.ibis.components[componentName].pins[PinShortame],
             x=x, y=y, angle=angle, diffNo=diffNo)

    def change_property(self, tabname, Component, vPropChange):
        """Modify a property.

        Parameters
        ----------
        tabname : str
                property tab name

        vPropChange : list
                specific property to change

        Component :  `pyaedt.modeler.Object3d.CircuitComponent`
                 Circuit Component Object.
        """

        vChangedProps = ["NAME:ChangedProps", vPropChange]
        vPropServers = ["NAME:PropServers", Component.composed_name]
        vGeo3dlayout = ["NAME:" + tabname, vPropServers, vChangedProps]
        vOut = ["NAME:AllTabs", vGeo3dlayout]
        self._circuit.modeler.schematic.oeditor.ChangeProperty(vOut)

    def set_as_input_buffer(self, component):
        """ Set ibis component as an input buffer

        Parameters
        ----------
        component:  `pyaedt.modeler.Object3d.CircuitComponent`
                 Circuit Component Object.

        """

        tabname = "Buffer_Pin"
        arg =self.arg_for_property( "buffer_mode", "Input Buffer")
        self.change_property(tabname, component, arg)

    def set_as_output_buffer(self, component):
        """ Set ibis component as an output buffer

        Parameters
        ----------
        component:  `pyaedt.modeler.Object3d.CircuitComponent`
                 Circuit Component Object.

        """
        arg =self.arg_for_property( "buffer_mode", "Output Buffer")
        tabname ="Buffer_Pin"
        self.change_property(tabname, component, arg)

    def excitation_port(self, component, portname):
        """ Definition of the excitation port for the output buffer

        Parameters
        ----------
        component:  `pyaedt.modeler.Object3d.CircuitComponent`
                 Circuit Component Object.
        portname : str
                 Name of the port

        """
        arg = self.arg_for_property( "logic_in", portname)
        tabname = "Buffer_Pin"
        self.change_property(tabname, component, arg)

    def buffer_model(self, component, models=[]):
        """ Define a model for each pin

        Parameters
        ----------
        component : `pyaedt.modeler.Object3d.CircuitComponent`
                 Circuit Component Object.
        models : list
                list of model name to be defined for the pin(s)

        """
        tabname = "Buffer_Pin"
        i = 1
        if models:
            for j in models:
                arg = [
                    "NAME:Model" + str(i),
                    "OverridingDef:=", True,
                    "Value:=", "\"" + str(j) + "\"",
                    "HasPin:=", False,
                    "ShowPin:=", False,
                    "Display:=", False,
                    "Sweep:="	, False,
                    "DefaultOutput:="	, False,
                    "SDB:="			, False
                ]
                i += 1
                self.change_property(tabname, component, arg)
        else:
            print("No model defined")

########
    def arg_for_property(self, Name, Ibistext):
        return [
            "NAME:"+Name,
            "OverridingDef:=", True,
            "IbisText:=", Ibistext,
            ""
        ]