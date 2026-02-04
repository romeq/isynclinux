from os.path import expanduser, isdir, isfile
from os import environ, mkdir
from getpass import getpass
from pyicloud.utils import password_exists_in_keyring, store_password_in_keyring

USERNAME_CACHE_FILE = ".cache.username"
FILES_CACHE_FILE = ".cache.files"
IGNORE_FILE = "ignored_folders"


# Returns full path for a config file
def get_config_file(name: str) -> str:
    return f"{config_dir()}/{name}"


def read_file_or_input_and_create(prompt: str, fallback_file: str):
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


def read_ignored_folders(ignore_file) -> list[str]:
    try:
        f = open(ignore_file)
        lines = [x.strip() for x in f.readlines()]
        f.close()
        return lines
    except FileNotFoundError:
        return []


# Ask and potentially save user credinteals
def get_credinteals():
    # username
    username_file = get_config_file(USERNAME_CACHE_FILE)
    username = read_file_or_input_and_create("Email: ", username_file)

    # password
    password_exists = password_exists_in_keyring(username)
    password: str | None = None
    if not password_exists:
        password = getpass(f"Password for {username}: ")
        if input("Would you like to save your password to keychain? (Y/n): ").lower() != "n":
            store_password_in_keyring(username, password)

    return username, password


def ask_yes_or_no(question_string: str, prefer_true: bool) -> bool:
    if prefer_true:
        return input(question_string + "[Y/n]: ").lower() != "n"
    return input(question_string + " [y/N]: ").lower == "y"


def get_env(key: str) -> str:
    try:
        return environ[key]
    except KeyError:
        return ""

def get_env_with_default(key: str, fallback_string: str) -> str:
    primary_kv = get_env(key)
    if primary_kv == "":
        return fallback_string
    return primary_kv

def config_dir() -> str:
    config_dir_path =expanduser(get_env("XDG_CONFIG_HOME")) or expanduser("~/.config")
    dir = f"{config_dir_path}/isynclinux"
    if isdir(dir):
        return dir
    else:
        mkdir(dir)
        return dir
        

