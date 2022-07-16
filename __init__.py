__version__ = "0.0.1"

from time import sleep
import virtualbox
import const
import os
import re
from HSMhelper import Node

target = const.ovf_file
ip = '172.16.187.11'  

net_conf = {
        "addr":"192.168.43.11",
        "mask":"255.255.255.0",
        "gw":"192.168.43.1"
        } 

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
    set_adapter_1(conf_machine, "hostOnly")
    progress = ovf.import_machines()
    print("========importing machine:")
    if not percent(progress):
        return 0 
    uuid_machines = ovf.machines
    hsm = vbox.find_machine(uuid_machines[0])
    # создаем сессию с правами записи
    tmp = hsm.create_session()
    # получаем изменяемую копию машины
    hsm_tmp = tmp.machine
    eth0 = hsm_tmp.get_network_adapter(0)
    eth0.mac_address = "0800272bf921"
    # коммитим изменения машины
    hsm_tmp.save_settings()
    # освобождаем доступ к машине
    tmp.unlock_machine()    
    sleep(5)
    progress = hsm.launch_vm_process(tmp, "gui", [])
    print("========starting machine:")
    if not percent(progress):
        return 0

def wait_resp(hostname, del_s):
    cnt = 0
    while True:
        if del_s == cnt:
            return 0
        sleep(1)
        cnt+=1
        response = os.system("ping -n 1 " + hostname)
        if response == 0:
            return 1

if __name__ == "__main__":
    def_ip = "10.0.2.15"
    deploy(target)
    #wait_resp(def_ip, 100)
    sleep(100)
    n15 = Node(def_ip)
    if n15.config.eth0_set(net_conf):
        print("Complete!")
        n15.config.reboot()
    