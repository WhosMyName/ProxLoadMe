"""Script to Download Anime Episodes from Proxer.me"""

import os
import sys
import time
import logging
import re
import concurrent.futures as cf 
from datetime import datetime
from configparser import ConfigParser
from re import search

import requests
from bs4 import BeautifulSoup, SoupStrainer

# SEARCH FOR # TO FIND ALL COMMENTS

AUTHFILE = "login.auth"

HEADERS = requests.utils.default_headers()
HEADERS.update(
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36", })

if os.name == "nt":
    SLASH = "\\"
else:
    SLASH = "/"
CWD = os.path.dirname(os.path.realpath(__file__)) + SLASH

LOGGER = logging.getLogger('plme.main')
LOG_FORMAT = "%(asctime)-15s | %(levelname)s | %(module)s %(name)s %(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(message)s"
LOGGER.setLevel(logging.DEBUG)
STRMHDLR = logging.StreamHandler(stream=sys.stdout)
STRMHDLR.setLevel(logging.INFO)
STRMHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
FLHDLR = logging.FileHandler("error.log", mode="a", encoding="utf-8", delay=False)
FLHDLR.setLevel(logging.DEBUG)
FLHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(STRMHDLR)
LOGGER.addHandler(FLHDLR)

LIMIT = 5
SESSION = requests.Session()
EXECUTOR = cf.ThreadPoolExecutor(LIMIT)

def ask_overwrite(filename):
    """ asks if a file sould be overwritten """
    retval = input(f"The file {filename} already exists...\nSould it be overwritten?\n[y/n]")
    if retval == "n":
        return False
    return True

def download_file(srcfile, srcurl):
    """Function to Downloadad and verify downloaded Files"""
    if os.path.exists(srcfile):
        if not ask_overwrite(srcfile):
            return False
    LOGGER.info(f"Downloading {srcurl} as {srcfile}")
    with open(srcfile, "wb") as fifo:#open in binary write mode
        response = SESSION.get(srcurl)#get request
        fifo.write(response.content)#write to file
    return True

def init_preps():
    """Function to log in and initiate the Download Process"""

    config = ConfigParser()
    try:
        config.read(AUTHFILE)
        user = config["LOGIN"]["USER"]
        passwd = config["LOGIN"]["PASS"]
        #LOGGER.info(f"{user}|{passwd}")
        resp = SESSION.get("https://proxer.me")
        strainer = SoupStrainer(id="loginBubble")
        soup = BeautifulSoup(resp.content, "html.parser", parse_only=strainer)
        url = soup.find("form")["action"]
        creds = {"username": user, "password":passwd, "remember":1}
        resp2 = SESSION.post(url, data=creds)
    except Exception as excp:
        LOGGER.exception(excp)
        LOGGER.warning(f"Something went wrong during Login!\nExiting...")
        exit(1)

    LOGGER.info("Recommended URL-Format would be: http://proxer.me/info/277/\n")
    inputurl = str(
        input("Please enter the URL of the Anime you want to download: "))
    #inputurl = "https://proxer.me/info/6587"#cm
    firstepisode = int(
        float(
            input("Please enter the Number of the first Episode you want: ") or 1))
    lastepisode = int(
        float(
            input("Please enter the Number of the last Episode you want: ") or 1))

    if lastepisode <= firstepisode:
        lastepisode = firstepisode
    resp = SESSION.get(inputurl)
    strainer = SoupStrainer(class_="fn")
    soup = BeautifulSoup(resp.content, "html.parser", parse_only=strainer)
    name = soup.string

    animedir = f"{CWD}{name}{SLASH}"
    if not os.path.exists(animedir):
        os.mkdir(animedir)

    os.chdir(animedir)
    match = search("#.*", inputurl)
    if match is None:
        match = ""
    else:
        match = match[0]
    inputurl = inputurl.strip(match).replace("info", "watch")
    if inputurl[-1:] != "/":
        inputurl = f"{inputurl}/"

    ftrlst = []

    for episodenum in range(firstepisode, lastepisode + 1):
        episodeurl = f"{inputurl}{episodenum}/engsub"
        LOGGER.debug(episodeurl)
        LOGGER.info(f"Creating Worker for Episode {episodenum}")
        
        ftrlst.append(EXECUTOR.submit(retrieve_source, episodeurl, name, episodenum))

    for future in cf.as_completed(ftrlst):
        try:
            video = future.done()
            LOGGER.info(f"Worker for Episode {episodenum} returned: {video}")
        except Exception as excp:
            LOGGER.exception(
                f"{supposed_video} has thrown Exception:\n{excp}")


def retrieve_source(episodeurl, name, episodenum):
    """Function to make all the Magic happen"""
    #LOGGER.info(f"{episodeurl}, {name}, {episodenum}")
    streamhosterurl = None
    resp = SESSION.get(episodeurl, timeout=30)

    for line in resp.text.split("\n"):
        if "var streams" in line:
            #LOGGER.info(line.split("[{")[1].split("}];")[0].split("},{"))
            for streamhoster in line.split("[{")[1].split("}];")[0].split("},{"):
                elem = streamhoster.split("code\":\"")[1].split("\",\"img\"")[0].replace("//", "").replace(r"\/", "/").replace("\":\"", "\",\"").split("\",\"")
                code = str(elem[0])
                baseurl = f"{elem[8]}".replace("#", code)
                if "http" not in baseurl:
                    baseurl = f"http://{baseurl}" 
                #LOGGER.info(f"Streamurls: {baseurl}")
                if "proxer" in baseurl:
                    streamhosterurl = baseurl
    #LOGGER.info(f"Streamhoster: {streamhosterurl}")

    resp2 = SESSION.get(streamhosterurl, timeout=30)
    for line in resp2.text.split("\n"):
        if "\"http" and ".mp4\"" in line:
            streamurl = f"http{line.split('http')[1].split('.mp4')[0]}.mp4"
            episodename = f"{os.getcwd()}{SLASH}{name}_Episode_{episodenum}.mp4"
            #LOGGER.info(f"Streamurl: {streamurl}")
            if streamurl == "": # error check for captcha
                return False
            if not download_file(episodename, streamurl):
                return False # error check for file previously downloaded/failed ?

def __main__():
    """MAIN"""
    init_preps()

if __name__ == "__main__":
    __main__()
