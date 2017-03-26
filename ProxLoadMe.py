"""Script to Download Anime Episodes from Proxer.me"""
import os
import threading
import multiprocessing
import time
import subprocess
import ast
import requests

CURRTHREADS = multiprocessing.Value("i", 0)
LIMIT = 5

def init_preps():
    """Function to initiate the Download Process"""
    cwd = os.getcwd() + "/" 
    os.chdir(cwd)
    print("Recommended URL-Format would be: http://proxer.me/info/277/\n")
    inputurl = str(input("Please enter the URL of the Anime you want to download: "))
    inputurl = "http://proxer.me/info/277/"
    firstepisode = int(float(input("Please enter the Number of the first Episode you want: ")))
    lastepisode = int(float(input("Please enter the Number of the last Episode you want: ")))

    aninum = inputurl.split("/info/")[1].strip("/").replace("\n", "")
    infofile = cwd + aninum + ".html"
    get_file(infofile, inputurl)
    with open(infofile, "r", encoding="UTF-8") as ifile:
        for line in ifile:
            if "<title>" in line:
                name = line.split(" - ")[0].strip("<title>")

    os.remove(infofile)
    animedir = cwd + name + "/"
    if not os.path.exists(animedir):
        os.mkdir(animedir)
        os.chmod(animedir, 0o775)

    os.chdir(animedir)
    inputurl = inputurl.replace("info", "watch")
    if inputurl[-1:] != "/":
        inputurl = inputurl + "/"

    for iterator in range(firstepisode, lastepisode + 1):
        episodeurl = inputurl + str(iterator) + "/engsub"
        print(episodeurl)
        print("Creating Worker-Process for Episode " + str(iterator))
        CURRTHREADS.value = CURRTHREADS.value + 1
        worker = multiprocessing.Process(target=retrieve_source, args=(str(episodeurl), str(name), int(iterator), CURRTHREADS), daemon=False)
        worker.start()
        time.sleep(5)
        while CURRTHREADS.value == LIMIT:
            time.sleep(1)

def get_file(srcfile, srcurl):
    """Function to Download"""
    time.sleep(5)
    header = requests.utils.default_headers()
    header.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36"})
    if not os.path.isfile(srcfile):
        with open(srcfile, "wb") as fifo:#open in binary write mode
            response = requests.get(srcurl, headers=header)#get request
            fifo.write(response.content)#write to file
    return

def retrieve_source(episodeurl, name, iterator, CURRTHREADS):
    """Function to make all the Magic happen"""
    streamhosterlist = []
    episodesrc = os.getcwd() + "/Episode_" + str(iterator) + "-SRC.html"
    print(episodesrc)
    getter = threading.Thread(target=get_file, args=(str(episodesrc), str(episodeurl)), daemon=False)
    getter.start()
    while getter.is_alive():
        time.sleep(1)

    with open(episodesrc, "r", encoding="UTF-8") as esrc:
        for line in esrc:
            if  "var streams" in line:
                print(line)
                streamhosterlist = ast.literal_eval(str(line.split("code\":\"")[1].split("\",\"img\"")[0].replace("\/", "/").replace("//", "http://").replace("\":\"", "\",\"").split("\",\"")))
    os.remove(episodesrc)

    for x in streamhosterlist:
        print(x)

    streamsrcurl = streamhosterlist.pop(8).replace("#", streamhosterlist.pop(0))
    print(streamsrcurl)
    streamsrcfile = os.getcwd() + "/Stream_" + str(iterator) + "-SRC.html"
    setter = threading.Thread(target=get_file, args=(str(streamsrcfile), str(streamsrcurl)), daemon=False)
    setter.start()
    while setter.is_alive():
        time.sleep(1)

    with open(streamsrcfile, "r", encoding="UTF-8") as ssrc:
        for line in ssrc:
            if "\"http" and ".mp4\"" in line:
                streamurl = "http" + str(line.split("\"http")[1].split(".mp4\"")[0]) + ".mp4"
    os.remove(streamsrcfile)

    episode = os.getcwd() + "/" + str(name) + "_Episode_" + str(iterator) + ".mp4"
    if not os.path.isfile(episode):
        better = threading.Thread(target=get_file, args=(str(episode), str(streamurl)), daemon=False)
        better.start()
        while better.is_alive():
            time.sleep(1)
    CURRTHREADS.value = CURRTHREADS.value - 1
    return

def main():
    """MAIN"""
    os.umask(0)
    init_preps()
main()
