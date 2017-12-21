"""Script to Download Anime Episodes from Proxer.me"""

import os
import threading
import multiprocessing
import time
import tempfile
import requests
from datetime import datetime
from shutil import which
from selenium import webdriver

#SEARCH FOR # TO FIND ALL COMMENTS

CURRTHREADS = multiprocessing.Value("i", 0)
LIMIT = 3
HEADERS = requests.utils.default_headers()
HEADERS.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",})
SUPPORTEDHOSTER = ["proxer", "streamcloud", "mp4upload", "bitvid", "auroravid"]
FIREFOXPATH = which("firefox")
CHROMEPATH = which("chrome") or which("chromium")
if os.name == "nt":
    SLASH = "\\"
else:
    SLASH = "/"
CWD = os.path.dirname(os.path.realpath(__file__)) + SLASH

def log(messagelist):
    logfile = CWD + "debug.log"
    txt = ""
    for x in messagelist:
        txt = txt + " " + str(x)
    txt = txt + "\n"
    with open(logfile, "a") as dbg:
        dbg.write(txt)

def get_file(srcfile, srcurl, counter=0, ftype=0):#ftype indicates if video or not
    """Function to Downloadad and verify downloaded Files"""
    if counter == 5:
        print("Could not download File:", srcfile, "in 5 attempts")
        return 1
    counter = counter + 1
    if not os.path.isfile(srcfile):
        time.sleep(5)
        print("Downloading", srcurl, "as", srcfile)
        with open(srcfile, "wb") as fifo:#open in binary write mode
            response = requests.get(srcurl, headers=HEADERS)#get request
            print("\n\n\n", response.headers,"\n\n\n") # check against actual filesize
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
            print("File was downloaded correctly on a previous run")
            return 0

def init_webdriver():
    """Simple Function to initialize and configure Webdriver"""
    if FIREFOXPATH != None:
        print(FIREFOXPATH)#cm
        from selenium.webdriver.firefox.options import Options

        options = Options()
        options.binary = FIREFOXPATH
        options.add_argument("-headless")
        return webdriver.Firefox(firefox_options=options, log_path="geckodriver.log")

    elif CHROMEPATH != None:
        print(CHROMEPATH)#cm
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.binary_location = CHROMEPATH
        options.add_argument("--headless")
        return webdriver.Chrome(chrome_options=options, service_args=['--verbose'], service_log_path="chromedriver.log")

def autocleanse(cleansefile):
    """ Function for safer deleting of files """
    if os.path.exists(cleansefile):
        os.remove(cleansefile)
        print("Removed:", cleansefile)
        return
    else:
        print("File", cleansefile, "not deleted, due to File not existing")
        return

def init_preps():
    """Function to initiate the Download Process"""
    dt = datetime.now()
    log(["-----------------", str(dt.hour) + ":" + str(dt.minute),  str(dt.day) + "-" + str(dt.month) + "-" + str(dt.year), "------------"])
    os.chdir(CWD)
    print("Recommended URL-Format would be: http://proxer.me/info/277/\n")
    inputurl = str(input("Please enter the URL of the Anime you want to download: "))
    #inputurl = "https://proxer.me/info/19588"#cm
    firstepisode = int(float(input("Please enter the Number of the first Episode you want: ") or 1))
    lastepisode = int(float(input("Please enter the Number of the last Episode you want: ") or 1))

    aninum = inputurl.split("/info/")[1].strip("/").replace("\n", "")
    infofile = CWD + aninum + ".html"
    get_file(infofile, inputurl)
    name = None
    log(["URL:\t", inputurl])
    with open(infofile, "r", encoding="UTF-8") as ifile:
        for line in ifile:
            if "<title>" in line and "Just a moment" not in line:
                name = line.split(" - ")[0].strip("<title>").replace("?", "").replace("'", "").replace("!", "").replace(":", " -").replace("&amp;", "&")
    if name == None:
        log(["Could not parse Anime-Name"])
        name = aninum

    autocleanse(infofile)
    animedir = CWD + name + SLASH
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
    print("Process", iterator, episodesrc)
    get_file(str(episodesrc), str(episodeurl))

    with open(episodesrc, "r", encoding="UTF-8") as esrc:
        for line in esrc:
            if  "var streams" in line:
                print(line.split("[{")[1].split("}];")[0].split("},{"))
                log([line.split("[{")[1].split("}];")[0].split("},{")])
                for streamhoster in line.split("[{")[1].split("}];")[0].split("},{"):
                    elem = streamhoster.split("code\":\"")[1].split("\",\"img\"")[0].replace(r"\/", "/").replace("//", "http://").replace("\":\"", "\",\"").split("\",\"")
                    print("Process", iterator + ":\n", elem)
                    if "http" in elem[8]:
                        baseurl = str(elem[8])
                        code = str(elem[0])
                        url = baseurl.replace("#", code)
                        print(url)
                        streamhosterlist.append(url)
    autocleanse(episodesrc)

    for url in streamhosterlist:
        found = False
        print(url)
        for hoster in SUPPORTEDHOSTER:
            if hoster in url.split("://")[1].split("/")[0]:
                found = True
                print("Process", iterator, "Valid Hoster", hoster, "in URL:", url)
        if found == False:
            streamhosterlist.remove(url)
            print("Debug Message: Unknown Hoster ", url)
            log(["Debug Message: Unknown Hoster", str(url)])    

    for hoster in streamhosterlist:
        hoster = str(hoster)
        print("Process", iterator, "Hoster:", hoster, "\n\n")
        switcher = parse_file(hoster, name, currthreads, iterator)
        log(["Process", iterator, "Evaluation:", switcher])
        if switcher == 0:
            currthreads.value = currthreads.value - 1
            return
        log(["Failed to download Episode", iterator, "from", hoster])
    currthreads.value = currthreads.value - 1
    log(["Failed to download Episode", iterator, "from all Hoster"])
    return

def parse_file(hoster, name, currthreads, iterator):
    """ Function that does the actual parsing and downloading """
    streamsrcfile = str(os.getcwd() + SLASH + "Stream_" + iterator + "-SRC.html")
    driver = init_webdriver()
    autocleanse(streamsrcfile)
    try:
        driver.get(hoster)
    except Exception as exep:
        print("Exception:\n", exep, "\nfor Hoster:", hoster)
        log(["Exception:\n", str(exep), "\nfor Hoster:", str(hoster)])
        driver.close()
        return 1
    
    time.sleep(12)
    with open(streamsrcfile, "w") as src:
        src.write(str(driver.page_source))
    driver.close()

    with open(streamsrcfile, "r", encoding="UTF-8") as ssrc:
        if "proxer" in hoster:
            print("ProxMe")
            for line in ssrc:
                line = str(line)
                if "\"http" and ".mp4\"" in line:
                    print("munzfvdfdfvdvcddf", line)
                    streamurl = str("http" + str(line.split("\"http")[1].split(".mp4\"")[0]) + ".mp4")
                    episode = os.getcwd() + SLASH + str(name) + "_Episode_" + iterator + ".mp4"
                    print("Streamurl:", streamurl)
                    status = get_file(str(episode), streamurl, 0, 1)
                    autocleanse(streamsrcfile)
                    if status == 0: # Change all to return status for final release
                        return 0#0
                    else:
                        return 1
        
        elif "mp4upload" in hoster:
            print("MP4Up")
            for line in ssrc:
                line = str(line)
                if "src=\"" and ".mp4\"" in line:
                    print("iuuzttr", line)
                    streamurl = str(line.split("src=\"")[1].split("\"")[0])
                    episode = os.getcwd() + SLASH + str(name) + "_Episode_" + iterator + ".mp4"#rm
                    print("Streamurl:", streamurl)
                    status = get_file(str(episode), streamurl, 0, 1)
                    autocleanse(streamsrcfile)
                    if status == 0:
                        return 0#0
                    else:
                        return 1
        
        elif "auroravid" in hoster:#fix
            print("Aurora")
            with open("aurora.html","w") as arl:#rm
                for line in ssrc:
                    line = str(line)
                    arl.write(line)#rm
                    if "type=\'video/x-flv\'>" in line:
                        streamurl = str(line.split("\" type=\'video/x-flv\'>")[0].split("\"")[1])
                        episode = os.gcwd() + SLASH + str(name) + "_Episode_" + iterator + ".mp4"#rm
                        print("Streamurl:", streamurl)
                        status = get_file(str(episode), streamurl, 0, 1)
                        autocleanse(streamsrcfile)
                        if status == 0:
                            return 0#0
                        else:
                            return 1
        
        elif "bitvid" in hoster:#fix
            print("BitVid")
            with open("bidvid.html","w") as bvl:#rm
                for line in ssrc:
                    line = str(line)
                    bvl.write(line)#rm
                    if "type=\'video/x-flv\'>" in line:
                        streamurl = str(line.split("\" type=\'video/x-flv\'>")[0].split("\"")[1])
                        episode = os.getcwd() + SLASH + str(name) + "_Episode_" + iterator + ".flv"#rm
                        print("Streamurl:", streamurl)
                        status = get_file(str(episode), streamurl, 0, 1)
                        autocleanse(streamsrcfile)
                        if status == 0:
                            return 0#0
                        else:
                            return 1
        
        elif "streamcloud" in hoster:#fix
            print("Streamcloud")
            autocleanse(streamsrcfile)
            ses = requests.Session()
            init_req = ses.get(hoster, headers=HEADERS)
            with open(streamsrcfile,"w+") as tempf:
                tempf.write(init_req.content.decode("utf-8"))
                tempf.seek(0)
                print("Searching for fname")
                for line in tempf:
                    if "<input type=\"hidden\" name=\"fname\" value=\"" in line:
                        fname = line.split("value=\"")[1].split("\">")[0]

            _id = hoster.split("eu/")[1].split("/")[0]
            print("Sent first Request")
            datapayload = {"op":"download1", "usr_login":"", "id":_id, "fname":fname, "referer":"", "hash":""}
            print(init_req.cookies)
            time.sleep(11)
            req = ses.post(hoster, data=datapayload, cookies=init_req.cookies, headers=HEADERS)
            print("Sent 2nd Request")
            with open("streamcloud.html", "w") as fifi:
                fifi.write(req.content.decode("utf-8"))
            with open(streamsrcfile,"w+") as tempf:
                tempf.write(req.content.decode("utf-8"))
                tempf.seek(0)
                print("Searching for Filesource")
                for line in tempf:
                    line = str(line)
                    if "file:" in line:
                        print("jnfdfvstzrt", line)
                        streamurl = str(line.split("file: \"")[1].split("\"")[0])
                        episode = os.getcwd() + SLASH + str(name) + "_Episode_" + iterator + ".mp4"
                        print("Streamurl:", streamurl)
                        status = get_file(str(episode), streamurl, 0, 1)
                        autocleanse(streamsrcfile)
                        if status == 0:
                            return 0
                        else:
                            return 1
    return 1

def main():
    """MAIN"""
    os.umask(0)
    init_preps()
main()
