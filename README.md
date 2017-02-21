## Why To Use

ProxLoadMe was created for those people:
* This special kind of people who would like to watch/archive their favorite Animes offline.
* For People who don't have a always perfect/working Internet Access or just want to bulk-download Animes.

## Requirements

### Requirements \*nix

* Install Python3 via your package manager
* Install wget via your package manager (you should seriously have this pre-installed)
* Download or Clone this Repo

### Requirements Windows

* Download and Install Python3 from [Python Downloadpage](https://www.python.org/downloads/release/python-360/)  
add Python3 to PATH during installation and disable Path-Limit
* Download wget from [Wget Downloadpage](https://eternallybored.org/misc/wget/)  
Unpack the downloaded Archive and move Content to SysWoW64 and System32
* Download or Clone this Repo

## How to use

### \*nix
Open Directory in Terminal
Execute the Shell Scripts:
* run_proxload.sh -> Recommended
* open Terminal, cd to Script-Path, python3 ProxLoadMe.py

>*Exit via Ctrl + C*

### Windows
Either open Directory in CMD and execute python ProxLoadMe.py or
Execute the Shell Scripts:
* run_proxload.bat -> Recommended
* open Terminal, cd to Script-Path, python3 ProxLoadMe.py

>*Exit via Ctrl + C*

### How ProxLoadMe works

* It will take your Input, parse it and download all relevant Files from Proxer
* After parsing those Files, it will poroceed to download the Videofiles
* It will quit automatically or you can, if you want stop it midway using *Ctrl + C*

>**Note:** *I added time.sleep(5) to prevent the Script from triggering the Chaptcha Mechanism/Bot Detection.  
If you face wierd output somewhat like :  
```IndexError: pop from empty list```,  
please open any Anime Episode on Proxer and solve the Chaptch*

>**Note:** *Additionally I might have added a Download-Limit of 5 to prevent the Script from downloading all Episodes in parallel.  
This Feature can be disabled by changing the Value of LIMIT to some Value fitting for your use.*

```python
LIMIT = 5 <-------------- YourValueHere
```