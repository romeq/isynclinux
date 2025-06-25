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
pipx install . 

# Sync files to ~/iCloud
isynclinux ~/iCloud 
```
