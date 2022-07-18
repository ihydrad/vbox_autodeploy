import os
import const
from deploy import HSMDeploy
from HSMhelper import Node
from time import sleep
import argparse


deploy_folder = const.deploy_folder
net_conf = {
        "addr": "192.168.56.11",
        "mask": "255.255.255.0",
        "gw": "192.168.56.1"
        }


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

    def defclear_targets(self):
        for ova in self.taggets.values():
            os.remove(ova)

    def run(self):
        while True:
            sleep(5)
            self.targets = self.get_subfolders()
            if self.targets:
                for ip, ova_path in self.targets.items():
                    print(f'Starting deploy "{os.path.basename(ova_path)}":[{ip}]')
                    deploy = HSMDeploy(ova_path, ip)
                    deploy.run()
                    sleep(5)
                    node = Node()
                    node.config.eth0_set(net_conf)
                    node.reboot()
                self.clear_targets()


if __name__ == "__main__":
    monitoring = Monitoring(deploy_folder)
    monitoring.run()
