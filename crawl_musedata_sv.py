#
# python version  2.6.2
# crawl_musedata.py
#
# 
#  
#By Brian Søborg Mathiasen and Kim Juncher (c)
#Extended for POG by s@vrist.dk

#import re, os, os.path
import sys
import time
import random
import logging
#import BeautifulSoup as Soup
#from urlgrabber.grabber import URLGrabber, URLGrabError

from preomrgae import Preomrgae as POG
from crawl_library import *

DOMAIN = 'http://www.musedata.org'
URL_PATH = DOMAIN + '/cgi-bin/mdsearch?s=t&keyword=pdf'
MAIN_STORAGE = './data/'
STORAGE = MAIN_STORAGE + 'musedata/'
SEPARATOR = '#'

pog = POG()

#URLGRABBER = URLGrabber(keepalive=0, retries=10)
#SEPARATOR = '#'

def extract_information(line):
    ''' explodes a string and returns a number of values, such as work name, work number
'''
    splitline = line.split('/')
#    composer = splitline[4]
    work = splitline[-2]
    work_nr = splitline[-1]
    year = " "
    return (work, work_nr, year)


def getComposer(line):
    ''' extract full composer name from page
format:
"Surname, Firstname initials "
'''
    initials = ""
    if ('Composer' in line[0].contents[1].contents[0]):
        name = str(line[1].contents[0][1:])
        while (name[-1] == " "): # remove trailing whitespaces
            name = name[0:-1]
        nameelm = name.split(' ')
        name = nameelm[0] + ' '
        for elm in nameelm[1:]:
            initials += elm[0]+' '
        name += initials
        return name


def getNameFunc(line, pagelinks, termFunc=None, specSearch=None, composer=None):
    ''' specially designed naming function used to extract usable link and artist names or work names
this function is used by getWork() in conjunction with the API provided by crawl_library.py
'''
    usablelink = str(line).split('<a href=\"')[1].split('\">')[0]

    for t in line.contents:
        name = ""
        try:
            name+= str(t.contents[0])
        except Exception, e:
            name+= str(t)
            continue
    name = name.replace('/', '-').replace(':', '-').replace('\\','-').replace('"', '').replace('\\','')

    pagelinks.append((usablelink, name))




def getWork():
    ''' main program to download and organize pdf scores
File names are saved as:
composer/composer#year#work_nr#title.pdf

returns the list of potential non-downloaded scores (direct links)
'''
    pagelinks = getLinks(getSoup(URL_PATH, domain=DOMAIN,hset=None),getNameFunc)

    if (os.path.exists(STORAGE) == False):
        os.mkdir(STORAGE)
    
    for link, title in pagelinks:
        soup = getSoup(link, domain=DOMAIN,hset=None)
        composer = getComposer(soup.findAll('td'))
        try:
            status,aid = pog.add_author(composer,link,"musedata")
        except Exception, e:
            l.warn("Failed to add author. Skipping all. %s, %s",composer,link)
        else:
            sys.stdout.flush()
            for line in soup.findAll('a'):
                stline = str(line)
                if ('format=pdf' in stline and 'multi=zip' in stline) or 'file=fullscore.pdf' in stline or 'file=allparts.pdf' in stline:            # find the link with 'pdf'
                    work, work_nr, year = extract_information(link)
                    path = STORAGE + composer + '/' + composer + SEPARATOR + year + SEPARATOR + work_nr + SEPARATOR + title + '.pdf'
                    linelink = stline.split('<a href=\"')[1].split('\">')[0]
                    try:
                        pog.add_work(linelink,aid,name=work,contentlink=link)
                    except Exception, e:
                        l.warn("Failed to add work %s,%s for author %s",
                               work,linelink,composer)
            rndslp(5)
    return SKIPPEDLINKS



if __name__ == '__main__':
    FORMAT = "%(asctime)-15s %(levelname)s [%(name)s.%(funcName)s]  %(message)s"
    logging.basicConfig(level=logging.DEBUG,format=FORMAT,filename="crawl_musedata.log")
    l = logging.getLogger("crawl_musedata")
    l.info("Startup run. domain %s",DOMAIN)
    start = time.time()
    getWork()
    stop = time.time()
    l.info("Runtime %f",(start-stop))
