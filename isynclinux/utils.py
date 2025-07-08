from os.path import expanduser, isdir, isfile
from os import environ, mkdir
from getpass import getpass

USERNAME_CACHE_FILE = ".cache.username"
FILES_CACHE_FILE = ".cache.files"
IGNORE_FILE = "ignored_folders"

def get_input_or_fallback_file(prompt: str, fallback_file: str):
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


def get_credinteals():
    username_file = get_config_file(USERNAME_CACHE_FILE)
    username = get_input_or_fallback_file("Email: ", username_file)
    return username, getpass(f"Password for {username}: ") if not isfile(username_file) else "-"


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
        

def get_config_file(name: str) -> str:
    return f"{config_dir()}/{name}"
