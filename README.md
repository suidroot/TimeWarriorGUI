# TimeWarriorGUI

This is a script to provide a simple GUI to the TimeWarrior CLI application, allowing to add and stop time trackers.

Features
* Allows to start, stop, rename, coninue and delete tasks
* Rename tag on a task
* Integration with [iCalBuddy](https://hasseg.org/icalBuddy/) to simplify Meeting tracking on Macs

Limitation
* Does not support multiple tags on a task, will only uses first Tag on a task as name


![image](https://user-images.githubusercontent.com/520237/119217929-363ace00-bae6-11eb-83f8-5017f2329ad0.png)

## Install and Run

1. You need PySimpleGUI:
```bash
pip3 install PySimpleGUI
```
2. Clone current version or download release
3. To execute run following command from location of files
```
python3 tw-gui.py
```
