# isynclinux

> **Note**  
> This repository is work-in-progress, and only supports downloading for now.
> Updates are expected when I have free time.


A simple (SLOC < 300) syncer for iCloud on Linux platforms.

## Motivation

I couldn't find such program online so I created my own with PyiCloud

## Features
- [x] Download current iCloud drive to a specific directory
- [x] Respect `XDG_CONFIG_HOME`
- [ ] Upload files
- [ ] Remove files/directories that don't exist on server anymore
- [ ] Automatic syncing (either event-based or by looping)
- [ ] Virtual files support
- [ ] For some reason the file discovery is slow as hell, so try to share the work between multiple threads

## Installation and usage

Install using [pipx](https://github.com/pypa/pipx)

```sh
pipx install git+https://github.com/romeq/isynclinux.git

# Ignoring folders from sync
# - Option 1: Edit using CLI
isynclinux ignore -e
# - Option 2: Manual
mkdir -p ~/.config/isynclinux
echo ".git" > ~/.config/isynclinux/ignored_folders

# Syncing your iCloud to ~/iCloud
isynclinux sync ~/iCloud
```

## Caveats
- Running `isynclinux ignore -e` reads the EDITOR environment variable and uses `os.system` to edit the file. EDITOR is not parsed to preserve the ability to run editors with custom flags and one may for example try to execute a custom application by running `EDITOR=\"./mydeviousapp; cat\" isynclinux ignore -e`. If $EDITOR envvar can't be found, `nano` is used as default editor.
