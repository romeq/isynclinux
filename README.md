# isynclinux

A simple (SLOC ~ 220)


> **Note**  
> This repository is work-in-progress!



Sync your iCloud to a Linux folder 

## Installation

```sh
git clone git@github.com:romeq/isynclinux && cd isynclinux
pip install -r requirements.txt

# Save password to keyring (optional)
# If you don't save it you'll have to enter it everytime
icloud --username=<your icloud email>
export PYICLOUD_PASSWORD=true # only export this variable if the password is in keyring

# Sync files to ~/iCloud
./main.py ~/iCloud 
```
