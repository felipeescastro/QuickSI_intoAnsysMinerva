from pyaedt.generic.process import SiwaveSolve
from pyaedt import Edb
import subprocess
import tempfile
import shutil
import json
import sys
import os
import re

app_data_path = os.environ["APPDATA"]
env_pyaedt = os.path.join(app_data_path, "pyaedt_env_ide")

def set_freq_sweep(edb,imported_json_s_param):
    """Add a SIwave SYZ analysis.

    Parameters
    ----------
    edb :
    imported_json_s_param :

    Returns
    -------
    bool
        ``True`` when successful, ``False`` when failed.
    """
    freq_sweep_dict = imported_json_s_param["Freq Sweep"]
    process = SiwaveSolve(edb.edbpath, edb.edbversion)
    exec_file = os.path.splitext(process._project_path)[0] + ".exec"
    if os.path.exists(exec_file):
        temp_exec = open('temp.exec', 'w')
        types = list(freq_sweep_dict.keys())

        temp_exec.write("SetSIwaveSyzSimName " + imported_json_s_param["sweep_name"] + "\n")
        cmpt_dcpt = "True" if imported_json_s_param["cmpt_dcpt"]=="True" else "False"
        temp_exec.write("ComputeExactDcPt " + cmpt_dcpt + "\n")

        temp_exec.write("SetSwp " + str(freq_sweep_dict[types[0]][0]) + " " + freq_sweep_dict[types[0]][1] + " " +
                        freq_sweep_dict[types[0]][2] + " " + types[0] + "\n")
        if len(freq_sweep_dict.keys()) > 1:
            for i in range(1, len(freq_sweep_dict.keys())):
                temp_exec.write(
                    "AddSwp " + str(freq_sweep_dict[types[i]][0]) + " " + freq_sweep_dict[types[i]][1] + " " +
                    freq_sweep_dict[types[i]][2] + " " + types[i] + "\n")
        if imported_json_s_param["discret_sweep"] == "True":
            temp_exec.write("SetDiscreteSwp " + "\n")
        else:
            temp_exec.write("SetInterpSwp " + "\n")
        causality = "True" if imported_json_s_param["Enforce_causality"]=="True" else "False"
        passivity = "True" if imported_json_s_param["Enforce_passivity"]=="True" else "False"
        temp_exec.write("SIwaveSyzEnforceCausality " + causality + "\n")
        temp_exec.write("SIwaveSyzEnforcePassivity " + passivity + "\n")
        temp_exec.write("ExportTouchstone " + project_path + "\n")

        exec_file = os.path.splitext(process._project_path)[0] + ".exec"
        temp_exec.close()
        prepend_lines(exec_file, 'temp.exec')

    return True

def prepend_lines(file_name, from_file):
    """ Insert given string as a new line at the beginning of a file """
    # define name of temporary dummy file
    dummy_file = 'dummy.exec'
    # open original file in read mode and dummy file in write mode
    with open(file_name, 'r') as read_obj, open(dummy_file, 'w') as write_obj, open(from_file, 'r') as read_from:
        # Write given line to the dummy file
        for line in read_from:
            write_obj.write(line)
        # Read lines from original file one by one and append them to the dummy file
        for line in read_obj:
            write_obj.write(line)
    # remove original file
    os.remove(file_name)
    os.remove(from_file)
    # Rename dummy file as the original file
    os.rename(dummy_file, file_name)

def save_as_siw(edb):
    # supporting non graphical solve only
    process = SiwaveSolve(edb.edbpath, edb.edbversion)
    edb.core_siwave.create_exec_file()

    if SiwaveSolve.nongraphical:
        if os.name == "posix":
            exe_path = os.path.join(process.installer_path, "siwave_ng")
        else:
            exe_path = os.path.join(process.installer_path, "siwave_ng.exe")
        exec_file = os.path.splitext(process._project_path)[0] + ".exec"
        if os.path.exists(exec_file):
            with open(exec_file, "r+") as f:
                f.writelines("SaveSiw")
            command = [exe_path]
            command.append(process._project_path)
            command.append(exec_file)
            command.append("-formatOutput")
            command.append("-useSubdir")
            print(command)
            p = subprocess.Popen(command)
            p.wait()
            # os.remove(exec_file)
            # p.wait()
    return os.path.splitext(process._project_path)[0] + ".siw"


args = sys.argv
environs = os.environ
environs = list(environs.keys())
env_EM_start = "ANSYSEM_ROOT"
ansys_em_roots =[]

# Find the last ANSYS EM version installed in local PC
for env in environs:
    if env_EM_start == env[:(len(env_EM_start))]:
        ansys_em_roots.append(env)
last_version_root = ansys_em_roots[len(ansys_em_roots)-1]
v = last_version_root[-3:]
version_in_dot_format = "20" + v[:2] + "." + v[2]

# Check that there are at least 3 or 4  arguments to perform the simulations
# if not, quit/exit() the terminal and try again
if len(args) in [3, 4]:
    json_path = os.path.abspath(args[1])
    board_path = os.path.abspath(args[2])
    default_project_path, project_siw = os.path.split(board_path)
    default_project_path = os.path.join(default_project_path,"Results")
    project_path = default_project_path
    project_name = project_siw.replace(".aedb", '')
    if len(args) == 4:
        project_path = os.path.abspath(args[3])

# else:
#     print("The number of arguments does not match")
#     sys.exit()


if not os.path.exists(project_path):
    os.makedirs(project_path)

j_file = open(json_path, "r")
jsonFile = json.load(j_file)
j_file.close()

if not os.path.exists(os.path.join(project_path, project_name + ".aedb")):
    os.makedirs(os.path.join(project_path, project_name + ".aedb"))
    shutil.copyfile(os.path.join(board_path, "edb.def"), os.path.join(project_path, project_name + ".aedb", "edb.def"))
new_edb_path = os.path.join(project_path, project_name + ".aedb")

edb0 = Edb(edbpath=new_edb_path, edbversion=version_in_dot_format)
siw_path = save_as_siw(edb0)
core_nets= edb0.core_nets
core_padstack = edb0.core_padstack
edb0.save_edb()

si_wave_input = {}
if "S-parameters" in jsonFile.keys() and jsonFile["S-parameters"]:
    s_parameters_input = jsonFile["S-parameters"]
    command = [os.path.join(env_pyaedt, "Scripts", "python.exe")]
    command.append(".\\nets_manager\\net_manager.py")
    command.append(json_path)
    command.append(new_edb_path)
    command.append(version_in_dot_format)
    p = subprocess.Popen(command)
    p.wait()
    j_file = open(".\\nets_sorted.json", "r")
    net_file = json.load(j_file)
    j_file.close()
    # os.remove("nets_manager/nets_sorted.json")
    count_ports = 0
    # edb1 = Edb(edbpath=new_edb_path, edbversion=Version)
    for net in net_file["Signal Nets"]:
        for comp in net_file["Components"]:
            if edb0.core_nets.is_net_in_component(comp, net):
                count_ports += 1
                pin_name = edb0.core_padstack.get_pinlist_from_component_and_net(comp, net)
                port_name = net + '_' + comp + '_' + pin_name[0].GetName()
                edb0.core_siwave.create_circuit_port_on_net(positive_component_name=comp,
                                                           positive_net_name=net, port_name=port_name)

    edb0.save_edb()
    edb0.core_siwave.add_siwave_syz_analysis()
    set_freq_sweep(edb0, s_parameters_input)
    edb0.solve_siwave()
edb0.close_edb()

if "Sim Scan" in jsonFile.keys() and jsonFile["Sim Scan"]:
    zo_xt_script_path = ".\\z0_xt_scan\\Z0XTscan.py"
    si_wave_input = jsonFile["Sim Scan"]
    command = [os.path.join(env_pyaedt, "Scripts", "python.exe")]
    command.append(zo_xt_script_path)
    command.append(json_path)
    command.append(siw_path)
    command.append(os.path.join(project_path, "Z0_XT_scan"))
    print(command)
    p = subprocess.Popen(command)
    p.wait()


j_file = open(".\\nets_sorted.json", "r")
net_file = json.load(j_file)
j_file.close()

s_parameters_input = jsonFile["S-parameters"]
print(" AEDT ANALYSIS :")
if "AEDT" in jsonFile.keys() and jsonFile["AEDT"]:
    aedt_input = {}
    temp_comp ={}
    temp_comp["Components"] =s_parameters_input["Components"]
    del net_file["Signal Nets"]
    del net_file["Components"]
    aedt_input["AEDT"]= jsonFile["AEDT"].copy()
    aedt_input["AEDT"].update(net_file)
    aedt_input["AEDT"].update(temp_comp)
    aedt_input_json_path= ("aedt_input_json.json")
    aedt_file = open(aedt_input_json_path,"w")
    aedt_input_json= json.dump(aedt_input, aedt_file, indent=2)
    aedt_file.close()
    command = [os.path.join(env_pyaedt, "Scripts", "python.exe")]
    command.append(".\\aedt_analysis\\edt_analysis.py")
    command.append(aedt_input_json_path)
    command.append(os.path.join(project_path,project_name+".s"+str(count_ports)+"p"))
    command.append(project_path)
    p = subprocess.Popen(command)
    p.wait()

# os.remove("nets_sorted.json")
# os.remove("aedt_input_json.json")