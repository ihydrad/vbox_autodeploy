__version__ = "0.0.1"

from time import sleep
import virtualbox
import const
import os
import re

target = const.ovf_file
ip = '172.16.187.11'  

def percent(progress):
    print("Complete: ")
    while progress.percent != 100:
        sleep(0.1)
        print(f"{progress.percent}%", end='\r')
        if progress.canceled:
            print("Canceled")
            return 0
    return 100

def get_ver_ovf_machine(full_path):
    pat = r'\d+\.\d+\.\d\.\d+'
    name = os.path.basename(full_path)
    return re.search(pat, name).group(0)

def get_last_ip_octet(ip_addr):
    return ip_addr.split('.')[-1]

def build_name(target_path, ip_macchine):
    return get_ver_ovf_machine(target_path) + '_' + \
        get_last_ip_octet(ip_macchine)

def set_adapter_1(conf, type_iface):
    desc = conf.get_description()
    vbox_values, extra_config = desc[3:]
    extra_config = list(extra_config)    
    extra_config[8]  = f'type={type_iface}'
    en = [True for _ in range(len(extra_config))]
    conf.set_final_values(en, list(vbox_values), extra_config)

def deploy(target):
    name = build_name(target, ip)
    vbox = virtualbox.VirtualBox()
    ovf = vbox.create_appliance()
    ovf.read(target)
    ovf.interpret()  
    conf_machine = ovf.virtual_system_descriptions[0]
    conf_machine.set_name(name)
    set_adapter_1(conf_machine, "Bridged")
    progress = ovf.import_machines()
    print("========importing machine:")
    if not percent(progress):
        return 0 
    uuid_machines = ovf.machines
    machine = vbox.find_machine(uuid_machines[0])
    session = machine.create_session()
    session.unlock_machine()
    sleep(5)
    progress = machine.launch_vm_process(session, "gui", [])
    print("========starting machine:")
    if not percent(progress):
        return 0

if __name__ == "__main__":
    deploy(target)