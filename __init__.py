__version__ = "0.0.1"

from time import sleep
import virtualbox
import const
import os
import re
from HSMhelper import Node
from virtualbox.library import NetworkAttachmentType

target = const.ovf_file
net_conf = {
        "ip_addr": "192.168.43.11",
        "mask": "255.255.255.0",
        "gw": "192.168.43.1"
        }


class HSMDeploy:
    __buld_pattern = r'\d+\.\d+\.\d\.\d+'
    start_hsm_ip = "10.0.2.15"

    def __init__(self, ovf_path, ip) -> None:
        self._ovf_path = ovf_path
        self.ip_addr = ip
        self._machine_name = self.machine_name
        try:
            self.hsm_build = re.search(self.__buld_pattern, self.ovf_name)
            self.hsm_build = self.hsm_build.group(0)
        except:
            self.hsm_build = 'hsm'

    @property
    def machine_name(self):
        self.ovf_name = os.path.basename(self._ovf_path)
        return self.ovf_name + self.ip_addr.split('.')[-1]

    @machine_name.setter
    def machine_name(self, name):
        self._machine_name = name

    def wait(self, progress):
        print("Complete: ")
        while progress.percent != 100:
            sleep(0.1)
            print(f"{progress.percent}%", end='\r')
            if progress.canceled:
                print("Canceled")
                return 0
        return 100

    def run(self):
        vbox = virtualbox.VirtualBox()
        appliance = vbox.create_appliance()
        appliance.read(self._ovf_path)
        appliance.interpret()
        conf_machine = appliance.virtual_system_descriptions[0]
        conf_machine.set_name(self._machine_name)
        progress = appliance.import_machines()
        print("========importing machine:")
        if not self.wait(progress):
            return 0
        uuid_machines = appliance.machines
        hsm = vbox.find_machine(uuid_machines[0])
        session = hsm.create_session()
        hsm_tmp = session.machine
        eth0 = hsm_tmp.get_network_adapter(0)
        eth0.host_only_interface = "VirtualBox Host-Only Ethernet Adapter"
        eth0.attachment_type = NetworkAttachmentType["host_only"]
        eth0.mac_address = "0800272bf921"
        hsm_tmp.save_settings()
        session.unlock_machine() 
        sleep(5)
        progress = hsm.launch_vm_process(session, "gui", [])
        print("========starting machine:")
        if not self.wait(progress):
            return 0

    # TODO add method for get names of all network adapers


if __name__ == "__main__":
    hsm_deploy = HSMDeploy(target, net_conf["ip_addr"])
    hsm_deploy.run()
    n15 = Node(hsm_deploy.start_hsm_ip)
    if n15.config.eth0_set(net_conf):
        print("Complete!")
        n15.config.reboot()
