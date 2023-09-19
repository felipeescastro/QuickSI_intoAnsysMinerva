
import tempfile
import os
import subprocess
import shutil
import json
import sys
import re
from lxml import etree
from pyaedt import Edb
from functions import *


default_Version = '2022.2'
version_list = {
    "2022.2": "ANSYSEM_ROOT222",
    "2022.1": "ANSYSEM_ROOT221",
    "2021.1": "ANSYSEM_ROOT211",
    "2021.2": "ANSYSEM_ROOT212"
}
default_values = {
    "NominalZ0": "50",
    "WarningThreshold": "10",
    "ViolationThreshold": "20",
    "FEXTWarningThreshold": "7",
    "FEXTViolationThreshold": "17",
    "NEXTWarningThreshold": "7",
    "NEXTViolationThreshold": "17",
    "DriverRiseTime": "10ps",
    "Voltage": "1V",
    "DriverImpedance": "50.0ohm",
    "TerminationImpedance": "50.0ohm",
    "MinTlineSegmentLength": "0.3mm",
    "Z0Frequency": "1e9Hz"
}
version_format = '\d{4}[.]\d{1}'
args = sys.argv

# Check that there are at least 3 or 4 or 5 arguments to perform the simulations
# if not, quit/exit() the terminal and try again
if len(args) in [3, 4, 5]:
    json_path = os.path.abspath(args[1])
    board_path = os.path.abspath(args[2])
    default_project_path, project_siw = os.path.split(board_path)
    default_project_path = os.path.join(default_project_path,"SIwave_Results")
    project_path = default_project_path

    project_name = project_siw.replace(".siw", '')
    Version = default_Version
    if len(args) == 5:
        project_path = os.path.abspath(args[4])
        Version = args[3]
    # In case of 4 arguments, the 4th can be considered as the project path or the version
    elif len(args) == 4:
        Version = args[3]
else:
    print("The number of arguments does not match")
    sys.exit()


'''
    #DIRECTORY
'''
json_path="example.json"
## Open json file
j_file = open(json_path, "r")
jsonFile = json.load(j_file)
j_file.close()
# Make sure the first dictionary/keys in the .json file is "Sim Scan" (with space).
# It was done so that you can do different types of simulations
# in a single script with only one .json file
dictFromJsonNotModified = jsonFile["Sim Scan"]
dictFromJson = dictFromJsonNotModified

## Temporary directory
# The temporary path depends on the PC Used
# Check if one is well created in your environment variables
temp_folder = tempfile.gettempdir()
temp_folder = os.path.join(temp_folder, 'AnsysPyXml-Z0XTscan', project_name)
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

## Install path
if Version in version_list.keys():
    # Make sure the Ansys Environment Variables are well-defined
    # in your system properties with the same Names
    AnsysEnviron = version_list[Version]
    installPath = os.environ[AnsysEnviron]
siwave_path = os.path.join(installPath, 'siwave.exe')
siwave_ng_path = os.path.join(installPath, 'siwave_ng.exe')

#### CREATE EDB FROM SIW
edbpath = os.path.join(temp_folder, project_name + '.aedb')
# create a temporary script to export a .aedb file from the .siw
create_edb = open(os.path.join(temp_folder, "script_create_edb.py"), "w")
create_edb.write('edbfilepath =r"' + edbpath +
                 '"\noDoc.ScrExportEDB(edbfilepath)')
create_edb.close()
# Open SIwave run the previous script and exit
command = [siwave_path, board_path,'-runscriptandexit', os.path.join(temp_folder, "script_create_edb.py")]

subprocess.run(command)
edb = Edb(edbpath=edbpath, edbversion=Version)

# in case the file path already exist use the same file to run the simulations
if not os.path.exists(project_path):
    os.makedirs(project_path)

report_file = os.path.join(project_path, "verification-report.log")
log = create_logger(report_file)
display('Project Name                  : ' + project_name, log)
display('*.json File Location          : ' + json_path, log)
display('Loaded *.siw File Location    : ' + board_path, log)
display('Siwave Version                : ' + Version, log)
display('Project File Location         : ' + project_path + '\n', log)

# copy *.siw in the designed project path location
if not os.path.exists(os.path.join(temp_folder, project_name + '.siw')):
    shutil.copyfile(board_path, os.path.join(project_path, project_name + '.siw'))
board_path = os.path.join(temp_folder, os.path.join(project_path, project_name + '.siw'))

### Power nets Verifation
# Power nets name extracted from Edb
powerNets = edb.core_nets.power_nets.keys()

# Make sure that there is at least one power Reference defined
# otherwise quit/exit() the terminal
if powerNets:
    toPrint1 = "\nPOWER REFERENCE WELL DEFINED\n-----> Start Analysis\n"
    print(toPrint1)
else:
    toPrint1 = "NO POWER REFERENCE  DEFINED\n-----> STOP ANALYSIS\n" \
               "Identify the power nets in PCB before trying again"
    print(command)
    print(toPrint1)
    sys.exit()
display(toPrint1, log)

# Signal nets name extracted from Edb
NetsInEdb = edb.core_nets.signal_nets.keys()

'''
    #ZO IMPEDANCE SCAN
'''

create_html = False  # create Html report file, only if there's an impedance scan performed

# At this step, the amount of arguments and the power nets are already verified
# Perform Impedance scan simulation if the keys "Z0scan" exist in .json file
if "Z0scan" in dictFromJson.keys():
    display("\n\nIMPEDANCE SCAN: ", log)
    display("-----> Start Verifications", log)
    extractedNetsName = extract_netsNames(dictFromJson, sim_name="Z0scan")
    # For the nets verification, it is necessary to classify the nets in two categories:
    # 1- (To check) If the full name of the net is given, check its existence in Edb
    # 2- (To list) If a part of the net name is given,
    #       find at least one net that contains the sequence(name part) you are looking for
    NetsTolist, NetsTocheck = classify_nets(extractedNetsName)
    verify1 = check_nets(NetsTocheck=NetsTocheck, NetsTolist=NetsTolist,
                         NetsInEdb=NetsInEdb, logger=log)
    verify2 = list_nets(NetsTocheck=NetsTocheck, NetsTolist=NetsTolist,
                        NetsInEdb=NetsInEdb, logger=log)
    print(f"Check: {verify1} list: {verify2}")

    # all nets, in the case of the nets to be checked, must exist in edb and
    # at least one net must be found for each part of the given name.
    if verify1 and verify2:
        display("-----> Start Analysis", log)
        zo_xml_file = open(os.path.join(temp_folder, "si_wave_zo_scan.xml"), "w")
        zo_exec_file = open(os.path.join(temp_folder, "zo_scan.exec"), "w")

        si_scan_config = etree.Element("SIwaveScanConfig")
        zo_scan = etree.SubElement(si_scan_config, "Z0ScanConfig")
        zo_scan.set("MinTlineSegmentLength",
                    dictFromJson["Z0scan"]["Parameters"]["MinTlineSegmentLength"])
        zo_scan.set("Z0Frequency",
                    dictFromJson["Z0scan"]["Parameters"]["Z0Frequency"])

        Nets_type = ["SingleEndedNets", "DifferentialNets",
                     "ExtendedNets", "ExtendedDifferentialNets"]
        for type_n in Nets_type:
            if type_n in dictFromJson["Z0scan"].keys():
                single_end = etree.SubElement(zo_scan, type_n)
                i = 0
                single = dictFromJson["Z0scan"][type_n]
                # the nets are in a list format in the nets type key
                # so each Net informations is indexed in the .json fil
                for i in range(0, len(single)):
                    net_name = etree.SubElement(single_end, "Net")
                    net_name.set("Name", single[i]["Name"])
                    defined_param("NominalZ0", net_name, single[i], default_values)
                    defined_param("WarningThreshold", net_name, single[i], default_values)
                    defined_param("ViolationThreshold", net_name, single[i], default_values)
                    i += 1

        zo_exec_file.write("ExecZ0Sim \n"
                           "CrosstalkScanConfigFile "
                           + os.path.join(temp_folder, "si_wave_zo_scan.xml") +
                           "\nSetNumCpus 4 \nSetZ0ScanSimName "
                           + dictFromJsonNotModified["Z0scan"]["Parameters"]["ScanName"])
        zo_xml_file.write(etree.tostring(element_or_tree=si_scan_config,
                                         encoding="unicode", pretty_print=True))
        zo_xml_file.close()
        zo_exec_file.close()

        # command line to perform the impedance scan
        command = [siwave_ng_path, board_path, os.path.join(temp_folder, "zo_scan.exec"),
                   "-formatOutput", "-useSubdir"]
        subprocess.run(command)
        create_html = True
        display("-----> Impendance Scan: Analysis Finished", log)

'''
    #XT SCAN FREQUENCY DOMAIN
'''

# Perform Impedance scan simulation if the keys "XTFD scan" exist in .json file
if "XTFD scan" in dictFromJson.keys():
    display("\n\nCROSSTALK SCAN [FREQUENCY DOMAIN]: ",log)
    display("-----> Start Verifications", log)
    extractedNetsNames=extract_netsNames(dictFromJson, sim_name="XTFD scan")
    # For the verification of nets it is necessary to classify the nets in two categories:
    # 1- (To check) If the full name of the net is given, check its existence in Edb
    # 2- (To list) If a part of the net name is given,
    #       find at least one net that contains the sequence(name part) you are looking for
    NetsTolist, NetsTocheck= classify_nets(extractedNetsNames)

    verify1 = check_nets(NetsTocheck=NetsTocheck, NetsTolist=NetsTolist, NetsInEdb= NetsInEdb,logger=log)
    verify2 = list_nets(NetsTocheck=NetsTocheck, NetsTolist=NetsTolist,NetsInEdb=NetsInEdb,logger=log)
    print(f"Check: {verify1} list: {verify2}")
    # all nets, in the case of the nets to be checked, must exist in edb and
    # at least one net must be found for each part of the given name.
    if verify1 and verify2 :
        display("-----> Start Analysis", log)
        fdxt_xml_file= open(os.path.join(temp_folder,"si_wave_fdxt_scan.xml"),"w")
        fdxt_exec_file= open(os.path.join(temp_folder,"fdxt_scan.exec"),"w")

        si_scan_config = etree.Element("SIwaveScanConfig")
        fdxt_scan = etree.SubElement(si_scan_config, "FdXtalkConfig")
        fdxt_scan.set("MinTlineSegmentLength",
                      dictFromJson["XTFD scan"]["Parameters"]["MinTlineSegmentLength"])
        fdxt_scan.set("XtalkFrequency",
                      dictFromJson["XTFD scan"]["Parameters"]["Z0Frequency"])

        Nets_type = ["SingleEndedNets", "DifferentialNets",
                     "ExtendedNets", "ExtendedDifferentialNets"]
        for type_n in Nets_type:
            if type_n in dictFromJson["XTFD scan"].keys():
                single_end = etree.SubElement(fdxt_scan, type_n)
                i = 0
                single = dictFromJson["XTFD scan"][type_n]
                # the nets are in a list format in the nets type key
                # so each Net informations is indexed in the .json fil
                for i in range(0, len(single)):
                    net_name = etree.SubElement(single_end, "Net")
                    net_name.set("Name", single[i]["Name"])
                    defined_param("FEXTWarningThreshold", net_name, single[i], default_values)
                    defined_param("FEXTViolationThreshold", net_name, single[i], default_values)
                    defined_param("NEXTWarningThreshold", net_name, single[i], default_values)
                    defined_param("NEXTViolationThreshold", net_name, single[i], default_values)
                    i += 1


        fdxt_exec_file.write("ExecCrosstalkSim \n"
                           "CrosstalkScanConfigFile "
                           +os.path.join(temp_folder,"si_wave_fdxt_scan.xml") +
                           "\nSetNumCpus 4\n"
                           "SetFdXtalkScanSimName "+dictFromJsonNotModified["XTFD scan"]["Parameters"]["ScanName"])


        fdxt_xml_file.write(etree.tostring(element_or_tree= si_scan_config,
                                           encoding="unicode",pretty_print=True))
        fdxt_xml_file.close()
        fdxt_exec_file.close()

        command = [siwave_ng_path, board_path, os.path.join(temp_folder, "fdxt_scan.exec"),
                  "-formatOutput", "-useSubdir"]
        subprocess.run(command)
        display("-----> Crosstalk Scan(Frequency Domain): Analysis Finished", log)


'''
    #XT SCAN TIME DOMAIN
'''

# Perform Impedance scan simulation if the keys "XTTD scan" exist in .json file
if "XTTD scan" in dictFromJson.keys():
    display("\n\nCROSSTALK SCAN [TIME DOMAIN]: ", log)
    display("-----> Start Verifications", log)
    extractedNetsNames = extract_netsNames(dictFromJson, sim_name="XTTD scan")
    NetsTolist, NetsTocheck = classify_nets(extractedNetsNames)

    # if there is a regular expression in the net name list extracted,
    # make sure to create a new dictionary with their full name to facilitate the extraction of pins name
    if NetsTolist:
        NetsListed = list_nets_tdx(NetsTolist, edb=edb)
        dictFromJson = reshape_imported_json(imported_json=dictFromJson, Netlist=NetsListed + NetsTocheck)

    componentsList = extract_components_list_fromJson(imported_json=dictFromJson)
    verifyComponents = check_components(edb=edb, componentsList=componentsList,
                                        logger=log)
    verify1 = check_nets(NetsTocheck=NetsTocheck, NetsTolist=NetsTolist,
                         NetsInEdb=NetsInEdb, logger=log)
    verify2 = list_nets(NetsTocheck=NetsTocheck, NetsTolist=NetsTolist,
                        NetsInEdb=NetsInEdb, logger=log)
    verifyPins = check_pins(edb, dictFromJson, log)

    print(f"NETSCheck: {verify1} NETSlist: {verify2} PINScheck:  {verifyPins}  Componenets check: {verifyComponents}")

    if verify1 and verify2 and verifyComponents and verifyPins:
        display("-----> Start Analysis", log)
        tdxt_xml_file = open(os.path.join(temp_folder, "si_wave_tdxt_scan.xml"), "w")
        tdxt_exec_file = open(os.path.join(temp_folder, "tdxt_scan.exec"), "w")
        si_scan_config = etree.Element("SIwaveScanConfig")
        tdxt_scan = etree.SubElement(si_scan_config, "TdXtalkConfig")
        Nets_type = ["SingleEndedNets", "DifferentialNets",
                     "ExtendedNets", "ExtendedDifferentialNets"]

        for netType in Nets_type:
            if netType in dictFromJson["XTTD scan"].keys():
                drivers = etree.SubElement(tdxt_scan, "DriverPins")
                pin = dictFromJson["XTTD scan"][netType]
                # from each element from the list from the dictionnary ( new one if there is regex)
                # write pins name  in *.xml file
                for i in range(0, len(pin)):
                    D_pin = etree.SubElement(drivers, "Pin")
                    pin_name = edb.core_padstack.get_pinlist_from_component_and_net \
                        (refdes=pin[i]["DriverComponent"], netname=pin[i]["Name"])
                    D_pin.set("Name", pin_name[0].GetName())
                    D_pin.set("RefDes", pin[i]["DriverComponent"])
                    defined_param("DriverRiseTime", D_pin, pin[i], default_values)
                    defined_param("Voltage", D_pin, pin[i], default_values)
                    defined_param("DriverImpedance", D_pin, pin[i], default_values)

                receivers = etree.SubElement(tdxt_scan, "ReceiverPins")
                pin = dictFromJson["XTTD scan"][netType]
                for i in range(0, len(pin)):
                    R_pin = etree.SubElement(receivers, "Pin")
                    pin_name = edb.core_padstack.get_pinlist_from_component_and_net \
                        (refdes=pin[i]["ReceiverComponent"], netname=pin[i]["Name"])
                    R_pin.set("Name", pin_name[0].GetName())
                    R_pin.set("RefDes", pin[i]["ReceiverComponent"])
                    defined_param("ReceiverImpedance", R_pin, pin[i], default_values, "TerminationImpedance")

        tdxt_exec_file.write("ExecTimeDomainCrosstalkSim \n"
                             "CrosstalkScanConfigFile "
                             + os.path.join(temp_folder, "si_wave_tdxt_scan.xml") +
                             "\nSetNumCpus 4\n"
                             "SetTdXtalkScanSimName -Time DOM ")
        tdxt_xml_file.write(etree.tostring(element_or_tree=si_scan_config,
                                           encoding="unicode", pretty_print=True))
        tdxt_xml_file.close()
        tdxt_exec_file.close()
        command = [siwave_ng_path, board_path, os.path.join(temp_folder, "tdxt_scan.exec"),
                   "-formatOutput", "-useSubdir"]
        subprocess.run(command)
        display("-----> Crosstalk Scan(Time Domain): Analysis Finished\n", log)

if create_html:
    # GENERATE  Z0  HTML REPORT
    # create a temporary script to create a report using SIwave
    create_z0_htmlreport = open(os.path.join(temp_folder, "create_z0_htmlreport.py"), "w")
    create_z0_htmlreport.write('oDoc= oApp.GetActiveProject()\n'
                               'oDoc.ScrExportZ0ScanReport("' + dictFromJsonNotModified
                               ["Z0scan"]["Parameters"]["ScanName"] + '", r"'
                               + os.path.join(project_path, "Reports", 'Z0-html-Report22.html') + '")')
    create_z0_htmlreport.close()
    # Open SIwave run a script and exit. (There is no batch mode for this function yet.)
    command=[siwave_path, board_path, "-runscriptandexit",os.path.join(temp_folder, "create_z0_htmlreport.py")]
    done= subprocess.run(command)

    if done.returncode ==0 :
        display("-----------------------------", log)
        display("-----> Z0 HTML report Created\n", log)

edb.close_edb()
display('\nProject Results File Location           : ' + project_path + '\n' +
        'Temporary Project File Location         : ' + temp_folder, log)
