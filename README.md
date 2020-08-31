## Why To Use

ProxLoadMe was created for those people:
* This special kind of people who would like to watch/archive their favorite Animes offline.
* For People who don't have a always perfect/working Internet Access or just want to bulk-download Animes.

## Requirements

### Requirements \*nix

* Install Python3 via your package manager
* Download or Clone this Repo
* Install Dependencies via pip  

```
python3 -m pip install --user -r requirements.txt
```

### Requirements Windows

* Download and Install Python3 from [Python Downloadpage](https://www.python.org/downloads/latest/)  
add Python3 to PATH during installation, install pip alongside and disable Path-Limit
* Download or Clone this Repo
* Install Dependencies via pip

```
python -m pip install --user -r requirements.txt
```

## How to use

### \*nix
* open Terminal, cd to Script-Path, python3 ProxLoadMe.py

>*Exit prematurely via Ctrl + C*

### Windows
Either open Directory in CMD and execute python ProxLoadMe.py or double-click to open:
* open Terminal, cd to Script-Path, python ProxLoadMe.py

>*Exit prematurely via Ctrl + C*

### How ProxLoadMe works

* It will take your Input, parse it and download all relevant Files from Proxer
* After parsing those Files, it will proceed to download the Videofiles
* The Script will quit automatically or you can stop it midway using *Ctrl + C*

>**Note:** *I added time.sleep(5) to prevent the Script from triggering the Chaptcha Mechanism/Bot Detection.  
If you face wierd output somewhat like :  
```IndexError: pop from empty list```,  
please open any Anime Episode on Proxer and solve the Captcha*

>**Note:** *ProxLoadMe requires cloudscraper for handling the cloudflare redirection page, tqdm for progressbars during download, requests for web requests and BeautifulSoup4 for parsing of reqested websites.*

>**Note:** *Additionally I might have added a Download-Limit of 5 to prevent the Script from downloading all Episodes in parallel.  
This Feature can be disabled by changing the Value of LIMIT to some Value fitting for your use.*

```python
LIMIT = 5 #<-------------- YourValueHere
```
