import os
import time
from shutil import copyfileobj
from pathlib import Path
from shutil import copyfileobj
from typing import Optional
import click
from pyicloud import PyiCloudService
from os.path import expanduser, isfile
from pyicloud.services.drive import DriveNode
from os import stat

from rich.console import Console


class SyncService:
    def __init__(self, api: PyiCloudService,verbose=False) -> None:
        self.api = api
        self._amount_of_files = 0
        self._drive_size_gb = 0
        self._total_time_taken = 0
        self.verbose = verbose
        self.ignored_folders: list[str] = [] 
        self.file_list_cache_file: Optional[str] = None
        self.richcl = Console(log_time_format="", highlighter=None)
        self.update = False
        return None


    def list_files_recursive(self, folder: DriveNode, current_path="", status=None):
        icloud_file_list = []
        if self.verbose:
            start_time = time.time()
            files = folder.get_children()
            end_time = time.time()
            self._total_time_taken += end_time-start_time
            self.richcl.log(f"Processing {current_path} ({end_time - start_time:.5f}s) ({self._total_time_taken:.5f}s)")
        else:
            files = folder.get_children()

        for file in files:
            new_path = f"{current_path}/{file.name}" if current_path else file.name
            if file.type == "folder" or file.type == "app_library":
                if file.name in self.ignored_folders:
                    continue
                files_in_subfolder = self.list_files_recursive(file, new_path, status)
                icloud_file_list.extend(files_in_subfolder)

            elif file.type == "file":
                icloud_file_list.append(new_path)
                self._amount_of_files = self._amount_of_files + 1
                file_size_gb = (file.size or 0) / 1000 / 1000 / 1000
                self._drive_size_gb = round(self._drive_size_gb + file_size_gb, 4)
                if status:
                    status.update(f"[green]Found {self._amount_of_files} files ({self._drive_size_gb}Gb), continuing...")

        return icloud_file_list


    def sync_icloud_drive_to_disk(self, sync_dir: str) -> int:
        sync_dir = expanduser(sync_dir)

        if self.validate_dir_eligibility(sync_dir) > 0:
            return 1

        root_folder = self.api.drive.root
        if root_folder is None:
            return 1

        icloud_file_list = []
        if isfile(self.file_list_cache_file or ""):
            if click.confirm("Found cached file list, do you want to use it?"):
                icloud_file_list = self.read_cached_file_list()

        if not icloud_file_list:
            status = self.richcl.status("[green]Finding files...")
            status.start()

            try:
                icloud_file_list = self.list_files_recursive(root_folder, status=status)
            except KeyboardInterrupt:
                status.stop()
                self.richcl.log("Stopping! ")
                return 1

            self.cache_file_list(icloud_file_list)
            status.stop()
            self.richcl.log(f"[green]Found {len(icloud_file_list)} files ({self._drive_size_gb:.3f} Gb)")
        else:
            icloud_file_list = self.read_cached_file_list()

        files_synced = 0
        new_files_downloaded = 0
        status = self.richcl.status(f"[lightblue]Syncing files...")
        status.start()
        for file in icloud_file_list:
            files_synced += 1
            folders = file.split("/")

            percent_done = round(files_synced / len(icloud_file_list) * 100, 1)
            pd = f"{percent_done}%"
            status.update(f"[blue]Syncing {files_synced}/{len(icloud_file_list)} ({pd} done) '{file}'")

            if len(folders) == 1:
                drive_file = root_folder[folders[0]]
                if drive_file:
                    new_files_downloaded += self.write_local_file(drive_file, sync_dir)
            else:
                new_files_downloaded += self.download_file_in_icloud(folders, root_folder, sync_dir)

        status.stop()
        if new_files_downloaded == 0:
            self.richcl.log(f"[green]You are already in sync! Use '--update' to download changes to existing files.")
        else:
            if self.update:
                self.richcl.log(f"[green]Update completed! {new_files_downloaded} files are now up-to-date.")
            else:
                self.richcl.log(f"[green]Syncing completed! Downloaded {new_files_downloaded} new files.")
        return 0

    def read_cached_file_list(self) -> list[str]:
        try:
            fp =open(self.file_list_cache_file or "", "r")
            return [file.strip() for file in fp.readlines()]
        except Exception:
            self.richcl.log(f"Couldn't open {self.file_list_cache_file}")
            return []


    def cache_file_list(self, files: list[str]):
        try:
            fp =open(self.file_list_cache_file or "", "w")
            [fp.write(file + "\n") for file in files]
            fp.close()

        except:
            self.richcl.log(f"Couldn't write: {self.file_list_cache_file}")
            return



    def validate_dir_eligibility(self, sync_dir) -> int:
        if sync_dir == "":
            self.richcl.log("No sync directory specified")
            return 1
        elif sync_dir == "/":
            self.richcl.log("Cannot sync to root")
            return 1
        elif not os.path.isdir(sync_dir):
            self.richcl.log("Sync path does not exist or is not a directory")
            return 1
        return 0

    def download_file_in_icloud(self, folders, root_folder, sync_dir) -> int:
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
            return 0

        try:
            if stat(f"{file_sync_dir}/{drive_file.name}").st_size == drive_file.size and not self.update:
                return 0
        except FileNotFoundError:
            pass  # file doesn't exist, download it

        return self.write_local_file(drive_file, file_sync_dir)


    def write_local_file(self, drive_file, sync_dir) -> int:
        local_file_path = sync_dir + "/" + drive_file.name
        if not isfile(local_file_path) or self.update:
            response = drive_file.open(stream=True)
            file_out = open(sync_dir + "/" + drive_file.name, 'wb')
            copyfileobj(response.raw, file_out)
            file_out.close()
            return 1
        else:
            return 0
