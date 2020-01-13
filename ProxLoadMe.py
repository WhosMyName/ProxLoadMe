"""Script to Download Anime Episodes from Proxer.me"""

import os
import sys
import time
import logging
import re
from datetime import datetime

from configparser import ConfigParser
from bs4 import BeautifulSoup, SoupStrainer
import requests
import concurrent.futures as cf 

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

LOGGER = logging.getLogger('udli.main')
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

def get_file(srcfile, srcurl, counter=0, ftype=0):  # ftype indicates if video or not
    """Function to Downloadad and verify downloaded Files"""
    if counter == 5:
        LOGGER.info("Could not download File: {srcfile} in 5 attempts")
        return 1
    counter = counter + 1
    if not os.path.isfile(srcfile):
        time.sleep(5)
        LOGGER.info(f"Downloading {srcurl} as {srcfile}")
        with open(srcfile, "wb") as fifo:  # open in binary write mode
            response = requests.get(srcurl, headers=HEADERS)  # get request
            # check against actual filesize
            LOGGER.debug(f"\n\n\n {response.headers} \n\n\n")
            fifo.write(response.content)  # write to file
        if int(str(os.path.getsize(srcfile)).strip(
                "L")) < 25000000 and ftype:  # Assumes Error in Download and redownlads File
            LOGGER.info("Redownloading {srcurl} as {srcfile}")
            return get_file(srcfile, srcurl, counter)
        else:  # Assume correct Filedownload
            return 0
    else:
        if int(str(os.path.getsize(srcfile)).strip(
                "L")) < 25000000 and ftype:  # Assumes Error in Download and redownlads File
            LOGGER.info(f"{srcfile} was already downloaded but the filesize does not seem to fit -> Redownl0ading")
            return get_file(srcfile, srcurl, 0)
        else:  # Assume correct Filedownload
            LOGGER.info("File was downloaded correctly on a previous run")
            return 0

def init_preps():
    """Function to initiate the Download Process"""

    config = ConfigParser()
    try:
        config.read(AUTHFILE)
        user = config["LOGIN"]["USER"]
        passwd = config["LOGIN"]["PASS"]
        #LOGGER.info("%s, %s" % (user, passwd))
        resp = SESSION.get("https://proxer.me")
        strainer = SoupStrainer(id="loginBubble")
        soup = BeautifulSoup(resp.content, "html.parser", parse_only=strainer)
        url = soup.find("form")["action"]
        creds = {"username": user, "password":passwd, "remember":1}
        resp2 = SESSION.post(url, data=creds)
    except Exception as excp:
        LOGGER.exception(excp)

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

    resp = SESSION.get(inputurl)
    strainer = SoupStrainer(class_="fn")
    soup = BeautifulSoup(resp.content, "html.parser", parse_only=strainer)
    name = soup.string

    animedir = f"{CWD}{name}{SLASH}"
    if not os.path.exists(animedir):
        os.mkdir(animedir)

    os.chdir(animedir)
    inputurl = inputurl.replace("info", "watch")
    if inputurl[-1:] != "/":
        inputurl = f"{inputurl}/"

    ftrlst = []

    for iterator in range(firstepisode, lastepisode + 1):
        episodeurl = f"{inputurl}{iterator}/engsub"
        LOGGER.debug(episodeurl)
        LOGGER.info(f"Creating Worker for Episode {iterator}")
        
        ftrlst.append(EXECUTOR.submit(retrieve_source, episodeurl, name, iterator))

    for future in cf.as_completed(ftrlst):
        try:
            video = future.done()
            LOGGER.info(f"{future} produced return {video}")
        except Exception as excp:
            LOGGER.exception(
                "%s has thrown Exception:\n%s", supposed_video, excp)


def retrieve_source(episodeurl, name, episodenum):
    """Function to make all the Magic happen"""
    #LOGGER.info(f"{episodeurl}, {name}, {episodenum}")
    streamhosterurl = None
    resp = SESSION.get(episodeurl)

    for line in resp.text.split("\n"):
        if "var streams" in line:
            #LOGGER.info(line.split("[{")[1].split("}];")[0].split("},{"))
            for streamhoster in line.split("[{")[1].split("}];")[0].split("},{"):
                elem = streamhoster.split("code\":\"")[1].split("\",\"img\"")[0].replace(
                    r"\/", "/").replace("//", "").replace("\":\"", "\",\"").split("\",\"")
                code = str(elem[0])
                baseurl = f"{elem[8]}".replace("#", code)
                if "http" not in baseurl:
                    baseurl = f"http://{baseurl}" 
                #LOGGER.info(f"Streamurls: {baseurl}")
                if "proxer" in baseurl:
                    streamhosterurl = baseurl
    #LOGGER.info(f"Streamhoster: {streamhosterurl}")

    resp2 = SESSION.get(streamhosterurl)
    for line in resp2.text.split("\n"):
        if "\"http" and ".mp4\"" in line:
            streamurl = f"http{line.split('http')[1].split('.mp4')[0]}.mp4"
            episodename = f"{os.getcwd()}{SLASH}{name}_Episode_{episodenum}.mp4"
            #LOGGER.info(f"Streamurl: {streamurl}")
            get_file(episodename, streamurl, 0, 1)


def __main__():
    """MAIN"""
    #os.umask(0)
    init_preps()

if __name__ == "__main__":
    __main__()
