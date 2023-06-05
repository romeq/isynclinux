from os.path import expanduser
from os import environ
from getpass import getpass

USERNAME_CACHE_FILE = expanduser("~/.username")


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
