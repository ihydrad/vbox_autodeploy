__version__ = "0.0.1"

from time import sleep
import virtualbox
import const
import os
import re
from HSMhelper import Node
from virtualbox.library import NetworkAttachmentType
from tqdm import tqdm

target = const.ovf_file
net_conf = {
        "addr": "192.168.56.11",
        "mask": "255.255.255.0",
        "gw": "192.168.56.1"
        }


def set_net_conf(conf):
    cnt = 30
    print("Try connect to machine...", end='')
    sleep(5)
    while cnt:
        cnt -= 1
        try:
            print(".", end='')
            hsm_ssh = Node(hsm_deploy.start_hsm_ip)
        except:
            continue
        if hsm_ssh.config.eth0_set(conf):
            print("Complete! Rebooting...")
            hsm_ssh.config.reboot()
            return 1
    return 0


class HSMDeploy:
    __buld_pattern = r'\d+\.\d+\.\d\.\d+'
    start_hsm_ip = "10.0.2.15"

    def __init__(self, ovf_path, ip) -> None:
        self._ovf_path = ovf_path
        self.ip_addr = ip
        self.hsm_build = ''
        self._machine_name = self.machine_name

    @property
    def machine_name(self) -> str:
        self.ovf_name = os.path.basename(self._ovf_path)
        try:
            self.hsm_build = re.search(self.__buld_pattern, self.ovf_name)
            self.hsm_build = self.hsm_build.group(0)
        except IndexError:
            self.hsm_build = 'hsm'
        return self.hsm_build + '_' + self.ip_addr.split('.')[-1]

    @machine_name.setter
    def machine_name(self, name):
        self._machine_name = name

    def wait(self, progress) -> int:
        for i in tqdm(range(100)):
            if progress.canceled:
                print("Canceled")
                return 0
            while progress.percent > i:
                break
            while progress.percent <= i:
                sleep(0.05)
        return 1

    def start_appliance(self, vbox_obj) -> virtualbox.library.IMachine:
        print("Starting appliance...")
        appliance = vbox_obj.create_appliance()
        appliance.read(self._ovf_path)
        appliance.interpret()
        conf_machine = appliance.virtual_system_descriptions[0]
        conf_machine.set_name(self._machine_name)
        progress = appliance.import_machines()
        print("========importing machine:")
        if not self.wait(progress):
            raise ("start_appliance not complete!")
        uuid_machines = appliance.machines
        hsm = vbox_obj.find_machine(uuid_machines[0])
        print("\nMachine name:", hsm)
        return hsm

    def configure_machine(self, machine):
        session_conf = machine.create_session()
        hsm_tmp = session_conf.machine
        eth0 = hsm_tmp.get_network_adapter(0)
        eth0.host_only_interface = "VirtualBox Host-Only Ethernet Adapter"
        eth0.attachment_type = NetworkAttachmentType["host_only"]
        eth0.mac_address = "0800272bf921"
        hsm_tmp.save_settings()
        session_conf.unlock_machine()

    def wait_for_load_os(self, session_obj):
        print("\nWaiting for resolution 1024px(full loaded system):")
        while True:
            res = session_obj.console.display.get_screen_resolution(0)[0]
            print(f"Current display resolution: {res}px", end='\r')
            sleep(5)
            if res < 1024:
                continue
            else:
                print("\nLoad OS is complete!")
                break

    def run(self) -> bool:
        vbox = virtualbox.VirtualBox()
        try:
            hsm = vbox.find_machine(self._machine_name)
            session = hsm.create_session()
            while hsm.state != 1:
                session.console.power_down()
                print("Try power down machine...")
                sleep(5)
            print("Machine is power down!")
            print(f"Removing {self._machine_name} machine...")
            hsm.remove()
            session.unlock_machine()
        except:
            hsm = self.start_appliance(vbox)
        self.configure_machine(hsm)
        sleep(5)
        session_scr = virtualbox.Session()
        progress = hsm.launch_vm_process(session_scr, "gui", [])
        print("\n========starting machine:")
        self.wait(progress)
        self.wait_for_load_os(session_scr)

    # TODO add method for get names of all network adapters
    # TODO add address on the iface hostonly (10.0.2.14)


if __name__ == "__main__":
    hsm_deploy = HSMDeploy(target, net_conf["addr"])
    hsm_deploy.run()
    #set_net_conf(net_conf)

