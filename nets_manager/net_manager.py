from collections import defaultdict
from pyaedt import Edb
import json
import sys
import re


ext_keyword= "_EXTD"
args = sys.argv
print(args)

# json_path = "example.json"
# edb_path = "D:\Temp\Galileo.aedb"

json_path = args[1]
edb_path = args[2]
version = args[3]
## Open json file
j_file = open(json_path, "r")
jsonFile = json.load(j_file)
j_file.close()
edb = Edb(edbpath=edb_path, edbversion="2022.2") ################################
s_parameters_input = jsonFile["S-parameters"]

components_list= []
for comp_type in ["DriverComponents", "ReceiverComponents"]:
    for comp_name in s_parameters_input["Components"][comp_type]:
        components_list.append(comp_name)

RESISTOR = edb.edb.Definition.ComponentType.Resistor
INDUCTOR = edb.edb.Definition.ComponentType.Inductor
CAPACITOR = edb.edb.Definition.ComponentType.Capacitor
#######################################################################
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
    NetsToCheck = []
    NetsToList = []
    for net in NetstoClassify:
        # it is assumed that user will always be looking for 0 or more characters
        # which means "*", if there is a "*" characters in the string, it will be considered as regex
        if re.findall("[*]", net) or re.findall("[.]", net):
            NetsToList.append(net)
        else:
            NetsToCheck.append(net)
    return NetsToList, NetsToCheck

def list_nets_(NetToList, edb):
    """List the Nets full name

    :param:
        NetToList: list of str
            list of the partial Nets Name (regular expressions)
        edb: ``Edb`` object
    :return
        NetList: list of str
            the Nets full name, extracted from EDB with regular expression
    """
    NetList = []
    for net in NetToList:
        NetList = [Net for Net in edb.core_nets.signal_nets.keys() if re.findall(net, Net)]
    return NetList

def get_nets_on_components(comp_name):
    nets_connected_to_comp = []
    cmp = edb.edb.Cell.Hierarchy.Component.FindByName(edb.active_layout, comp_name)
    for obj in cmp.LayoutObjs:
        netName = '' if obj.GetNet().IsNull() else obj.GetNet().GetName()
        if netName != '':
            nets_connected_to_comp.append(netName)
    return nets_connected_to_comp

def get_rlc_connected_to_net(inputNet):
    netObj = edb.edb.Cell.Net.FindByName(edb.active_layout, inputNet)
    pinsConnectedToPwrNet = defaultdict(list)
    for padInst in netObj.PadstackInstances:
        refDes = '' if padInst.GetGroup().IsNull() else padInst.GetGroup().GetName()
        pinsConnectedToPwrNet[refDes].append(padInst)

    pinsConnectedToPwrNet.pop('', None)

    RLConnectedToNet = []
    for c in pinsConnectedToPwrNet:
        cmp = edb.edb.Cell.Hierarchy.Component.FindByName(edb.active_layout, c)
        if cmp.GetComponentType() == RESISTOR or cmp.GetComponentType() == INDUCTOR or cmp.GetComponentType() == CAPACITOR:
            RLConnectedToNet.append(c)
    return RLConnectedToNet

def check_connected_net(count, net, comp_name):
    if net in get_nets_on_components(comp_name):
        count += 1
    return count

def check_neg_pos_net(diff_net, positive_net, negative_net):
    diff_pair = edb.edb.Cell.DifferentialPair.FindByName(edb.active_layout, diff_net)
    if diff_pair.GetPositiveNet().GetName() == positive_net and diff_pair.GetNegativeNet().GetName() == negative_net:
        return True
    else:
        return False

def diff_net_exists(diff_net):
    if len(s_parameters_input["Differential Nets"][diff_net]) == 2:
        # check if each net is connected with both components at the same time
        # else send warning and create net
        pos_net = s_parameters_input["Differential Nets"][diff_net][0]
        neg_net = s_parameters_input["Differential Nets"][diff_net][1]

        if edb.edb.Cell.ExtendedNet.FindByName(edb.active_layout, pos_net).GetName() and edb.edb.Cell.ExtendedNet.FindByName(edb.active_layout, neg_net).GetName():
            return [edb.edb.Cell.ExtendedNet.FindByName(edb.active_layout, pos_net).GetName(),
                    edb.edb.Cell.ExtendedNet.FindByName(edb.active_layout, neg_net).GetName()]
        elif not check_neg_pos_net(diff_net, s_parameters_input["Differential Nets"][diff_net][0],
                                 s_parameters_input["Differential Nets"][diff_net][1]):
            print("ERROR: the mentionned nets do not correspond to the right differential pair")
        else:

            count_neg, count_pos = 0,0
            for compo in components_list:
                count_neg += check_connected_net(0, neg_net, compo)
                count_pos += check_connected_net(0, pos_net, compo)
            if  count_neg > 1 and count_pos > 1:
                return [pos_net, neg_net]
            else:
                print(f"Net {diff_net} not connected to components")
    elif len(s_parameters_input["Differential Nets"][diff_net]) == 0:
        # give the positive and negative nets
        diff_pair = edb.edb.Cell.DifferentialPair.FindByName(edb.active_layout, diff_net)
        return [diff_pair.GetPositiveNet().GetName(), diff_pair.GetNegativeNet().GetName()]

def nets_in_extended_net(extd_net):
    x_net_list = []
    for net in extd_net.Nets:
        for compo in components_list:
            if check_connected_net(0, net.GetName(), compo):
                x_net_list.append(net.GetName())
                break
    return x_net_list

def DiffList(listA, listB):
    return [elem for elem in listA if elem not in listB]

def shortest_string(stringA, stringB):
    if len(stringA)<len(stringB):
        return stringA
    else:
        return stringB

def connected_extended_net(input_net, components):
    for comp_type in components.keys():
        count = 0
        for c in components[comp_type]:
            if check_connected_net(count, input_net, c) == 1:
                rlc_list = get_rlc_connected_to_net(input_net)
                nets_rlc = DiffList(get_nets_on_components(rlc_list[0]), [input_net])
                while len(rlc_list)!=0:
                    rlc_list = DiffList(get_rlc_connected_to_net(nets_rlc[0]), rlc_list)
                    if rlc_list:
                        nets_rlc = DiffList(get_nets_on_components(rlc_list[0]), nets_rlc)
                if comp_type == "DriversComponents":
                    for comp in components["ReceiversComponents"]:

                        return [input_net, nets_rlc[0]] if check_connected_net(0, nets_rlc[0], comp) \
                            else print("ERROR: the net input does not give the net connected to two components ")
                else:
                    for comp in components["DriversComponents"]:
                        return [input_net, nets_rlc[0]] if check_connected_net(0, nets_rlc[0], comp) \
                            else print("ERROR: the net input does not give the net connected to two components ")

def diff_net_not_existed(diff_net):
    diff_pair=[]
    if len(s_parameters_input["Differential Nets"][diff_net]) == 0:
        print("ERROR: the differential pair is not defined in database")
    elif len(s_parameters_input["Differential Nets"][diff_net]) == 2:
        nets = s_parameters_input["Differential Nets"][diff_net]
        positive_net_extd = edb.edb.Cell.ExtendedNet.FindByName(edb.active_layout, nets[0])
        negative_net_extd = edb.edb.Cell.ExtendedNet.FindByName(edb.active_layout, nets[1])
        positive_net = edb.edb.Cell.Net.FindByName(edb.active_layout, nets[0])
        negative_net = edb.edb.Cell.Net.FindByName(edb.active_layout, nets[1])
        print(positive_net_extd.GetName(), positive_net.GetName())
        if negative_net.GetName() and positive_net.GetName():
            pos_net, neg_net = positive_net.GetName(), negative_net.GetName(),
            count_neg, count_pos = 0, 0
            for comp_name in components_list:
                count_neg += check_connected_net(0, neg_net, comp_name)
                count_pos += check_connected_net(0, pos_net, comp_name)
            if count_neg > 1 and count_pos > 1:
                create_diff = edb.edb.Cell.DifferentialPair.Create(edb.active_layout, diff_net, positive_net,
                                                                 negative_net)
                diff_pair= [pos_net, neg_net] if create_diff else print("ERROR: {diff_net} doesn't exist and cannot be created")

            else:
                components = s_parameters_input["Components"]
                diff_pair = [shortest_string(connected_extended_net(pos_net, components)[0],connected_extended_net(pos_net, components)[1])+ext_keyword,
                             connected_extended_net(pos_net, components),
                             shortest_string(connected_extended_net(neg_net, components)[0], connected_extended_net(neg_net, components)[1]) + ext_keyword,
                             neg_net, connected_extended_net(neg_net, components)]
        elif positive_net_extd.GetName() and negative_net_extd.GetName():
            edb.edb.Cell.DifferentialPair.Create(edb.active_layout, diff_net, positive_net, negative_net)
            diff_pair = [positive_net_extd, negative_net_extd]
        else:
            print("ERROR: one of the nets may not exist")
    return diff_pair

def non_repetitive_list(_list):
    return_list = []
    for el in _list:
        if el not in return_list:
            return_list.append(el)
    return return_list

# ### Nets
if  "SingleEnded Nets" in s_parameters_input.keys() and len(s_parameters_input["SingleEnded Nets"]) :
    net_to_list, net_with_full_name = classify_nets(s_parameters_input["SingleEnded Nets"])
    nets_full_name =  list_nets_(net_to_list, edb)
    s_parameters_input["SingleEnded Nets"] = nets_full_name + net_with_full_name
    print(s_parameters_input["SingleEnded Nets"])

elif "Differential Nets" in s_parameters_input.keys() and len(s_parameters_input["Differential Nets"]) :
    diff_net_to_classify = []
    for diff_pair in s_parameters_input["Differential Nets"].keys():
        if not len( s_parameters_input["Differential Nets"][diff_pair]):
            diff_net_to_classify.append(diff_pair)

    for diff_pair in diff_net_to_classify:
        del s_parameters_input["Differential Nets"][diff_pair]

    net_to_list, net_with_full_name = classify_nets(diff_net_to_classify)
    nets_full_name = list_nets_(net_to_list, edb)
    diff_net_full_list = nets_full_name + net_with_full_name
    for diff_pair in diff_net_full_list:
        s_parameters_input["Differential Nets"][diff_pair]=[]


signal_nets = []
new_nets_dict = {}

if "Differential Nets" in s_parameters_input.keys() and len(s_parameters_input["Differential Nets"]) :
    ext_dict = {}
    diff_dict = {}
    for diff_pair in s_parameters_input["Differential Nets"].keys():
        if edb.edb.Cell.DifferentialPair.FindByName(edb.active_layout, diff_pair).GetName():
            [pos_net, neg_net] = diff_net_exists(diff_pair) if diff_net_exists(diff_pair) is not None else []
            count_neg, count_pos = 0,0
            for comp_name in components_list:
                count_neg += check_connected_net(0, neg_net, comp_name)
                count_pos += check_connected_net(0, pos_net, comp_name)
            if  count_neg > 1 and count_pos > 1:
                diff_dict[diff_pair] = [pos_net, neg_net]
                signal_nets += [pos_net, neg_net]
            else:
                print("ERROR: Nets not connected to components")
        else:

            differential_net = diff_net_not_existed(diff_pair)
            if isinstance(differential_net, list):
                if len(differential_net) == 2:
                    diff_dict[diff_pair] = [differential_net[0].GetName(), differential_net[1].GetName()]
                    ext_dict[differential_net[0].GetName()] = nets_in_extended_net(differential_net[0])
                    ext_dict[differential_net[1].GetName()] = nets_in_extended_net(differential_net[1])
                    signal_nets += nets_in_extended_net(differential_net[0])+nets_in_extended_net(differential_net[1])
                elif len(differential_net) == 4:
                    diff_dict[diff_pair] = [differential_net[0], differential_net[2] ]
                    ext_dict[differential_net[0]] = differential_net[1]
                    ext_dict[differential_net[2]] = differential_net[2]
                    signal_nets += [differential_net[1], differential_net[2]]
            else:
                diff_dict[diff_pair] = [differential_net[0].GetName(), differential_net[1].GetName()]
                signal_nets += [differential_net[0].GetName(), differential_net[1].GetName()]
    new_nets_dict["Differential Nets"] = diff_dict
    new_nets_dict["Extended Nets"] = ext_dict

signal_nets +=  s_parameters_input["SingleEnded Nets"] if "SingleEnded Nets" in s_parameters_input.keys() else []
signal_nets =non_repetitive_list(signal_nets)
new_nets_dict["Signal Nets"] = signal_nets
new_nets_dict["Components"] = components_list

j_file = open("nets_sorted.json", "w")
jsonFile = json.dump(new_nets_dict,j_file, indent=2)
print(new_nets_dict)
j_file.close()
edb.close_edb()
