#!/bin/python3
from getpass import getpass
import os
from shutil import copyfileobj
import sys
from pathlib import Path
import click
from shutil import copyfileobj
from pyicloud import PyiCloudService
from os.path import expanduser
from os import environ, stat

USERNAME_CACHE_FILE = ".username"


def get_input_or_fallback_file(prompt, fallback_file):
    try:
        f = open(fallback_file, "r")
        username = f.read()
        f.close()
    except FileNotFoundError:
        username = input(prompt)

        f = open(fallback_file, "w")
        f.write(username)
        f.close()

    return username


def get_credinteals(password_already_saved: bool):
    username = get_input_or_fallback_file("Email: ", USERNAME_CACHE_FILE)
    if password_already_saved:
        return username, ""
    return username, getpass(f"Password for {username}: ")


def ask_yes_or_no(question_string: str, prefer_true: bool) -> bool:
    if prefer_true:
        return input(question_string + "[Y/n]: ").lower() != "n"
    return input(question_string + " [y/N]: ").lower == "y"


def get_env(key: str) -> str:
    try:
        return environ[key]
    except KeyError:
        return ""


def authenticate_2fa(api: PyiCloudService) -> int:
    if api.requires_2fa:
        code = input(
            "Enter the code you received in one of your approved devices: ")
        result = api.validate_2fa_code(code)

        if not result:
            print("Failed to verify security code")
            return 1

        if not api.is_trusted_session:
            print("Session is not trusted. Requesting trust...")
            result = api.trust_session()

            if not result:
                print(
                    "Failed to request trust. You will likely be prompted for the code again in the coming weeks")

        devices = api.trusted_devices
        for i, device in enumerate(devices):
            print(
                "  %s: %s" % (i, device.get('deviceName',
                                            "SMS to %s" % device.get('phoneNumber')))
            )

        device = click.prompt('Which device would you like to use?', default=0)
        device = devices[device]
        if not api.send_verification_code(device):
            print("Failed to send verification code")
            return 1

        code = click.prompt('Please enter validation code')
        if not api.validate_verification_code(device, code):
            print("Failed to verify verification code")
            return 1

    return 0


amount_of_files = []


def list_files_recursive(folder, current_path=""):
    icloud_file_list = []
    files = folder.get_children()
    for file in files:
        if file.type == "folder" or file.type == "app_library":
            new_path = f"{current_path}/{file.name}" if current_path else file.name
            files_in_subfolder = list_files_recursive(file, new_path)
            icloud_file_list.extend(files_in_subfolder)

        elif file.type == "file":
            file_path = f"{current_path}/{file.name}" if current_path else file.name
            icloud_file_list.append(file_path)
            amount_of_files.append(1)
            print("\033[32mFound\033[0m {} files\t".format(
                sum(amount_of_files)), end="\r")

    return icloud_file_list


def sync_icloud_files_to(api: PyiCloudService, sync_dir: str) -> int:
    sync_dir = expanduser(sync_dir)
    if sync_dir == "":
        print("No sync directory specified")
        return 1
    elif sync_dir == "/":
        print("Cannot sync to root")
        return 1
    elif not os.path.isdir(sync_dir):
        print("Sync path does not exist or is not a directory")
        return 1

    # Retrieve the root folder from iCloud Drive
    root_folder = api.drive.root
    if root_folder is None:  # if root folder is empty
        return 1

    icloud_file_list = list_files_recursive(root_folder, "")
    print()

    files_synced = 0

    f = open("icloud-file-list.txt", "w")
    f.write("\n".join(icloud_file_list))
    f.close()

    for file in icloud_file_list:
        files_synced += 1
        path_split = file.split("/")

        percent_done = round(files_synced / len(icloud_file_list) * 100, 2)
        print(
            f"\033[32mSyncing\033[0m {files_synced} of {len(icloud_file_list)} ({percent_done}%)\t", end="\r")

        # If the file is in the root folder
        if len(path_split) == 1:
            drive_file = root_folder[path_split[0]]
            if not drive_file:
                continue

            response = drive_file.open(stream=True)
            file_out = open(sync_dir + "/" + drive_file.name, 'wb')
            copyfileobj(response.raw, file_out)
            file_out.close()

            continue

        file_parent_folders = path_split[:len(path_split) - 1]
        current_folder = api.drive.root

        subdir_to_create = "/".join(file_parent_folders)
        file_sync_dir = "/".join([sync_dir, subdir_to_create])

        Path(file_sync_dir).mkdir(parents=True, exist_ok=True)

        for folder in file_parent_folders:
            tmp_current = current_folder[folder]
            if not tmp_current:
                continue
            current_folder = tmp_current

        filename = path_split[len(path_split) - 1]
        drive_file = current_folder[filename]
        if not drive_file:
            continue

        file_name = f"{file_sync_dir}/{drive_file.name}"
        try:
            if stat(file_name).st_size == drive_file.size:
                continue
        except FileNotFoundError:
            pass  # file doesn't exist, download it

        response = drive_file.open(stream=True)
        file_out = open(file_name, 'wb')
        copyfileobj(response.raw, file_out)
        file_out.close()
    return 0


def main() -> int:
    has_password_been_saved_to_keyring = get_env("PYICLOUD_PASSWORD") != ""
    username, password = get_credinteals(has_password_been_saved_to_keyring)

    if has_password_been_saved_to_keyring:
        api = PyiCloudService(username)
    else:
        api = PyiCloudService(username, password)

    if authenticate_2fa(api) > 0:
        return 1

    sync_dir = expanduser("~/.icloud-sync")
    if len(sys.argv) > 1:
        sync_dir = sys.argv[1]

    if sync_icloud_files_to(api, sync_dir) > 0:
        return 1
    print("\n\033[32mSyncing\033[0m succeeded!")

    return 0


if __name__ == "__main__":
    status_code = main()
    sys.exit(status_code)
