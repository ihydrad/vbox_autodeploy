from time import sleep
import virtualbox
import folders
import os
import re
from virtualbox.library import NetworkAttachmentType
from tqdm import tqdm
import datetime


target = folders.ovf_file

def timeit(func):
    def wrapper(*args, **kvargs):
        startTime = datetime.datetime.now()
        result = func(*args, **kvargs)
        print("used time:", datetime.datetime.now() - startTime)
        return result
    return wrapper


class HSMDeploy:
    build_pattern = r'\d+\.\d+\.\d\.\d+'

    def __init__(self, ovf_path, prefix='') -> None:
        self.vbox = virtualbox.VirtualBox()
        self._ovf_path = ovf_path
        self.prefix = prefix
        self.hsm_build = ''
        self._machine_name = self.machine_name

    @property
    def machine_name(self) -> str:
        self.ovf_name = os.path.basename(self._ovf_path)
        try:
            self.hsm_build = re.search(self.build_pattern, self.ovf_name)
            self.hsm_build = self.hsm_build.group(0)
        except IndexError:
            self.hsm_build = 'hsm'
        return self.hsm_build + "_" + self.prefix

    @machine_name.setter
    def machine_name(self, name):
        self._machine_name = name

    def wait(self, progress) -> int:
        for i in tqdm(range(100)):
            if progress.completed:
                continue
            while progress.percent > i:
                break
            while progress.percent <= i:
                sleep(0.05)
                if progress.completed:
                    break
        sleep(10)
        if progress.result_code != 0:
            raise Exception(progress.error_info.text)
        else:
            return 1

    def start_appliance(self) -> virtualbox.library.IMachine:
        print("Starting appliance...")
        appliance = self.vbox.create_appliance()
        appliance.read(self._ovf_path)
        appliance.interpret()
        conf_machine = appliance.virtual_system_descriptions[0]
        conf_machine.set_name(self._machine_name)
        progress = appliance.import_machines()
        print("========importing machine:")
        if not self.wait(progress):
            raise ("start_appliance not complete!")
        uuid_machines = appliance.machines
        hsm = self.vbox.find_machine(uuid_machines[0])
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

    @timeit
    def wait_for_load_os(self, session_obj):
        print("\nTarget resolution: 1024px")
        cnt = 0
        while True:
            cnt += 1
            res = session_obj.console.display.get_screen_resolution(0)[0]
            anim_char = ['-', '\\', '|', '/']
            msg = f"Current: {res}px"
            print(anim_char[cnt % 4] + msg, end='\r')
            sleep(0.5)
            if res < 1024:
                continue
            else:
                print("\nLoading complete, ", end='')
                break

    def remove_machine(self, name):
        all_machines = list(map(str, self.vbox.machines))
        if self._machine_name in all_machines:
            hsm = self.vbox.find_machine(name)
            session = hsm.create_session()
            while hsm.state != 1:
                session.console.power_down()
                print("Try power down machine...")
                sleep(5)
            print("Machine is down!")
            print(f"Removing {self._machine_name} machine...")            
            session.unlock_machine()
            hsm.remove()
            return True
        else:
            return 0

    def run(self) -> bool:
        self.remove_machine(self._machine_name)
        hsm = self.start_appliance()
        # start = input("Start guest?(N/y)")
        # if start.lower() == 'n' or start == '':
        #     return 0
        self.configure_machine(hsm)
        sleep(5)
        session = virtualbox.Session()
        progress = hsm.launch_vm_process(session, "gui", [])
        print("\n========starting machine:")
        self.wait(progress)
        self.wait_for_load_os(session)

    # TODO add method for get names of all network adapters
    # TODO add address on the iface hostonly (10.0.2.14)


if __name__ == "__main__":
    hsm_deploy = HSMDeploy(target)
    hsm_deploy.run()
    #  set_net_conf(net_conf)