import re
from pyaedt import AedtLogger

####### FUNCTIONS
def create_logger(report_file):
    """ Create logger

    :param report_file: *.log file location
    :return: AedtLogger object
    """
    return AedtLogger(filename=report_file, to_stdout=False)

def display(text, logger):
    """
    print text in the terminal and in *.log file

    :param:
        text: str
            text to display
        logger: file
            in which the text will be written
    :return:
        None
    """
    logger.info(msg=text)

def check_nets(NetsTocheck, NetsTolist, NetsInEdb,logger):
    """
    Check if the given full name of the net exists in Edb

    :param:
        NetsTocheck: list of the nets with their fullname to verify
        NetsTolist: list of sequence(name part) to find in the Edb Nets name list
        NetsInEdb: list Signal nets name extracted from Edb
        logger: file in which the results will be written
    :return:
        bool
    """
    countNet=0
    # if the name sequence list is empty and not the net to check list
    # considered the condition return true, in that case the condition 'AND' can be used
    if NetsTolist and len(NetsTocheck) == 0:
        return True
    elif len(NetsTolist) == 0 and len(NetsTocheck) == 0:
        return False
    # if the name sequence list is not empty whatever the nets to check list is
    # associated nets names will be searched
    elif NetsTocheck:
        display("NETS VERIFICATION: ",logger)
        display("---------------------",logger)
        for Net in NetsTocheck:
            for net in NetsInEdb:
                if net == Net:
                    display(f"NET {Net} | FOUND",logger)
                    countNet += 1
                    # each net name is supposed to be unique, so when found,
                    # there's no need to continue the research
                    break
        if countNet == len(NetsTocheck):
            return True
        else:
            return False
    display("---------------------", logger)

def list_nets(NetsTolist, NetsTocheck,NetsInEdb,logger):
    """
        List all nets in edb containing a part of the net name is given,
        find at least one net that contains the sequence(name part) you are looking for

        Parameters:
        -----------
        NetsTocheck: list of the nets with their fullname to verify
        NetsTolist: list of sequence(name part) to find in the Edb Nets name list
        NetsInEdb: list Signal nets name extracted from Edb
        logger: file in which the results will be written

        Returns:
        -----------
        bool
        """
    # if the name sequence list is empty and not the net to check list
    # considered the condition return true, in that case the condition 'AND' can be used
    if len(NetsTolist)==0 and len(NetsTocheck)>0:
        return True
    elif len(NetsTolist)==0 and len(NetsTocheck)==0:
        return False
    # if the name sequence list is not empty whatever the nets to check list is
    # associated nets names will be searched
    elif len(NetsTolist)>0:

        display(f"---- LIST NET SEQUENCE ----",logger)
        display("---------------------------------",logger)

        foundInList= 0
        foundInEdb = 0
        for Net in NetsTolist:
            display(f"with: {Net}",logger)
            display("---------------------------------",logger)
            for net in NetsInEdb:
                    if re.findall(Net, net):  # Net is a regular expression
                        display(f"NET {net} \t| FOUND",logger)
                        foundInEdb+=1
            if foundInEdb==0:
                display(f"NET  {Net} SEQUENCE \t| NOT FOUND",logger)
            else:
                foundInList += 1
        display("---------------------", logger)
        # at least one net must be found for each regex in the Nets name to list
        if foundInList == len(NetsTolist) and foundInEdb:
            return True
        else:
            return False

def classify_nets(NetstoClassify):
    '''
    For the nets verification, it is necessary to classify the nets in two categories:
     1- (To check) If the full name of the net is given, check its existence in Edb\n
     2- (To list) If a part of the net name is given,
           find at least one net that contains the sequence(name part) you are looking for
    :param:
        NetstoClassify: list of str
            list of nets "name" to be classified

    :return:
              NetsToList: list of str
                list of sequence(name part/regex) to find in the Edb Nets name list
              NetsToCheck: list of str
                list of the nets fullname
    '''
    NetsToCheck=[]
    NetsToList=[]
    for net in NetstoClassify:
        # it is assumed that user will always be looking for 0 or more characters
        # which means "*", if there is a "*" characters in the string, it will be considered as regex
        if re.findall("[*]", net) or re.findall("[.]", net):
            NetsToList.append(net)
        else:
            NetsToCheck.append(net)
    return NetsToList, NetsToCheck

def extract_netsNames(imported_json, sim_name):
    """
    Extract All Nets Name from *.json file

    :param:
        imported_json: file
            *.json file from which the names will be extracted
        sim_name: str
            the name of the Simulation
    :return Netsname: list
            Nets name list

    """
    Netsname=[]
    undesirablelist=["Parameters","DriverPins","DriverComponents","ReceiverPins","ReceiveComponents"]
    for nets_type in imported_json[sim_name].keys():
        if nets_type not in undesirablelist:
            for i in range(0,len(imported_json[sim_name][nets_type])):
                Netsname.append(imported_json[sim_name][nets_type][i]["Name"])
    return Netsname

def extract_components_list_fromJson(imported_json):
    """
    Extract All Components Name from *.json file

    :param:
        imported_json: Dict
            *.json file from which the names will be extracted

    :return:
        componentsList: list of str
                Components name list

    """
    netsType = ["SingleEndedNets", "DifferentialNets", "ExtendedNets", "ExtendedDifferentialNets"]
    componentsList = []
    for netType in netsType:
        if netType in imported_json["XTTD scan"].keys() :
            componentsType = ['DriverComponent', 'ReceiverComponent']
            for componenttype in componentsType:
                for i in range(0, len(imported_json["XTTD scan"][netType])):
                    componentsList.append(imported_json["XTTD scan"][netType][i][componenttype])

    # make sure to avoid repetitive components names in the list
    componentsList.sort()
    uniqueNameList=[]
    for i in range(0, len(componentsList)):
        if i == 0:
            current_comp_name = componentsList[i]
            uniqueNameList.append(current_comp_name)
        else:
            previous_comp_name = current_comp_name
            current_comp_name = componentsList[i]
            # the component list is sorted, so if the previous name is the same as the actual one
            # skip it
            if current_comp_name != previous_comp_name:
                uniqueNameList.append(current_comp_name)
    return uniqueNameList

def check_components(componentsList,edb,logger):
    """
    Check if the components list extracted from *.json file exists in Edb

    :param:
        componentsList: list of str
            the components list extracted from *.json file
        edb:``Edb`` object
        logger: Aedtlogger object
            file in which the results will be written

    :return:
        bool
    """
    countComponents=0
    display("COMPONENTS VERIFICATION: ",logger)
    display("---------------------",logger)

    for component in componentsList:
        if component in edb.core_components.components.keys():
            countComponents +=1
            display(f"COMPONENT {component} | FOUND",logger)

    if countComponents == len(componentsList):
        display(f"-----ALL COMPONENTS FOUND-------\n",logger)
        display("---------------------", logger)
        return True
    else:
        display(f"------COMPONENTS MISSING--------\n",logger)
        display("---------------------", logger)
        return False

def check_pins( edb, imported_json,logger):
    """
    With the nets and the components names being extracted (from *.json),
    find the pins name associated

    :param:
        edb: ``Edb`` object
        imported_json: Dict
            dictionary from which the nets and the components names will
            be extracted to find the pins name
        logger: Aedtlogger object
            file in which the results will be written
    :return: bool
    """
    display("-------------PINS CHECK---------------\n"
          "\t-> NET    ____________________________\n"
          "\t    * PIN \t(COMPONENT)   \t| STATE \n"
          "\t--------------------------------------",logger)
    Nets_type = ["SingleEndedNets", "DifferentialNets", "ExtendedNets", "ExtendedDifferentialNets"]
    countDiffPins=0
    countSigPins = 0
    countDiff=0
    countsingle=0
    countTotalPins=0
    ref=0
    for netType in Nets_type:
        if netType in imported_json["XTTD scan"].keys():
            ref+=1
            display(f"-------- {netType} ------------|",logger)
            for  i in range(0,len(imported_json["XTTD scan"][netType])):
                net =imported_json['XTTD scan'][netType][i]["Name"]
                display(f"-> {net}____________________________|",logger)
                componentsType = ['DriverComponent', 'ReceiverComponent']
                for componenttype in componentsType:
                    component = imported_json['XTTD scan'][netType][i][componenttype]
                    pin = edb.core_padstack.get_pinlist_from_component_and_net(refdes=component, netname=net)
                    try:
                        pinName = pin[0].GetName()  # pin[0] is an object
                        countTotalPins +=1
                        display(f"       * {pinName} \t({component})   \t| FOUND",logger)
                    except TypeError:  # make sure pin[0] is not empty
                        display(f"ERROR: PINS \t({net}|{component})   \t| NOT FOUND",logger)
                        display("Make sure the net and the component designed are well connected", logger)
                        return False
                        pass
                        break
            # for each single-ended net there is a total of 2 pins expected
            if netType in ["SingleEndedNets", "ExtendedNets"]:
                countSigPins += 2 * len(imported_json["XTTD scan"][netType])
                countsingle +=1
            # for each differential net there is a total of 4 pins expected
            elif netType in ["DifferentialNets", "ExtendedDifferentialNets"]:
                countDiffPins += 4 * len(imported_json["XTTD scan"][netType])
                countDiff += 1
    if countTotalPins == ((countSigPins*countsingle)+(countDiffPins*countDiff)):
        display("----------ALL PINS FOUND----------\n", logger)
        display("---------------------", logger)
        return True
    else:
        display("----------ERROR : PINS MISSING------\n", logger)
        display("Make sure the nets and the components designed are well connected", logger)
        display("---------------------", logger)
        return False

def list_nets_tdx(NetToList, edb):
    """List the Nets full name

    :param:
        NetToList: list of str
            list of the partial Nets Name (regular expressions)
        edb: ``Edb`` object
    :return
        NetList: list of str
            the Nets full name, extracted from EDB with regular expression
    """
    NetList=[]
    for net in NetToList:
        NetList = [Net for Net in edb.core_nets.signal_nets.keys() if re.findall(net, Net)]
    return NetList

def reshape_imported_json(imported_json, Netlist):
    """
    Création d'une variable de type dicationary qui va faciliter la création des Pins.

    In the *.xml file generated, the section singled-ended nets allows writing only one net
    (including the regular expression) without specification of driver or receiver components.
    So to solve this problem it was decided to define the pins (driver and receiver) for
    each net whose name was fully given.
    Thus, this function will make sure to create a new dictionary where especially the name
    of the net is the full one found in the Edb signal nets associated with the informations
    given with the regular expression

    :param:
        imported_json:Dict
            dictionary from which the nets name (including the regular expression)
             will be taken to build the new dictionary
        Netlist: list of str
            list of nets with their fullname
    :return:
        json_dict: Dict
            the new dictionary
    """
    Nets_type = ["SingleEndedNets", "DifferentialNets", "ExtendedNets", "ExtendedDifferentialNets"]
    for netType in Nets_type:
        if netType in imported_json["XTTD scan"].keys():
            json_dict={"XTTD scan":
                                {netType:[]}}
            for i in range(0,len(imported_json["XTTD scan"][netType])):
                netname = imported_json["XTTD scan"][netType][i]["Name"] # can be regular expression or not
                # if the name of the net is a regular expression, so create list elements with
                # the  information given with the regex associated to the full name (as the new net nae) found in Edb
                # otherwise (full nam already given case) just create only one with its own information
                if re.findall("[*]", netname) or re.findall("[.]", netname):  # all Net name with "*" or "." is considered as regular expression
                    json_dict["XTTD scan"][netType] = [pin_info(net, imported_json, netType,i) for net in Netlist if re.findall(netname, net) ]
                else:
                    json_dict["XTTD scan"][netType].append(pin_info(netname, imported_json, netType,i))
    return json_dict

def pin_info (netname, imported_json, netType, index):
    """information related to the nets that will build the new dictionary

    :param:
        netname: str
            name of the Net that can be a regex
        imported_json: Dict
            *.json that will be the based of the new dictionary
        netType: str
            SingleEnded Nets or others Type found
        index: int
            where to place the Net found in the Edb (with the regex)

    :return:
        dico : Dict
            a new dictionary
    """
    dico = {"Name": netname,
            "DriverRiseTime": imported_json["XTTD scan"][netType][index]["DriverRiseTime"],
            "Voltage": imported_json["XTTD scan"][netType][index]["Voltage"],
            "DriverImpedance": imported_json["XTTD scan"][netType][index]["DriverImpedance"],
            "TerminationImpedance": imported_json["XTTD scan"][netType][index]["TerminationImpedance"],
            "DriverComponent": imported_json["XTTD scan"][netType][index]["DriverComponent"],
            "ReceiverComponent": imported_json["XTTD scan"][netType][index]["ReceiverComponent"]}
    return dico

def defined_param(paramInXml, etree ,current_dict, defaultValues, paramInJson = ""):
    """
    This function allows to set the default value in the xml file in case
    the information for some parameters is not recorded

    :param paramInXml: str
        The name of the parameters set as default in the xml file.
    :param etree: Any
        The xml object
    :param current_dict: dict
        The dictionary extracted from the *.json file
    :param defaultValues: str
        The default to be set in case information is missing
    :param paramInJson: str
        The name of the parameter in the json file
    :return: None
    """
    if not paramInJson:
        paramInJson = paramInXml

    if paramInJson not in current_dict.keys():
        etree.set(paramInXml, defaultValues[paramInJson])
    else:
        etree.set(paramInXml, current_dict[paramInJson])
