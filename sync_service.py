import os
from shutil import copyfileobj
from pathlib import Path
from shutil import copyfileobj
from pyicloud import PyiCloudService
from os.path import expanduser
from os import stat


class SyncService:
    def __init__(self, api: PyiCloudService) -> None:
        self.api = api
        self.amount_of_files = []
        return None

    def list_files_recursive(self, folder, current_path=""):
        icloud_file_list = []
        files = folder.get_children()
        for file in files:
            if file.type == "folder" or file.type == "app_library":
                new_path = f"{current_path}/{file.name}" if current_path else file.name
                files_in_subfolder = self.list_files_recursive(file, new_path)
                icloud_file_list.extend(files_in_subfolder)

            elif file.type == "file":
                file_path = f"{current_path}/{file.name}" if current_path else file.name
                icloud_file_list.append(file_path)
                self.amount_of_files.append(1)
                print("\033[32mFound\033[0m {} files\t".format(
                    sum(self.amount_of_files)), end="\r")

        return icloud_file_list

    def sync_icloud_drive_to_disk(self, sync_dir: str) -> int:
        sync_dir = expanduser(sync_dir)

        if self.validate_dir_eligibility(sync_dir) > 0:
            return 1

        root_folder = self.api.drive.root
        if root_folder is None:
            return 1

        icloud_file_list = self.list_files_recursive(root_folder, "")
        print(f"\033[32mFound\033[0m total of {len(icloud_file_list)} files\t")

        files_synced = 0

        for file in icloud_file_list:
            files_synced += 1
            folders = file.split("/")

            percent_done = round(files_synced / len(icloud_file_list) * 100, 1)
            print(
                f"\t\033[32mSyncing\033[0m {files_synced} of {len(icloud_file_list)} ({percent_done}%)\t", end="\r")

            if len(folders) == 1:
                drive_file = root_folder[folders[0]]
                if drive_file:
                    self.save_file(drive_file, sync_dir)
            else:
                self.download_file_in_directory(folders, root_folder, sync_dir)

        print(
            f"\t\033[36mSyncing\033[0m completed!")
        return 0

    def validate_dir_eligibility(self, sync_dir) -> int:
        if sync_dir == "":
            print("No sync directory specified")
            return 1
        elif sync_dir == "/":
            print("Cannot sync to root")
            return 1
        elif not os.path.isdir(sync_dir):
            print("Sync path does not exist or is not a directory")
            return 1
        return 0

    def save_file(self, drive_file, sync_dir):
        response = drive_file.open(stream=True)
        file_out = open(sync_dir + "/" + drive_file.name, 'wb')
        copyfileobj(response.raw, file_out)
        file_out.close()

    def download_file_in_directory(self, folders, root_folder, sync_dir):

        file_parent_folders = folders[:len(folders) - 1]
        current_folder = root_folder

        subdir_to_create = "/".join(file_parent_folders)
        file_sync_dir = "/".join([sync_dir, subdir_to_create])

        Path(file_sync_dir).mkdir(parents=True, exist_ok=True)

        for folder in file_parent_folders:
            tmp_current = current_folder[folder]
            if not tmp_current:
                continue
            current_folder = tmp_current

        filename = folders[len(folders) - 1]
        drive_file = current_folder[filename]
        if not drive_file:
            return

        file_name = f"{file_sync_dir}/{drive_file.name}"
        try:
            if stat(file_name).st_size == drive_file.size:
                return
        except FileNotFoundError:
            pass  # file doesn't exist, download it

        response = drive_file.open(stream=True)
        file_out = open(file_name, 'wb')
        copyfileobj(response.raw, file_out)
        file_out.close()
