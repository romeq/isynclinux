# isynclinux

> **Note**  
> This repository is work-in-progress, and only supports downloading for now.
> Updates are expected when I have free time.


A simple (SLOC ~ 220) syncer for iCloud on Linux platforms.


## Motivation

I couldn't find such program online so I created my own with PyiCloud

## Features
- [x] Download currently existing version
- [ ] Upload files
- [ ] Handle files/directories that don't exist on server anymore
- [ ] Automatic syncing (either event-based or by looping)
- [ ] Virtual files support
- [ ] For some reason the file discovery is slow as hell, so try to share the work between multiple threads

## Installation

```sh
git clone git@github.com:romeq/isynclinux && cd isynclinux
pip install -r requirements.txt

# Save password to keyring (optional)
# If you don't save it you'll have to enter it everytime
icloud --username=<your icloud email>
# only export this variable if the password is in keyring
# it might be a good idea to add this line to .bashrc
export PYICLOUD_PASSWORD=true 

# Sync files to ~/iCloud
./main.py ~/iCloud 
```
