#
# python version  2.6.2
# crawl_mutopia.py
#
# 
#By Brian Søborg Mathiasen and Kim Juncher (c)
#Extended for POG by s@vrist.dk


#import re, os, os.path
#import BeautifulSoup as Soup
#from urlgrabber.grabber import URLGrabber, URLGrabError

from crawl_library import *
import unicodedata
import sys
import logging
from preomrgae import Preomrgae as POG
import random
import time


DOMAIN = 'http://www.mutopiaproject.org'
URL_PATH = DOMAIN + '/browse.html'
SEPARATOR = '#'


#URLGRABBER = URLGrabber(keepalive=0, retries=10)
#SEPARATOR = '#'
#SKIPPEDLINKS = []

def extract_information(td, i):
   ''' function to parse a table soup to extract meta information such as work name, workyear.
Can be easily expanded to get more information if such is available in the table
'''
   workt = unicodedata.normalize('NFKD',td[i-5].contents[0]).encode("ascii","ignore")
   work = str(workt).replace('\"', '').replace('/', '-')
   work_nr = " "
   t = unicodedata.normalize('NFKD',td[i].contents[0]).encode("ascii","ignore")
   year = str(t.replace('\"', '').replace('/', '-'))
   return (work, work_nr, year)


def getNameFunc(line, pagelinks, termFunc=None, specSearch=None, composer=None):
   ''' specially designed naming function used to extract usable link and artist names or work names
this function is used by getWork() in conjunction with the API provided by crawl_library.py
'''
   name = ""
   if 'Composer=' in str(line):
      usablelink = str(line).split('<a href=\"')[1].split('\">')[0]
      name= str(unicodedata.normalize('NFKD',line.contents[0]).encode("ascii","ignore"))
      pagelinks.append((DOMAIN + '/' + usablelink, name))

def getComposer(name):
   ''' extracts the composers name and chops it to fit into the used naming standard
'''
   # prettify the name, it must use a certain naming standard
   name = name.split(' (')[0].split(' ')
   composer = name.pop() + ", "
   for initial in name:
      initial = initial.replace('.', '')
      composer += initial + " "
   return composer



def getWork():
   ''' main program to download and organize pdf scores
File names are saved as:
composer/composer#year#work_nr#title.pdf

returns the list of potential non-downloaded scores (direct links)
'''
   pagelinks = getLinks(getSoup(URL_PATH, domain=DOMAIN,hset=None),getNameFunc)

   for link, name in pagelinks:
       soup = getSoup(link, domain=DOMAIN,hset=None)
       tables = soup.findAll('table')
       td = tables[0].findAll('td')
       i = 6
       composer = getComposer(name)
       status,aid = pog.add_author(composer.strip(),link.strip(),site="mutopia")
       for line in soup.findAll('a'):
           stline = str(line)
           if 'a4.pdf' in stline:
               title, work_nr, year = extract_information(td, i)
               linelink = stline.split('<a href=\"')[1].split('\">')[0]
               try:
                   status,id = pog.add_work(DOMAIN+linelink[2:],aid,name=title,contentlink=link)
               except Exception, e:
                   l.warn("Failed to add work %s,%s",title,DOMAIN+linelink[2:])
               i += 21
               #if status.lower() == "ok":
                   #   continue
           sys.stdout.flush()
       rndslp(5)
   l.info("Done %d pagelinks",len(pagelinks))
   return SKIPPEDLINKS


if __name__ == '__main__':
    FORMAT = "%(asctime)-15s %(levelname)s [%(name)s.%(funcName)s]  %(message)s"
    logging.basicConfig(level=logging.DEBUG,format=FORMAT,filename="crawl_mutopia.log")
    pog = POG("http://localhost:8080")
    l = logging.getLogger("crawl_mutopia")
    l.info("Startup run. domain %s",DOMAIN)
    start = time.time()
    getWork()
    stop = time.time()
    l.info("Runtime %f",(start-stop))

