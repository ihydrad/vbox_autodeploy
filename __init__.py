__version__ = "0.0.1"

from ast import pattern
from lib2to3.pgen2.token import NAME
from time import sleep
import virtualbox
from virtualbox.library import VirtualSystemDescriptionType
import const
import os
import re

target = const.ovf_file
ip = '172.16.187.11'
NAME_VM_ID_DESC = 3
type_name_desc = VirtualSystemDescriptionType(NAME_VM_ID_DESC)

def print_pecent(progress):
    print("Complete: ")
    while progress.percent != 100:
        print(f"{progress.percent}%", end='\r')
        sleep(1)
    print(f"{progress.percent}%")

def get_ver_ovf_machine(full_path):
    pat = r'\d+\.\d+\.\d\.\d+'
    name = os.path.basename(full_path)
    return re.search(pat, name).group(0)

def get_last_ip_octet(ip_addr):
    return ip_addr.split('.')[-1]

def build_name():
    return get_ver_ovf_machine(target) + '_' + \
        get_last_ip_octet(ip)

def deploy(target, name):
    vbox = virtualbox.VirtualBox()
    ovf = vbox.create_appliance()
    ovf.read(target)
    ovf.interpret()    
    ovf_descriptions = ovf.virtual_system_descriptions[0]
    ovf_descriptions.remove_description_by_type(type_name_desc)
    ovf_descriptions.add_description(type_name_desc, name, '')
    progress = ovf.import_machines()
    print("========importing machine:")
    print_pecent(progress)
    uuid_machines = ovf.machines
    machine = vbox.find_machine(uuid_machines[0])
    session = machine.create_session()
    session.unlock_machine()
    sleep(5)
    progress = machine.launch_vm_process(session, "gui", [])
    print("========starting machine:")
    print_pecent(progress)

if __name__ == "__main__":
    deploy(target, build_name())