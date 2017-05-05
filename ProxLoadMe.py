"""Script to Download Anime Episodes from Proxer.me"""
import os
import threading
import multiprocessing
import time
import tempfile
import requests

#SEARCH FOR # TO FIND ALL COMMENTS

CURRTHREADS = multiprocessing.Value("i", 0)
LIMIT = 5
HEADERS = requests.utils.default_headers()
HEADERS.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",})
SUPPORTEDOSTER = ["proxer", "streamcloud", "mp4upload", "bitvid", "auroravid"]


if os.name == "nt":
    SLASH = "\\"
else:
    SLASH = "/"

def get_file(srcfile, srcurl, counter=0, ftype=0):#ftype indicates if video or not
    """Function to Downloadad and verify downloaded Files"""
    time.sleep(5)
    if not os.path.isfile(srcfile):
        print("Downloading", srcurl, "as", srcfile)
        counter = counter + 1
        with open(srcfile, "wb") as fifo:#open in binary write mode
            response = requests.get(srcurl, headers=HEADERS)#get request
            fifo.write(response.content)#write to file
        if int(str(os.path.getsize(srcfile)).strip("L")) < 25000000 and ftype: #Assumes Error in Download and redownlads File
            print("Redownloading", srcurl, "as", srcfile)
            autocleanse(srcfile)
            return get_file(srcfile, srcurl, counter)
        else: #Assume correct Filedownload
            return 0
    else:
        if int(str(os.path.getsize(srcfile)).strip("L")) < 25000000 and ftype: #Assumes Error in Download and redownlads File
            print(srcfile, "was already downloaded but the filesize does not seem to fit -> Redownl0ading")
            autocleanse(srcfile)
            return get_file(srcfile, srcurl, 0)
        else: #Assume correct Filedownload
            return 0

def autocleanse(cleansefile):
    """ Function for safer deleting of files """
    if os.path.exists(cleansefile):
        os.remove(cleansefile)
        return
    else:
        return

def init_preps():
    """Function to initiate the Download Process"""
    cwd = os.getcwd() + SLASH
    os.chdir(cwd)
    print("Recommended URL-Format would be: http://proxer.me/info/277/\n")
    inputurl = str(input("Please enter the URL of the Anime you want to download: "))
    #inputurl = "http://proxer.me/info/277/"
    firstepisode = int(float(input("Please enter the Number of the first Episode you want: ")))
    lastepisode = int(float(input("Please enter the Number of the last Episode you want: ")))

    aninum = inputurl.split("/info/")[1].strip("/").replace("\n", "")
    infofile = cwd + aninum + ".html"
    get_file(infofile, inputurl)
    with open(infofile, "r", encoding="UTF-8") as ifile:
        for line in ifile:
            if "<title>" in line:
                name = line.split(" - ")[0].strip("<title>")

    autocleanse(infofile)
    animedir = cwd + name + SLASH
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
        print("Creating Worker-Process for Episode " +str(iterator))
        CURRTHREADS.value = CURRTHREADS.value + 1
        worker = multiprocessing.Process(target=retrieve_source, args=(str(episodeurl), str(name), str(iterator), CURRTHREADS), daemon=False)
        worker.start()
        time.sleep(5)
        while CURRTHREADS.value == LIMIT:
            time.sleep(1)

def retrieve_source(episodeurl, name, iterator, currthreads):
    """Function to make all the Magic happen"""
    streamhosterlist = []
    episodesrc = os.getcwd() + SLASH + "Episode_" + iterator + "-SRC.html"
    print(episodesrc)
    getter = threading.Thread(target=get_file, args=(str(episodesrc), str(episodeurl)), daemon=False)
    getter.start()
    while getter.is_alive():
        time.sleep(1)

    with open(episodesrc, "r", encoding="UTF-8") as esrc:
        for line in esrc:
            if  "var streams" in line:
                print(line.split("[{")[1].split("}];")[0].split("},{"))
                for streamhoster in line.split("[{")[1].split("}];")[0].split("},{"):
                    elem = streamhoster.split("code\":\"")[1].split("\",\"img\"")[0].replace(r"\/", "/").replace("//", "http://").replace("\":\"", "\",\"").split("\",\"")
                    print(elem)
                    if "http" in elem[8]:
                        baseurl = str(elem[8]).replace("http:", "").replace("//", "")
                        code = str(elem[0])
                        url = "http://" + baseurl.replace("#", code)
                        print(url)
                        streamhosterlist.append(url)
    autocleanse(episodesrc)

    for url in streamhosterlist:
        found = 0
        print(url)
        for hoster in SUPPORTEDOSTER:
            print(hoster)
            if hoster in url:
                found = 1
                print("Valid Hoster", hoster, "in URL:", url)
                break
        if not found:
            streamhosterlist.remove(url)
            if os.path.exists("DEBUG.txt"):
                with open("DEBUG.txt", "a") as dbg:
                    print("Debug Messge: Unknown Hoster ", url)
                    dbg.write("Debug Message: Unknown Hoster " + str(url) + "\n")
            else:
                with open("DEBUG.txt", "w") as dbg:
                    print("Debug Messge: Unknown Hoster ", url)
                    dbg.write("Debug Message: Unknown Hoster " + str(url) + "\n")

            for hoster in streamhosterlist:
                hoster = str(hoster)
                print("\n\nHoster: ", hoster, "\n\n")
                switcher = parse_file(hoster, name, currthreads, iterator)
                print("Evaluation:", switcher)
                if switcher == 0:
                    return

def parse_file(hoster, name, currthreads, iterator):
    """ Function that does the actual parsing and downloading """
    streamsrcfile = str(os.getcwd() + SLASH + "Stream_" + iterator + "-SRC.html")
    autocleanse(streamsrcfile)
    setter = threading.Thread(target=get_file, args=(streamsrcfile, hoster), daemon=False)
    setter.start()
    while setter.is_alive():
        time.sleep(1)

    with open(streamsrcfile, "r", encoding="UTF-8") as ssrc:
        if "proxer" in hoster:
            for line in ssrc:
                if "\"http" and ".mp4\"" in line:
                    print("munzfvdfdfvdvcddf", line)
                    streamurl = str("http" + str(line.split("\"http")[1].split(".mp4\"")[0]) + ".mp4")
                    episode = os.getcwd() + SLASH + str(name) + "_Episode_" + iterator + ".mp4"
                    print("Streamurl:", streamurl)
                    status = get_file(str(episode), streamurl, 0, 1)
                    currthreads.value = currthreads.value - 1
                    autocleanse(streamsrcfile)
                    if status:
                        return 0
                    else:
                        return 1
        elif "mp4upload" in hoster:
            for line in ssrc:
                if "\"file\":" and ".mp4\"" in line:
                    print("iuuzttr", line)
                    streamurl = str(line.split("\"file\": ")[1].replace("\"", "").strip(","))
                    episode = os.getcwd() + SLASH + str(name) + "_Episode_" + iterator + ".mp4"
                    print("Streamurl:", streamurl)
                    status = get_file(str(episode), streamurl, 0, 1)
                    currthreads.value = currthreads.value - 1
                    autocleanse(streamsrcfile)
                    if status:
                        return 0
                    else:
                        return 1
        elif "auroravid" in hoster:
            for line in ssrc:
                if "type=\'video/x-flv\'>" in line:
                    streamurl = str(line.split("\" type=\'video/x-flv\'>")[0].split("\"")[1])
                    episode = os.getcwd() + SLASH + str(name) + "_Episode_" + iterator + ".mp4"
                    print("Streamurl:", streamurl)
                    status = get_file(str(episode), streamurl, 0, 1)
                    currthreads.value = currthreads.value - 1
                    autocleanse(streamsrcfile)
                    if status:
                        return 0
                    else:
                        return 1
        elif "bitvid" in hoster:
            for line in ssrc:
                if "type=\'video/x-flv\'>" in line:
                    streamurl = str(line.split("\" type=\'video/x-flv\'>")[0].split("\"")[1])
                    episode = os.getcwd() + SLASH + str(name) + "_Episode_" + iterator + ".flv"
                    print("Streamurl:", streamurl)
                    status = get_file(str(episode), streamurl, 0, 1)
                    currthreads.value = currthreads.value - 1
                    autocleanse(streamsrcfile)
                    if status:
                        return 0
                    else:
                        return 1
        elif "streamcloud" in hoster:
            ses = requests.Session()
            init_req = ses.get(hoster, headers=HEADERS)
            _id = hoster.split("eu/")[1].split("/")[0]
            fname = hoster.split("eu/")[1].split("/")[0].strip(".html")
            datapayload = {"op":"download1", "usr_login":"", "id":_id, "fname":fname, "referer":"", "hash":""}
            time.sleep(11)
            req = ses.post(hoster, data=datapayload, cookies=init_req.cookies, headers=HEADERS)
            with tempfile.TemporaryFile() as tempf:
                tempf.write(req.content)
                tempf.seek(0)
                print("Searching for Filesource")
                for line in tempf:
                    line = str(line)
                    if "file:" in line:
                        streamurl = str(line.split("file: \"")[1].split("\"")[0])
                        episode = os.getcwd() + SLASH + str(name) + "_Episode_" + iterator + ".mp4"
                        print("Streamurl:", streamurl)
                        status = get_file(str(episode), streamurl, 0, 1)
                        currthreads.value = currthreads.value - 1
                        autocleanse(streamsrcfile)
                        if status:
                            return 0
                        else:
                            return 1
        else:
            return 1

def main():
    """MAIN"""
    os.umask(0)
    init_preps()
main()
