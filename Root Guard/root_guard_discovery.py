# Copyright 2020, Cisco Systems, Inc.
# All Rights Reserved.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from netmiko import ConnectHandler
from jinja2 import Template
import pandas as pd
import csv
from getpass import getpass

def get_input(prompt=''):
    try:
        line = raw_input(prompt)
    except NameError:
        line = input(prompt)
    return line

def get_credentials():
    ip = get_input('Enter Switch IP: ')
    username = get_input('Enter Username: ')
    password = None
    while not password:
        password = getpass()
        password_verify = getpass('Retype your password: ')
        if password != password_verify:
            print('Passwords do not match. Try again.')
            password = None
    return ip,username,password

ip, username, password = get_credentials()

device = {
    "ip": ip,
    "device_type": "cisco_ios",
    "username": username,
    "password": password
}

with ConnectHandler(**device) as net_connect:
    stp_details = net_connect.send_command("show spanning-tree", use_genie=True)
    switchports = net_connect.send_command("show interfaces switchport", use_genie=True)
    hostname = net_connect.send_command("show run | in hostname")

interface_file = "all_interfaces.csv"
report_fields = ["Interface", "Role", "State"]
script_defined_role ='0_designated'
script_defined_state ='shutdown'

with open(interface_file, "w") as f:
    writer = csv.DictWriter(f, report_fields)
    writer.writeheader()

    for mode,details in stp_details.items():
         vlan_list = stp_details[mode]['vlans']
         for vlan, info in vlan_list.items():
             info = vlan_list[vlan]['interfaces']
             for interface,detail in info.items():
                 role = info[interface]['role']
                 state = info[interface]['port_state']
                 writer.writerow(
                    {"Interface": interface,
                    "Role": role,
                    "State": state
                    })

    for ports in switchports:
        writer.writerow(
           {"Interface": ports,
           "Role": script_defined_role,
           "State": script_defined_state
           })


#remove duplicate interfaces that may exist because of per VLAN STP
#there maybe multiple entries for an interface
#this will sort the interfaces by interface and Role
#it will keep the last entry of the sorted entries
#root or alternative
interfaces_1=pd.read_csv("all_interfaces.csv")
interfaces_2=interfaces_1.sort_values(["Interface","State"],ascending=False)
interfaces_3=interfaces_2.drop_duplicates(subset=['Interface'], keep='last')
interfaces_3.to_csv("interfaces.csv")


##use .csv w/o duplicates and render cfg using jinja2 template
source_file = "interfaces.csv"
interface_template_file = "jinja.j2"
interface_configs = ""

with open(interface_template_file) as f:
    interface_template = Template(f.read(),keep_trailing_newline=True)

with open(source_file) as f:
    reader = csv.DictReader(f)
    for row in reader:
        interface_config = interface_template.render(
            interface = row["Interface"],
            role = row["Role"]
        )
        interface_configs += interface_config

with open(ip+"_"+"interface_configs.txt", "w") as f:
  f.write(interface_configs)

print ("\n File "+ip+"_interface_configs.txt created succesfully for "+hostname)
