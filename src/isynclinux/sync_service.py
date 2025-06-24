import os
import time
from shutil import copyfileobj
from pathlib import Path
from shutil import copyfileobj
from pyicloud import PyiCloudService
from os.path import expanduser, isfile
from pyicloud.services.drive import DriveNode
from os import stat

from isynclinux.utils import config_dir


class SyncService:
    def __init__(self, api: PyiCloudService,file_list_cache_file, ignored_folders=[], verbose=False) -> None:
        self.api = api
        self.amount_of_files = 0
        self.drive_size_gb = 0
        self.total_time_taken = 0
        self.verbose = verbose
        self.ignored_folders = ignored_folders
        self.file_list_cache_file = file_list_cache_file
        return None

    def list_files_recursive(self, folder: DriveNode, current_path=""):
        icloud_file_list = []
        start_time = time.time()
        files = folder.get_children()
        end_time = time.time()
        if self.verbose:
            self.total_time_taken += end_time-start_time
            print(f"Processing {current_path} ({end_time - start_time:.5f}s) ({self.total_time_taken:.5f}s)")
        for file in files:
            new_path = f"{current_path}/{file.name}" if current_path else file.name

            if file.type == "folder" or file.type == "app_library":
                if file.name in self.ignored_folders:
                    continue
                files_in_subfolder = self.list_files_recursive(file, new_path)
                icloud_file_list.extend(files_in_subfolder)

            elif file.type == "file":
                icloud_file_list.append(new_path)
                self.amount_of_files = self.amount_of_files + 1
                file_size_gb = (file.size or 0) / 1000 / 1000 / 1000
                if not self.verbose:
                    print(f"\033[32mFound\033[0m {self.amount_of_files} files ({self.drive_size_gb:.4f} Gb)", end="\r")
                self.drive_size_gb = round(self.drive_size_gb + file_size_gb, 4)

        return icloud_file_list

    def sync_icloud_drive_to_disk(self, sync_dir: str) -> int:
        sync_dir = expanduser(sync_dir)

        if self.validate_dir_eligibility(sync_dir) > 0:
            return 1

        root_folder = self.api.drive.root
        if root_folder is None:
            return 1

        icloud_file_list = []
        if isfile(self.file_list_cache_file):
            print("Found cached file list, do you want to use it?")
            if input("y/N: ").lower() == "y":
                icloud_file_list = self.read_cached_file_list()
        if not icloud_file_list:
            icloud_file_list = self.list_files_recursive(root_folder)
            self.cache_file_list(icloud_file_list)
            drive_size_gb = self.drive_size_gb
            print(f"\033[32mFound\033[0m {len(icloud_file_list)} files ({drive_size_gb:.1f} Gb)")

        files_synced = 0

        filler = " "*10
        for file in icloud_file_list:
            files_synced += 1
            folders = file.split("/")

            percent_done = round(files_synced / len(icloud_file_list) * 100, 1)
            if not self.verbose:
                pd = f"({percent_done} %)"
                print(f"\033[32mSyncing\033[0m {files_synced} of {len(icloud_file_list)} {pd} {filler}", end="\r")

            if len(folders) == 1:
                drive_file = root_folder[folders[0]]
                if drive_file:
                    self.write_local_file(drive_file, sync_dir)
            else:
                self.download_file_in_icloud(folders, root_folder, sync_dir)

        print(f"\033[36mSyncing\033[0m completed! {filler}")
        return 0

    def read_cached_file_list(self) -> list[str]:
        try:
            fp =open(self.file_list_cache_file, "r")
            return [file.strip() for file in fp.readlines()]
        except Exception as error:
            print(error)
            print(f"Couldn't open {self.file_list_cache_file}")
            return []


    def cache_file_list(self, files: list[str]):
        try:
            fp =open(self.file_list_cache_file, "w")
            [fp.write(file + "\n") for file in files]
            fp.close()

        except:
            print(f"Couldn't write: {self.file_list_cache_file}")
            return



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

    def download_file_in_icloud(self, folders, root_folder, sync_dir):
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

        try:
            if stat(f"{file_sync_dir}/{drive_file.name}").st_size == drive_file.size:
                return
        except FileNotFoundError:
            pass  # file doesn't exist, download it

        if self.verbose:
            print(f"Syncing {drive_file}")
        self.write_local_file(drive_file, file_sync_dir)

    def write_local_file(self, drive_file, sync_dir):
        local_file_path = sync_dir + "/" + drive_file.name
        if not isfile(local_file_path):
            response = drive_file.open(stream=True)
            file_out = open(sync_dir + "/" + drive_file.name, 'wb')
            copyfileobj(response.raw, file_out)
            file_out.close()
