#!/bin/python3
import sys
import click
from pyicloud import PyiCloudService
from rich.console import Console
from .sync_service import SyncService
from .utils import *


def authenticate_2fa(api: PyiCloudService) -> int:
    if api.requires_2fa:
        code = input("Enter the code you received in one of your approved devices: ")
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

# TODO: Click options
@click.command()
@click.argument("sync_dir", envvar="ISYNCLINUX_DIR")
@click.option("--update", "-u", flag_value=True)
@click.option("--verbose", "-v", flag_value=True, envvar="ISYNCLINUX_VERBOSE")
def main(sync_dir: str, update: bool, verbose: bool) -> int:
    richcl = Console()

    username, password = get_credinteals()

    login_status = richcl.status("Logging in...")
    login_status.start()
    api = PyiCloudService(username, password)
    login_status.stop()
    richcl.log("[green]Logged in, proceeding...")

    try:
        if authenticate_2fa(api) > 0:
            sys.exit(1)
    except:
        print("Failed to authenticate")
        sys.exit(1)

    ignored_folders = read_ignored_folders(get_config_file(IGNORE_FILE))
    file_list_cache_file = get_config_file(".cache.files")

    service = SyncService(api, verbose)
    service.file_list_cache_file = file_list_cache_file
    service.ignored_folders = ignored_folders
    service.update = update
    if service.sync_icloud_drive_to_disk(sync_dir) > 0:
        sys.exit(1)

    sys.exit(0)

