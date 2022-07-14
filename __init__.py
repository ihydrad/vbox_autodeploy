__version__ = "0.0.1"

from time import sleep
import virtualbox

ovf_file = r'D:\soft\IT\forTest\dev\infotecs-hsm-3.3.0.1876-an-va-tdn-dsdr-dbg.ova'

def print_pecent(progress):
    print("Complete: ")
    while progress.percent != 100:
        print(f"{progress.percent}%", end='\r')
        sleep(1)
    print(f"{progress.percent}%")

vbox = virtualbox.VirtualBox()
ovf = vbox.create_appliance()
ovf.read(ovf_file)
progress = ovf.import_machines()
print("Importing machine:")
print_pecent(progress)
uuid_machines = ovf.machines
machine = vbox.find_machine(uuid_machines[0])
print("Deployed machine:", machine)
session = machine.create_session()
session.unlock_machine()
sleep(5)
progress = machine.launch_vm_process(session, "gui", [])
print("Starting machine:")
print_pecent(progress)