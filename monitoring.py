import os
import const
from deploy import HSMDeploy


deploy_folder = const.deploy_folder


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

    def run(self):
        self.targets = self.get_subfolders()
        for ip, ova_path in self.targets.items():
            print(f'Starting deploy "{os.path.basename(ova_path)}":[{ip}]')
            deploy = HSMDeploy(ova_path, ip)
            deploy.run()


if __name__ == "__main__":
    monitoring = Monitoring(deploy_folder)
    monitoring.run()
