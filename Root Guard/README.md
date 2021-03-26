# Cisco
Useful python scripts when interacting with Cisco devices.

# Prerequisites
These scripts were written in Python3. Python 3.5.x, 3.6.x, 3.7.x, or 3.8.x required for Pyats.
Script developed a tested on 3.7.9
pip version 20.1.1
netmiko  (3.3.2 tested)
Genie (20.12.2 tested)
Jinja2  (2.11.2 tested)
pandas (1.1.5 tested)
Pyats (20.12 teste)

# Note
Use these at your own risk. I am not responsible for config losses or damage that may occur with the use of these scripts.
Run the root_guard_discovery.py to find ports which are eligible for root guard configuration. root_guard_discovery.py discovers all ports in Designated Role in every VLAN & renders the configuration file using the jinja template. Script should create three (3) files (xx_interface_configs.txt, all_interfaces.csv, and interfaces.csv)

root_guard_conf.py performs pre- deployment check, deploys the configuration file, performs post-deployment check
Tip: Genie package in this script needs the hostname. The hostname is provided in the success message of the first script. 

# Authors
Ryan Newell

# License
This project is licensed under the GNU3 License - see the LICENSE.md file for details

