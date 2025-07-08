#!/bin/python3
import sys
import click
from pyicloud import PyiCloudService
import requests
from rich.console import Console
import os
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

@click.group()
def cli() -> None:
    pass

@cli.command()
@click.argument("sync_dir", envvar="ISYNCLINUX_DIR")
@click.option("--verbose", "-v", flag_value=True, envvar="ISYNCLINUX_VERBOSE")
@click.option("--update-files", "-u", flag_value=True)
def sync(sync_dir: str, update_files: bool, verbose: bool):
    richcl = Console(log_time_format="")

    username, password = get_credinteals()

    login_status = richcl.status("Logging in...")
    login_status.start()
    try:
        api = PyiCloudService(username, password)
    except requests.exceptions.ConnectionError:
        login_status.stop()
        richcl.log("[red]No internet connection")
        sys.exit(1)

    try:
        login_status.update("Authenticating 2FA...")
        if authenticate_2fa(api) > 0:
            sys.exit(1)
    except:
        print("Failed to authenticate")
        sys.exit(1)

    login_status.stop()
    richcl.log("[green]Logged in, proceeding...")

    ignored_folders = read_ignored_folders(get_config_file(IGNORE_FILE))
    file_list_cache_file = get_config_file(FILES_CACHE_FILE)

    service = SyncService(api, verbose)
    service.file_list_cache_file = file_list_cache_file
    service.ignored_folders = ignored_folders
    service.update = update_files
    if service.sync_icloud_drive_to_disk(sync_dir) > 0:
        sys.exit(1)

    sys.exit(0)


@cli.command("ignore")
@click.option("--verbose", "-v", flag_value=True, envvar="ISYNCLINUX_VERBOSE")
@click.option("--edit", "-e", flag_value=True)
def ignore(verbose: bool, edit: bool):
    richcl = Console(highlight=False)

    if not edit:
        if verbose: richcl.log("Didn't find edit (-e/--edit) flag, dumping file")
        ignored_folders_file = get_config_file(IGNORE_FILE)
        fp = open(ignored_folders_file)
        [print(ignored_folder_unstripped.strip()) for ignored_folder_unstripped in fp.readlines()]
        return

    default_editor = "nano"
    editor = get_env("EDITOR")
    if verbose: richcl.log(f"$EDITOR => '{editor}'")
    if verbose and not editor: richcl.log(f"Couldn't read $EDITOR, continuing with default editor (={default_editor})")
    if verbose and editor: richcl.log(f"Since $EDITOR exists and is not an empty string, using $EDITOR instead of default ({default_editor})")
    if not editor:
        editor = default_editor

    ignored_folders_file = get_config_file(IGNORE_FILE)
    if verbose: richcl.log(f"Got target file: {ignored_folders_file}")
    if verbose: richcl.log(f"Running '{editor} {ignored_folders_file}'")
    res = os.system(f"{editor} {ignored_folders_file}")
    if verbose: richcl.log(f"Result: {res}")

