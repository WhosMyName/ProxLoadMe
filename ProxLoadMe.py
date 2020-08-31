""" Script to Download Anime Episodes from Proxer.me """

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
import tqdm
from cloudscraper import CloudScraper

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

class NoURLError(Exception):
    pass

def download_file(srcfile, srcurl):
    """ Function to Downloadad and verify downloaded Files """
    response = SESSION.get(srcurl, stream=True)# get request, stream data
    content_length = int(response.headers['content-length'] or 0) # unfortunately this returns a string, easy conversion or 0
    if os.path.exists(srcfile) and os.path.getsize(srcfile) < content_length: # check if there was an previously correctly downloaded file
        os.remove(srcfile)
    LOGGER.debug(f"Downloading {srcurl} as {srcfile}")
    with open(srcfile, "wb") as fifo:# open in binary write mode
        if content_length == 0: # check if unusable, no conversion needed
            fifo.write(response.content)#write to file
        else: # write with progressbar
            progbar = tqdm.tqdm(total=content_length, unit_scale=True, desc=srcfile.split(SLASH)[len(srcfile.split(SLASH)) - 1], unit="bytes")
            progbar.get_lock()
            for chunk in response.iter_content(4096): # iterate the response, writing to file and updating the progressbar
                fifo.write(chunk)
                progbar.update(len(chunk))
            progbar.close()

def init_preps():
    """ Function to log in and initiate the Download Process """

    config = ConfigParser()
    try: # safely try to read login credentials and log into proxer
        config.read(AUTHFILE)
        user = config["LOGIN"]["USER"]
        passwd = config["LOGIN"]["PASS"]
        #LOGGER.info(f"{user}|{passwd}")
        scraper = CloudScraper() # use Cloudscraper to bypass Cloudflares Redirection Page
        resp = scraper.get("https://proxer.me") # grab the main page
        strainer = SoupStrainer(id="loginBubble") # restrict to login related html using a strainer
        soup = BeautifulSoup(resp.content, "html.parser", parse_only=strainer) # use the strainer to restrict parsing
        url = soup.find("form")["action"] # grab the login url
        creds = {"username": user, "password": passwd, "remember": 1} # set credentials (remember is irrelevant, due to this being a singular session)
        resp2 = SESSION.post(url, data=creds) # hopefully logged in correctly
    except Exception as excp:
        LOGGER.exception(excp)
        LOGGER.warning(f"Something went wrong during Login!\nExiting...")
        exit(1)

    LOGGER.info("Recommended URL-Format would be: http://proxer.me/info/277/\n")
    inputurl = input("Please enter the URL of the Anime you want to download: ")
    #inputurl = "https://proxer.me/info/6587"#cm
    firstepisode = int(
        input("Please enter the Number of the first Episode you want: ") or 1)
    lastepisode = int(
        input("Please enter the Number of the last Episode you want: ") or 1)

    if lastepisode <= firstepisode: # check for fishy episode requests
        lastepisode = firstepisode
    resp = SESSION.get(inputurl) # grab the anime page
    strainer = SoupStrainer(class_="fn") # let's restrict the area for our name search, to the exact element
    soup = BeautifulSoup(resp.content, "html.parser", parse_only=strainer)
    name = soup.string.replace(":", "-") # win compat qwq

    animedir = f"{CWD}{name}{SLASH}"
    if not os.path.exists(animedir): # create anime directory
        os.mkdir(animedir)

    os.chdir(animedir)
    match = search("#.*", inputurl) # check if the url contains unwanted resource descriptors
    if match is None:
        match = ""
    else:
        match = match[0] # there's a reason behind the urls scheme recommendation, if there's more than 1 match user should learn to read
    inputurl = inputurl.strip(match).replace("info", "watch") # make sure it's the correct url (lazy)
    if inputurl[-1:] != "/": # verify that "/" is the last char
        inputurl = f"{inputurl}/"

    futurelist = []
    for episodenum in range(firstepisode, lastepisode + 1):
        episodeurl = f"{inputurl}{episodenum}/engsub" # force the scrubs to enjoy engsub
        LOGGER.debug(episodeurl)
        LOGGER.debug(f"Creating Worker for Episode {episodenum}")
        futurelist.append(EXECUTOR.submit(retrieve_source, episodeurl, name, episodenum))

    for future in cf.as_completed(futurelist): # check for thread status
        try:
            video = future.done() # cf equivalent of threading.Thread.join()
            LOGGER.debug(f"Worker for Episode {episodenum} returned: {video}")
        except Exception as excp:
            LOGGER.exception(
                f"{supposed_video} has thrown Exception:\n{excp}")


def retrieve_source(episodeurl, name, episodenum):
    """ Function to make all the Magic happen, parses the streamhoster url [Proxer] and parses the video url """
    try: # if anything fails in here, it's prolly the captcha
        #LOGGER.info(f"{episodeurl}, {name}, {episodenum}")
        streamhosterurl = None
        resp = SESSION.get(episodeurl, timeout=30) # grab the specific episode

        for line in resp.text.split("\n"):
            if "var streams" in line:
                #LOGGER.info(line.split("[{")[1].split("}];")[0].split("},{"))
                for streamhoster in line.split("[{")[1].split("}];")[0].split("},{"): # parses all available stream hoster
                    elem = streamhoster.split("code\":\"")[1].split("\",\"img\"")[0].replace("//", "").replace(r"\/", "/").replace("\":\"", "\",\"").split("\",\"")
                    code = str(elem[0])
                    baseurl = f"{elem[8]}".replace("#", code)
                    if "http" not in baseurl:
                        baseurl = f"http://{baseurl}" 
                    #LOGGER.info(f"Streamurls: {baseurl}")
                    if "proxer" in baseurl: # we'll just use proxer tho
                        streamhosterurl = baseurl
        LOGGER.info(f"Streamhoster: {streamhosterurl}")

        if streamhosterurl == None:
            raise NoURLError

        resp2 = SESSION.get(streamhosterurl, timeout=30) # grabbing the page where the video is embedded in
        for line in resp2.text.split("\n"):
            if "\"http" and ".mp4\"" in line: # parsing the video url from that half-crappy js
                streamurl = f"http{line.split('http')[1].split('.mp4')[0]}.mp4"
                episodename = f"{os.getcwd()}{SLASH}{name}_Episode_{episodenum}.mp4"
                #LOGGER.info(f"Streamurl: {streamurl}")
                if streamurl == "": # verify this check!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!11
                    raise NoURLError()
                download_file(episodename, streamurl)
    except Exception as excp:
        LOGGER.exception(f"{excp}")

def __main__():
    """ MAIN """
    init_preps()

if __name__ == "__main__": # main guard
    __main__()
