# tech2xl
#
# Parses a file containing one or more show tech of Cisco devices
# and extracts system information. Then it writes to an Excel file
# You can put show tech of as many Cisco devices as you want in one file
# or you can have multiple files and use wildcards
#
# Requires xlwt library. For Python 3, use xlwt-future (https://pypi.python.org/pypi/xlwt-future)
#
# usage: python tech2xl <Excel output file> <inputfile>...
#
# Author: Andres Gonzelez, dec 2015

import re, glob, sys, csv, collections
import time
import os

def expand(s, list):
    for item in list:
        if len(s) <= len(item):
            if s.lower() == item.lower()[:len(s)]:
                return item
    return None


def expand_string(s, list):
    result = ''
    for pos, word in enumerate(s.split()):
        expanded_word = expand(word, list[pos])
        if expanded_word is not None:
            result = result + ' ' + expanded_word
        else:
            return None
    return result[1:]

start_time = time.time()
print("tech2xl v1.5")

#if len(sys.argv) < 2:
    #print("Usage: tech2xl <output file> <input files>...")
    #sys.exit(2)

commands = [["show"], \
            ["version", "cdp", "technical-support", "running-config", "interfaces", "diag", "inventory"], \
            ["neighbors", "status"], \
            ["detail"]]


int_types = ["Ethernet", "FastEthernet", "GigabitEthernet", "Gigabit", "TenGigabit", "Serial", "ATM", "Port-channel", "Tunnel", "Loopback"]

# Inicialized the collections.OrderedDictionary that will store all the info
systeminfo = collections.OrderedDict()
intinfo = collections.OrderedDict()
cdpinfo = collections.OrderedDict()
diaginfo = collections.OrderedDict()

#These are the fields to be extracted
systemfields = ["Name", "Model", "System ID", "Mother ID", "Image", "Uptime"]

intfields = ["Name", \
            "Interface", \
            "Type", \
            "Number", \
            "Description", \
            "Status", \
            "Line protocol", \
            "Hardware", \
            "Mac address", \
            "Encapsulation", \
            "Switchport mode", \
            "Access vlan", \
            "Voice vlan", \
            "IP address", \
            "Mask bits", \
            "Mask", \
            "Network", \
            "Last cleared", \
            "Output drops", \
            "Packets output", \
            "Output bytes", \
            "Packets input", \
            "Input bytes", \
            "Input errors", \
            "CRC", \
            "Frame errors", \
            "Overrun", \
            "Ignored", \
            "Output errors", \
            "Collisions", \
            "Interface resets", \
            "DLCI", \
            "Duplex", \
            "Speed", \
            "Media type"]   

cdpfields = ["Name", "Local interface", "Remote device name", "Remote device domain", "Remote interface", "Remote device IP"]

diagfields = ["Name", "Description", "Serial number", "Part number"]

masks = ["128.0.0.0","192.0.0.0","224.0.0.0","240.0.0.0","248.0.0.0","252.0.0.0","254.0.0.0","255.0.0.0","255.128.0.0","255.192.0.0","255.224.0.0","255.240.0.0","255.248.0.0","255.252.0.0","255.254.0.0","255.255.0.0","255.255.128.0","255.255.192.0","255.255.224.0","255.255.240.0","255.255.248.0","255.255.252.0","255.255.254.0","255.255.255.0","255.255.255.128","255.255.255.192","255.255.255.224","255.255.255.240","255.255.255.248","255.255.255.252","255.255.255.254","255.255.255.255"]


for filename in os.listdir("."):
    if filename.endswith(".txt"):
        infile = open(filename, "r")
        # This is the name of the router
        name = ''

        # Identifies the section of the file that is currently being read
        command = ''
        section = ''
        item = ''
        cdp_neighbor = ''

        take_next_line = 0

        for line in infile:

            # checks for device name in prompt
            m = re.search("^([a-zA-Z0-9][a-zA-Z0-9_\-\.]*)[#>]\s*([\w\-\_\s\b\a]*)", line)
            # avoids a false positive in the "show switch detail" or "show flash: all" section of show tech
            if m and not (command == "show switch detail" or command == "show flash: all"):

                if name == '':
                    infile.seek(0)
                else:
                    #removes all deleted chars with backspace (\b) and bell chars (\a)
                    cli = m.group(2)

                    while re.search("\b|\a", cli):
                        cli = re.sub("[^\b]\b|\a", "", cli)
                        cli = re.sub("^\b", "", cli)
                    command = expand_string(cli, commands)

                name = m.group(1)
                section = ''
                item = ''

                if name not in systeminfo.keys():
                    systeminfo[name] = collections.OrderedDict(zip(systemfields, [''] * len(systemfields)))
                    systeminfo[name]['Name'] = name

                if name not in intinfo.keys():
                    intinfo[name] = collections.OrderedDict()

                if name not in cdpinfo.keys():
                    cdpinfo[name] = collections.OrderedDict()

                continue

            # detects section within show tech
            m = re.search("^------------------ (.*) ------------------$", line)
            if m:
                command = m.group(1)
                section = ''
                item = ''
                continue

            # processes "show running-config" command or section of sh tech
            if command == 'show running-config':
                # extracts information as per patterns

                m = re.match("hostname ([a-zA-Z0-9][a-zA-Z0-9_\-\.]*)", line)
                if m:
                    if name == '':
                        name = m.group(1)
                        infile.seek(0)

                        section = ''
                        item = ''

                        if name not in systeminfo.keys():
                            systeminfo[name] = collections.OrderedDict(zip(systemfields, [''] * len(systemfields)))
                            systeminfo[name]['Name'] = name

                        if name not in intinfo.keys():
                            intinfo[name] = collections.OrderedDict()

                        if name not in cdpinfo.keys():
                            cdpinfo[name] = collections.OrderedDict()

                    continue

                m = re.match("interface (\S*)", line)
                if m:
                    section = 'interface'
                    item = m.group(1)

                    if item not in intinfo[name].keys():
                        intinfo[name][item] = collections.OrderedDict(zip(intfields, [''] * len(intfields)))
                        intinfo[name][item]['Name'] = name
                        intinfo[name][item]['Interface'] = item
                        
                        intinfo[name][item]['Type'] = re.split('\d', item)[0]
                        intinfo[name][item]['Number'] = re.split('\D+', item, 1)[1]
                    continue

                if section == 'interface':

                    if line == '!':
                        section = ''
                        continue

                    m = re.match(" description (.*)", line)
                    if m:
                        intinfo[name][item]['Description'] = m.group(1)
                        continue

                    m = re.match(" switchport mode (\w*)", line)
                    if m:
                        intinfo[name][item]['Switchport mode'] = m.group(1)
                        continue

                    m = re.search(" switchport access vlan (\d+)", line)
                    if m:
                        intinfo[name][item]["Access vlan"] = m.group(1)
                        continue

                    m = re.search(" switchport voice vlan (\d+)", line)
                    if m:
                        intinfo[name][item]["Voice vlan"] = m.group(1)
                        continue

                    m = re.search(" frame-relay interface-dlci (\d+)", line)
                    if m:
                        intinfo[name][item]["DLCI"] = int(m.group(1))
                        continue

                    m = re.search("^ ip address ([\d|\.]+) ([\d|\.]+)", line)
                    if m:
                        intinfo[name][item]['IP address'] = m.group(1)
                        intinfo[name][item]['Mask'] = m.group(2)
                        intinfo[name][item]['Mask bits'] = masks.index(m.group(2)) + 1

                        m = re.search("(\d+)\.(\d+)\.(\d+)\.(\d+)", intinfo[name][item]['IP address'])
                        
                        a = int(m.group(1))
                        b = int(m.group(2))
                        c = int(m.group(3))
                        d = int(m.group(4))

                        m = re.search("(\d+)\.(\d+)\.(\d+)\.(\d+)", intinfo[name][item]['Mask'])
                        
                        intinfo[name][item]['Network'] = str(a & int(m.group(1))) + '.' + \
                                                         str(b & int(m.group(2))) + '.' + \
                                                         str(c & int(m.group(3))) + '.' + \
                                                         str(d & int(m.group(4)))
                        continue

            # processes "show version" command or section of sh tech
            if command == 'show version' and name != '':
                # extracts information as per patterns
                m = re.search("Processor board ID (.*)", line)
                if m:
                    systeminfo[name]['System ID'] = m.group(1)
                    continue

                m = re.search("Model number\s*: (.*)", line)
                if m:
                    systeminfo[name]['Model'] = m.group(1)
                    continue

                m = re.search("^cisco (.*) processor", line)
                if m:
                    systeminfo[name]['Model'] = m.group(1)
                    continue

                m = re.search("^Cisco (.*) \(revision", line)
                if m:
                    systeminfo[name]['Model'] = m.group(1)
                    continue

                m = re.search("Motherboard Serial Number\s*: (.*)", line)
                if m:
                    systeminfo[name]['Mother ID'] = m.group(1)
                    continue

                m = re.search('System image file is \"flash:\/?(.*)\.bin\"', line)
                if m:
                    systeminfo[name]['Image'] = m.group(1)
                    continue

                m = re.search('System image file is \"flash:\/.*\/(.*)\.bin\"', line)
                if m:
                    systeminfo[name]['Image'] = m.group(1)
                    continue

                m = re.search('System image file is \"bootflash:(.*)\.bin\"', line)
                if m:
                    systeminfo[name]['Image'] = m.group(1)
                    continue

                m = re.search('System image file is \"sup-bootflash:(.*)\.bin\"', line)
                if m:
                    systeminfo[name]['Image'] = m.group(1)
                    continue

                m = re.search(r'Cisco IOS.*?, Version (\d+\.\d+\.\d+)', line)
                if m:
                    systeminfo[name]['Image'] = m.group(1)
                    continue

                m = re.search('.* uptime is (.*)', line)
                if m:
                    systeminfo[name]['Uptime'] = m.group(1)
                    continue



            # processes "show interfaces" command or section of sh tech
            if command == 'show interfaces' and name != '':
                # extracts information as per patterns

                m = re.search("^(\S+) is ([\w|\s]+), line protocol is (\w+)", line)
                if m:
                    item = m.group(1)
                    if item not in intinfo[name].keys():
                        intinfo[name][item] = collections.OrderedDict(zip(intfields, [''] * len(intfields)))
                        intinfo[name][item]['Name'] = name
                        intinfo[name][item]['Interface'] = item

                    intinfo[name][item]['Status'] = m.group(2)
                    intinfo[name][item]['Line protocol'] = m.group(3)
                    continue

                m = re.search("Hardware is (.+), address is ([\w|\.]+)", line)
                if m:
                    intinfo[name][item]['Hardware'] = m.group(1)
                    intinfo[name][item]['Mac address'] = m.group(2)
                    continue

                m = re.search("Hardware is ([\w\s-]+)$", line)
                if m:
                    intinfo[name][item]['Hardware'] = m.group(1)
                    continue

                m = re.search("^  Encapsulation ([\d|\w|\s|-]+),", line)
                if m:
                    intinfo[name][item]['Encapsulation'] = m.group(1)
                    continue

                m = re.search("^  Description: (.*)", line)
                if m:
                    intinfo[name][item]['Description'] = m.group(1)
                    continue

                m = re.search("^  Internet address is ([\d|\.]+)\/(\d+)", line)
                if m:
                    intinfo[name][item]['IP address'] = m.group(1)
                    intinfo[name][item]['Mask bits'] = int(m.group(2))
                    intinfo[name][item]['Mask'] = masks[int(m.group(2)) - 1]

                    m = re.search("(\d+)\.(\d+)\.(\d+)\.(\d+)", intinfo[name][item]['IP address'])
                    
                    a = int(m.group(1))
                    b = int(m.group(2))
                    c = int(m.group(3))
                    d = int(m.group(4))

                    m = re.search("(\d+)\.(\d+)\.(\d+)\.(\d+)", intinfo[name][item]['Mask'])
                    
                    intinfo[name][item]['Network'] = str(a & int(m.group(1))) + '.' + \
                                                     str(b & int(m.group(2))) + '.' + \
                                                     str(c & int(m.group(3))) + '.' + \
                                                     str(d & int(m.group(4)))
                    continue
              
                m = re.search("Last clearing of .* counters (.*)", line)
                if m:
                    intinfo[name][item]['Last cleared'] = m.group(1)
                    continue

                m = re.search("\S+ Total output drops: (\d+)", line)
                if m:
                    intinfo[name][item]['Output drops'] = m.group(1)
                    continue

                m = re.search("(\d+) packets output", line)
                if m:
                    intinfo[name][item]['Packets output'] = int(m.group(1))

                    m = re.search("(\d+) bytes", line)
                    if m:
                        intinfo[name][item]['Output bytes'] = int(m.group(1))

                    continue
                m = re.search("(\d+) packets input", line)
                if m:
                    intinfo[name][item]['Packets input'] = int(m.group(1))

                    m = re.search("(\d+) bytes", line)
                    if m:
                        intinfo[name][item]['Input bytes'] = int(m.group(1))

                    continue

                m = re.search("(\d+) input errors", line)
                if m:
                    intinfo[name][item]['Input errors'] = int(m.group(1))
  
                    m = re.search("(\d+) CRC", line)
                    if m:
                        intinfo[name][item]['CRC'] = int(m.group(1))

                    m = re.search("(\d+) frame", line)
                    if m:
                        intinfo[name][item]['Frame errors'] = int(m.group(1))

                    m = re.search("(\d+) overrun", line)
                    if m:
                        intinfo[name][item]['Overrun'] = int(m.group(1))

                    m = re.search("(\d+) ignored", line)
                    if m:
                        intinfo[name][item]['Ignored'] = int(m.group(1))

                    continue

                m = re.search("(\d+) output errors", line)
                if m:
                    intinfo[name][item]['Output errors'] = int(m.group(1))

                    m = re.search("(\d+) collisions", line)
                    if m:
                        intinfo[name][item]['Collisions'] = int(m.group(1))

                    m = re.search("(\d+) interface resets", line)
                    if m:
                        intinfo[name][item]['Interface resets'] = int(m.group(1))
                    continue

                m = re.search("(\w+) Duplex, (\d+)Mbps, link type is (\w+), media type is (.*)", line)
                if m:
                    intinfo[name][item]['Duplex'] = m.group(3) + "-" + m.group(1)
                    intinfo[name][item]['Speed'] = m.group(3) + "-" + m.group(2)
                    intinfo[name][item]['Media type'] = m.group(4)
                    continue

                m = re.search("(\w+)-duplex, (\d+)Mb/s, media type is (.*)", line)
                if m:
                    intinfo[name][item]['Duplex'] = m.group(1)
                    intinfo[name][item]['Speed'] = m.group(2)
                    intinfo[name][item]['Media type'] = m.group(3)
                    continue


            # processes "show interfaces status" command or section of sh tech
            if command == 'show interfaces status' and name != '':
                if (line[:4] != "Port"):
                    item = expand(line[:2], int_types)

                    if item is not None:
                        item = item + line[2:8].rstrip()

                        if item not in intinfo[name].keys():
                            intinfo[name][item] = collections.OrderedDict(zip(intfields, [''] * len(intfields)))
                            intinfo[name][item]['Name'] = name
                            intinfo[name][item]['Interface'] = item
                            intinfo[name][item]['Type'] = re.split('\d', item)[0]
                            intinfo[name][item]['Number'] = re.split('\D+', item, 1)[1]

                    m = re.search("(.+) (connected|notconnect|disabled)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)", line[8:])
                    if m:
                        if intinfo[name][item]['Description'] == '':
                            intinfo[name][item]['Description'] = m.group(1)
                        if intinfo[name][item]['Status'] == '':
                            intinfo[name][item]['Status'] = m.group(2)
                        if intinfo[name][item]['Access vlan'] == '':
                            if m.group(3) == 'trunk':
                                intinfo[name][item]['Switchport mode'] = 'trunk'
                            elif m.group(3) == 'routed':
                                intinfo[name][item]['Switchport mode'] = 'routed'
                            else:
                                intinfo[name][item]['Access vlan'] = m.group(3)
                        intinfo[name][item]['Duplex'] = m.group(4)
                        intinfo[name][item]['Speed'] = m.group(5)
                        intinfo[name][item]['Media type'] = m.group(6)

                        

            # processes "show CDP neighbors" command or section of sh tech
            if command == 'show cdp neighbors' and name != '':
                # extracts information as per patterns

                m = re.search("^([a-zA-Z0-9][a-zA-Z0-9_\-\.]*)$", line)
                if m:
                    if m.group(1) != "Capability" and m.group(1) != "Device":
                        cdp_neighbor = m.group(1)
                    continue

                m = re.search("^                 (...) (\S+)", line)
                if m and cdp_neighbor != '':

                    local_int = expand(m.group(1), int_types) + m.group(2)
                    remote_int_draft = line[68:-1]

                    tmp = expand(remote_int_draft[:2], int_types)

                    if tmp is not None:
                        remote_int = tmp + remote_int_draft[3:].strip()
                    else:
                        remote_int = remote_int_draft
                        
                    if (name + local_int + remote_int) not in cdpinfo.keys():
                        cdpinfo[name + local_int + remote_int] = collections.OrderedDict()
                    
                    if cdp_neighbor not in cdpinfo[name + local_int + remote_int].keys():
                        cdpinfo[name + local_int + remote_int][cdp_neighbor] = collections.OrderedDict(zip(cdpfields, [''] * len(cdpfields)))
                    
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Name'] = name

                    #splits name and domain, if any
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote device name'] = cdp_neighbor.split('.',1)[0]
                    if len(cdp_neighbor.split('.')) > 1:
                        cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote device domain'] = cdp_neighbor.split('.',1)[1]
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Local interface'] = local_int
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote interface'] = remote_int

                    cdp_neighbor = ''
                    continue

                m = re.search("^([a-zA-Z0-9][a-zA-Z0-9_\-\.]*)\s+(...) ([\d/]+)\s+\d+\s+", line)
                if m:
                    cdp_neighbor = m.group(1)
                    local_int = expand(m.group(2), int_types) + m.group(3)
                    remote_int_draft = line[68:-1]

                    tmp = expand(remote_int_draft[:2], int_types)

                    if tmp is not None:
                        remote_int = tmp + remote_int_draft[3:]
                    else:
                        remote_int = remote_int_draft
                        
                    if (name + local_int) not in cdpinfo.keys():
                        cdpinfo[name + local_int + remote_int] = collections.OrderedDict()
                    
                    if cdp_neighbor not in cdpinfo[name + local_int + remote_int].keys():
                        cdpinfo[name + local_int + remote_int][cdp_neighbor] = collections.OrderedDict(zip(cdpfields, [''] * len(cdpfields)))
                    
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Name'] = name
                    #splits name and domain, if any
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote device name'] = cdp_neighbor.split('.',1)[0]
                    if len(cdp_neighbor.split('.')) > 1:
                        cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote device domain'] = cdp_neighbor.split('.',1)[1]
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Local interface'] = local_int
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote interface'] = remote_int

                    cdp_neighbor = ''


            # processes "show inventory" command
            if command == 'show inventory' and name != '':

                # extracts information as per patterns
                m = re.search('NAME: .* , DESCR: \"(.+)\"', line)
                if m:
                    if (name + item) not in diaginfo.keys():
                        diaginfo[name + item] = collections.OrderedDict(zip(diagfields, [''] * len(diagfields)))
                    diaginfo[name + item]['Name'] = name
                    diaginfo[name + item]['Description'] = m.group(1)

                    continue

                    
                m = re.search('PID: (.*)\s*, VID: .*, SN: (\S+)', line)
                if m and item != '':
                    diaginfo[name + item]['Name'] = name
                    diaginfo[name + item]['Part number'] = m.group(1)
                    diaginfo[name + item]['Serial number'] = m.group(2)

                    continue

            # processes "show CDP neighbors detail" command or section of sh tech
            if command == 'show cdp neighbors detail' and name != '':
                # extracts information as per patterns

                m = re.search("^Device ID: ([a-zA-Z0-9][a-zA-Z0-9_\-\.]*)", line)
                if m:
                    cdp_neighbor = m.group(1)
                    continue

                m = re.search("^  IP address: (.*)", line)
                if m:
                    cdp_ip = m.group(1)
                    continue

                m = re.search("Interface: ([\w\/]+),  Port ID \(outgoing port\): (.*)", line)
                if m:
                    local_int = m.group(1)
                    remote_int = m.group(2)
                    if (name + local_int + remote_int) not in cdpinfo.keys():
                        cdpinfo[name + local_int + remote_int] = collections.OrderedDict()
                    
                    if cdp_neighbor not in cdpinfo[name + local_int + remote_int].keys():
                        cdpinfo[name + local_int + remote_int][cdp_neighbor] = collections.OrderedDict(zip(cdpfields, [''] * len(cdpfields)))
                    
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Name'] = name
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote device'] = cdp_neighbor
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote device name'] = cdp_neighbor.split('.',1)[0]
                    if len(cdp_neighbor.split('.')) > 1:
                        cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote device domain'] = cdp_neighbor.split('.',1)[1]

                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Local interface'] = local_int
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote interface'] = remote_int
                    cdpinfo[name + local_int + remote_int][cdp_neighbor]['Remote device IP'] = cdp_ip

                    cdp_neighbor = ''
                    cdp_ip = ''
                    continue


cont = len(systeminfo.keys())
print(cont, " devices")

if cont > 0:
    with open('system.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(systemfields)

        for name in systeminfo.keys():
            row = [systeminfo[name][field] for field in systemfields]
            writer.writerow(row)

    # Writes interface information
    cont = 0
    for name in intinfo.keys():
        cont = cont + len(intinfo[name])
    print(cont, " interfaces")

    if cont > 0:
        with open('interfaces.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(intfields)

            for name in intinfo.keys():
                for item in intinfo[name].keys():
                    row = [intinfo[name][item][field] for field in intfields]
                    writer.writerow(row)

    # Writes CDP information
    cont = 0
    for name in cdpinfo.keys():
        cont = cont + len(cdpinfo[name])
    print(cont, " neighbors")

    if cont > 0:
        with open('cdp_neighbors.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(cdpfields)

            for name in cdpinfo.keys():
                for item in cdpinfo[name].keys():
                    row = [cdpinfo[name][item][field] for field in cdpfields]
                    writer.writerow(row)

    # Writes show diag information
    cont = len(diaginfo.keys())
    print(cont, " modules")

    if cont > 0:
        with open('modules.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(diagfields)

            for item in diaginfo.keys():
                row = [diaginfo[item][field] for field in diagfields]
                writer.writerow(row)