# isynclinux

> **Note**  
> This repository is work-in-progress, and only supports downloading for now.
> Updates are expected when I have free time.


A simple (SLOC ~ 220) syncer for iCloud on Linux platforms.


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

# Add `.git` to ignored folders (e.g. don't sync git to local device). Ignored folders are seperated by newlines (\n).
mkdir -p ~/.config/isynclinux
echo ".git" > ~/.config/isynclinux/ignored_folders

# Sync your iCloud to ~/iCloud
isynclinux ~/iCloud
```
