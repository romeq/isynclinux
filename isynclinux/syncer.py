#!/bin/python3
from os import getenv
from os.path import isfile
import sys
import click
from pyicloud import PyiCloudService
from .sync_service import SyncService
from .utils import *


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


def main() -> int:
    is_password_saved_to_keyring = get_env("PYICLOUD_PASSWORD") != ""
    username, password = get_credinteals(is_password_saved_to_keyring)

    if is_password_saved_to_keyring:
        api = PyiCloudService(username)
    else:
        api = PyiCloudService(username, password)

    try:
        if authenticate_2fa(api) > 0:
            return 1
    except:
        print("Failed to authenticate")
        return 1

    sync_dir = expanduser(getenv("ICLOUD_SYNC_DIR") or "~/iCloud-sync")
    if len(sys.argv) > 1:
        sync_dir = sys.argv[1]

    
    ignored_folders = read_ignored_folders(get_config_file(IGNORE_FILE))
    file_list_cache_file = get_config_file(".cache.files")

    service = SyncService(api, file_list_cache_file, ignored_folders, getenv("ISYNCLINUX_VERBOSE")=="1")
    if service.sync_icloud_drive_to_disk(sync_dir) > 0:
        return 1

    return 0


if __name__ == "__main__":
    status_code = main()
    sys.exit(status_code)
