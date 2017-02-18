import os
import multiprocessing
import threading
import time
import subprocess
import ast

def init_preps():
    cwd = os.getcwd() + "/"
    os.chdir(cwd)
    print("Recommended URL-Format would be: http://proxer.me/info/277/\n")
    inputurl = str(input("Please enter the URL of the Anime you want to download: "))
    firstepisode = int(float(input("Please enter the Number of the first Episode you want: ")))
    lastepisode = int(float(input("Please enter the Number of the last Episode you want: ")))

    aninum = inputurl.split("/info/")[1].strip("/")
    infofile = cwd + aninum + ".html"
    if not os.path.isfile(infofile):
        subprocess.check_call(["wget", "-t", "5", "-q", "-O", infofile, inputurl])
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
        print("Creating Worker-Process for Episode " + str(iterator))
        worker = multiprocessing.Process(target=retrieve_source, args=(str(episodeurl), str(name), int(iterator)), daemon=False)
        worker.start()

def get_file(srcfile, srcurl):
    if not os.path.isfile(srcfile):
        subprocess.check_call(["wget", "-t", "5", "-q", "-O", srcfile, srcurl])
        os.chmod(srcfile, 0o666)
    return

def retrieve_source(episodeurl, name, iterator):
    streamhosterlist = []
    episodesrc = os.getcwd() + "/Episode_" + str(iterator) + "-SRC.html"
    getter = threading.Thread(target=get_file, args=(str(episodesrc), str(episodeurl)), daemon=True)
    getter.start()
    while getter.is_alive():
        time.sleep(1)

    with open(episodesrc, "r", encoding="UTF-8") as esrc:
        for line in esrc:
            if  "var streams" in line:
                streamhosterlist = ast.literal_eval(str(line.split("code\":\"")[1].split("\",\"img\"")[0].replace("\":\"", "\",\"").split("\",\"")))
    os.remove(episodesrc)

    streamsrcurl = streamhosterlist.pop(8).replace("\\", "").replace("#", streamhosterlist.pop(0))
    streamsrcfile = os.getcwd() + "/Stream_" + str(iterator) + "-SRC.html"
    setter = threading.Thread(target=get_file, args=(str(streamsrcfile), str(streamsrcurl)), daemon=True)
    setter.start()
    while setter.is_alive():
        time.sleep(1)

    with open(streamsrcfile, "r", encoding="UTF-8") as ssrc:
        for line in ssrc:
            if "\"http" and ".mp4\"" in line:
                streamurl = "http" + str(line.split("\"http")[1].split(".mp4\"")[0]) + ".mp4"
    os.remove(streamsrcfile)

    episode = os.getcwd() + "/" + str(name) + "_Episode_" + str(iterator) + ".mp4"
    better = threading.Thread(target=get_file, args=(str(episode), str(streamurl)), daemon=True)
    better.start()
    while better.is_alive():
        time.sleep(1)

def main():
    os.umask(0)
    init_preps()
main()