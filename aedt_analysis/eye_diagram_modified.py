from pyaedt.generic.general_methods import generate_unique_name
from pyaedt.generic.general_methods import pyaedt_function_handler
from pyaedt.modules.report_templates import CommonReport


class EyeDiagramMod(CommonReport):
    """Eye Diagram Report Class."""

    def __init__(self, app, report_type, setup_name):
        CommonReport.__init__(self, app, report_type, setup_name)
        self.domain = "Time"
        self.time_start = "0fs"
        self.time_stop = "200ns"
        self.unit_interval = "1e-09s"
        self.offset = "0ms"
        self.auto_delay = True
        self.manual_delay = "0ps"
        self.auto_cross_amplitude = True
        self.cross_amplitude = "0mV"
        self.auto_compute_eye_meas = True
        self.eye_meas_pont = "5e-10s"
        self.thinning = False
        self.dy_dx_tolerance = 0.001
        self.thinning_points = 500000000

        #add by wendjel
        self.component_class = None
        self.int_id = None

    @pyaedt_function_handler()
    def assign_eye_ids(self, component_class, int_id):  ###### modified by wendjel
        self.component_class = component_class
        self.int_id = int_id
    @property
    def _context(self):  ###### modified by wendjel

        if self.thinning:
            val = "1"
        else:
            val = "0"
        arg = [
            "NAME:Context",
            "SimValueContext:=",
            [
                1,
                0,
                2,
                0,
                False,
                False,
                -1,
                1,
                0,
                1,
                1,
                "",
                0,
                0,
                "DE",
                False,
                val,
                "DP",
                False,
                str(self.thinning_points),
                "DT",
                False,
                str(self.dy_dx_tolerance),
                "NUMLEVELS",
                False,
                "1",
                ##### add by wendjel
                "PCID",
                False,
                str(self.component_class.id),
                "PID",
                False,
                str(self.int_id),
                ###
                "WE",
                False,
                self.time_stop,
                "WM",
                False,
                "200ns",
                "WN",
                False,
                "0ps",
                "WS",
                False,
                self.time_start,
            ],
        ]
        return arg

    @property
    def _trace_info(self):
        if isinstance(self.expressions, list):
            return ["Component:=", self.expressions]
        else:
            return ["Component:=", [self.expressions]]

    @pyaedt_function_handler()
    def create(self, plot_name=None, component_class=None, int_id=None):
        """Create a new Eye Diagram Report.

        Parameters
        ----------
        plot_name : str, optional
            Optional Plot name.

        Returns
        -------
        bool
        """
        self.assign_eye_ids(component_class, int_id)

        if not plot_name:
            if self._is_created:
                self.plot_name = generate_unique_name("Plot")
        else:
            self.plot_name = plot_name

        self._post.oreportsetup.CreateReport(
            self.plot_name,
            self.report_category,
            self.report_type,
            self.setup,
            self._context,
            self._convert_dict_to_report_sel(self.variations),
            self._trace_info,
            [
                "Unit Interval:=",
                self.unit_interval,
                "Offset:=",
                self.offset,
                "Auto Delay:=",
                self.auto_delay,
                "Manual Delay:=",
                self.manual_delay,
                "AutoCompCrossAmplitude:=",
                self.auto_cross_amplitude,
                "CrossingAmplitude:=",
                self.cross_amplitude,
                "AutoCompEyeMeasurementPoint:=",
                self.auto_compute_eye_meas,
                "EyeMeasurementPoint:=",
                self.eye_meas_pont,
            ],
        )
        self._post.plots.append(self)
        self._is_created = True
        return True
