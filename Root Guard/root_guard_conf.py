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

from genie.conf import Genie
from netmiko import ConnectHandler
import logging
from genie.abstract import Lookup
from genie.libs import ops
from getpass import getpass
from genie.testbed import load

def get_input(prompt=''):
    try:
        line = raw_input(prompt)
    except NameError:
        line = input(prompt)
    return line

def get_credentials():
    hostname = get_input('Hostname: ')
    ip = get_input('Enter Switch IP: ')
    username = get_input('Enter Username: ')
    password = None
    while not password:
        password = getpass()
        password_verify = getpass('Retype your password: ')
        if password != password_verify:
            print('Passwords do not match. Try again.')
            password = None
    return hostname, ip,username,password

hostname, ip, username, password = get_credentials()

print ("\n ****Collecting Network State on "+ip+"for post verification****")


o =  {"devices":{
                hostname:{
                        "ip":ip,
                        "port": 22,
                        "protocol": "ssh",
                        "username": username,
                        "password": password,
                        "os": "iosxe",
        }
 }}
testbed = load(o)
device=testbed.devices[hostname]
device.connect()
lookup = Lookup(device.os, device.context)
stp = lookup.ops.stp.stp.Stp
STP_before = stp(device)
STP_before.learn()
logging.basicConfig(filename='test.log', level=logging.DEBUG)
logger = logging.getLogger("netmiko")

device1 = {
    "ip": ip,
    "device_type": "cisco_ios",
    "username": username,
    "password": password
}


cfg_file = ip+'_'+'interface_configs.txt'

print ("\n ****Loading Configuraiton on "+ip+"****")

with ConnectHandler(**device1) as net_connect:
    output = net_connect.send_config_from_file(cfg_file)

print(output)
print ("\n ****Loaded Configuraiton on "+ip+"****")
print ("\n ****Performing Diff Check "+ip+"****")

lookup = Lookup(device.os, device.context)
stp_after = lookup.ops.stp.stp.Stp
STP_after = stp_after(device)
STP_after.learn()

print ("\n ****Here is the Diff****")
diff = STP_after.diff(STP_before)
print(diff)


print ("\n ****If Successful, Diff will only include BPDU Counter Increases****")
