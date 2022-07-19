import os
import folders
from deploy import HSMDeploy
from HSMhelper import Node
from time import sleep
import argparse


deploy_folder = folders.deploy_folder


class Monitoring:
    def __init__(self, folder) -> None:
        self.folder = folder
        self.taggets = {}

    def get_subfolders(self):
        data = {}
        subfolders = os.listdir(self.folder)
        if subfolders:
            for subfolder in subfolders:
                target_path = os.path.join(self.folder, subfolder)
                out = os.listdir(target_path)
                if out and len(out) == 1:
                    ova_file = out[0]
                    if ova_file.split('.')[-1] == 'ova':
                        data[subfolder] = os.path.join(target_path, ova_file)
                else:
                    continue
        return data

    def remove_ova(self, target):
        print(f"Removing {target}")
        os.remove(target)

    def run(self):
        print("Monitoring started!")
        while True:
            sleep(1)
            self.targets = self.get_subfolders()
            if self.targets:
                sleep(7)
                for ip, ova_path in self.targets.items():
                    print(f'Starting deploy "{os.path.basename(ova_path)}":[{ip}]')
                    try:
                        prefix_name = ip.split('.')[-1]
                    except:
                        prefix_name = ip[-2:]
                    deploy = HSMDeploy(ova_path, prefix_name)
                    deploy.run()
                    sleep(5)
                    node = Node()
                    node.eth0.name = "eth0"
                    node.eth0.address = f"{ip}/24"
                    node.eth0.gateway = "192.168.56.1"
                    node.config.set_net_iface(node.eth0)
                    input("Net conf ok")
                    node.init()
                    self.remove_ova(ova_path)
                self.targets = ''


if __name__ == "__main__":
    monitoring = Monitoring(deploy_folder)
    monitoring.run()
