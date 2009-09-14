#
#
# python version  2.6.2
#
# 

#Functions for crawling http://www.free-scores.com
#By Brian Søborg Mathiasen and Kim Juncher (c)
#Extended for POG by s@vrist.dk
from crawl_library import *
import urllib
from django.utils import simplejson as json
import unicodedata
import sys
import time
import random
import logging

from preomrgae import Preomrgae as POG

pog = POG("http://localhost:8080")

'''Function to create composername, given the standard used on free-scores.com. Ex: Beethoven, Ludwig van returns Bethoven, L. W. '''
def create_name(name):
	nameArr= name.split(',')
	if len(nameArr) > 1:
		initialsArr = nameArr[1].split(' ')
		composer = nameArr[0]
		composer += ","
		for name in initialsArr:
			if name != '':
				composer += " "
				composer += name[0:1]
				composer += "."
	else:
		composer = name
	return composer

piecematch = re.compile("pdf=(\d+)")

'''Function return an array of tuples with link and filename for every piece on the given site. This function is used in the second level in free-scores homepage, where we have 1-20 pieces from one composer listed on the page.
The filename will be cleaned from htmlentities.'''
def getPieceName(line, pagelinks, composer, termFunc=None, specSearch=None):
    if(("download-sheet-music.php" in str(line)) and ("free-scores" in str(line)) and (not "img" in str(line.contents[0]))):
        usablelink = str(line).split('<a href=\"')[1].split('\"')[0] # sweet sweet unreadable code
        res = piecematch.search(usablelink)
        pdfid = res.group(1)
        name = create_name(composer)
        name += "# # #"
        name += pdfid
        #tmp = str(line.contents[0])
        #print tmp
        #length = len(tmp)
        #name += tmp[1:length]
        name = name.replace('&#039;',"\'").replace('&quot;', '\'').replace('/','-').replace('&ldquo;','\'').replace('&Ouml;','O').replace('&ordf;','o').replace('&eacute;','E').replace('&auml;','a').replace('&szlig;','ss').replace('&rdquo;','\'').replace('&deg;','o').replace('<','-').replace('>','-').replace(':','-').replace('\"','\'').replace('\\','-').replace('|','-').replace('?','-').replace('*','-').replace('&ograve;','O').replace('&amp;','&').replace('&uuml;','u').replace('&Uuml;','U')
        pagelinks.append((usablelink, name))

'''Function return an array of tuples with link and composer for every composer on the given site. This function is used in the first level in free-scores homepage, where we have links to every composers listed on the page'''
def getComposerLinks(line, pagelinks, composer, termFunc=None, specSearch=None):
	if(("Download-PDF-Sheet-Music-" in str(line)) and ("img" not in str(line)) and ('free-scores' not in str(line))):
		usablelink = str(line).split('<a href=\"')[1].split('\"')[0] # sweet sweet unreadable code
		for t in line.contents:
			name = ""
			try:
				name+= str(t.contents[0])
			except Exception, e:
				name+= str(unicodedata.normalize('NFKD',t).encode("ascii","ignore"))
				continue
			name = name.replace('/', '-').replace(':', '-').replace('\\','-').replace('"', '').replace('\\','')
		pagelinks.append((usablelink, name))

'''Function returns an array of tuples with link and filetype for every downloadable pdf or zip-file, which meets the requirements. This function is used in the third level in free-scores homepage, after we have chosen a piece.'''
def getDownloadlink(line, pagelinks, composer, termFunc=None, specSearch=None):
	if("Download PDF Sheet music" in str(line) or ('Donwload PDF sheet music' in str(line))):
		usablelink = str(line).split('<a href=\"')[1].split('\"')[0] # sweet sweet unreadable code
		pagelinks.append((usablelink,'pdf'))
	if(('Download PDF' in str(line)) and ('Zip file' in str(line))):
		usablelink = str(line).split('<a href=\"')[1].split('\"')[0] # sweet sweet unreadable code
		pagelinks.append((usablelink,'zip'))

'''Function returns an array of links for the nextpage. If there isn't any next page, list would be empty.'''
def get_next_page(url, url_term, domain):
	url = str(url).replace('amp;','')
	soup = getSoup(url, url_term, domain)
	nextLink = []
	for line in soup.findAll('a'): # find all 'a' tags
		#print line
		if('Next page' in str(line)):
			usablelink = str(line).split('<a href=\"')[1].split('\"')[0] # sweet sweet unreadable code
			nextLink.append(usablelink)
	return nextLink

matchtitle = re.compile("Free sheet music : ([^-]*) - ([^\(]*) \(")
'''Function uses the library and speciel free-scores functions to download every piece, from a given period, which is chosen by it's unique link.'''
def get_it_all(period):
    l.info("Getting for period: %s",period)
    soup = getSoup(base+'free-sheet-music_composers.php?periode=%s'%period,
                   "free-scores", base)
    pagelinks = getLinks(soup, getNameFunc=getComposerLinks)
    for composers in pagelinks:
        link, name = composers
        status,aid = pog.add_author(name,base+link)
        first = 1
        nextLink = []
        while (0 < len(nextLink)) or (first == 1):
            first = 0
            try:
                nextLink = get_next_page(link, "free-scores", base)
                composerSoup = getSoup(link, "free-scores", base)
            except Exception,e:
                l.warn("Failure during GetSoup. Skipping. Url=%s\n%s",url,e)
                continue
            pieces = getLinks(composerSoup, getNameFunc=getPieceName, composer=name)
            for piece in pieces:
                sys.stdout.flush()
                specLink, specName = piece
                #print "SYSTEM: Piece -" + specName
                #print "specLink %s"%specLink
                try:
                    downloadSoup = getSoup(specLink, "free-scores", base)
                except Exception, e:
                    l.warn("Failure during getSoup. Skipping. %s\n%s",specLink,e)
                    continue

                downloadLinkArr = getLinks(downloadSoup, getNameFunc=getDownloadlink)
                if len(downloadLinkArr) == 0:
                    l.warn("No links found in %s.",specLink)
                    continue
                download,filetype = downloadLinkArr[0]
                if not filetype is "pdf":
                    print "Skipping download %s. Not pdf"%download
                    break
                pagelinks = []
                title=str([ line for line in downloadSoup.findAll('title')][0])
                res = matchtitle.search(title)
                if not res is None:
                    try:
                        pog.add_work(download,aid,name=res.group(2),contentlink=specLink)
                    except Exception, e:
                        l.warn("Add_work failed for %s, for author %s. "+\
                               "Exception %s",download, name,e)
                    else:
                        rndslp(maxtime=1)
                else:
                    print "Failed to match title: %s"%title
                    l.warn("Failed to match title %s",title)

            if 0 < len(nextLink):
                print "SYSTEM: Continues to next page"
                rndslp()
                link = str(nextLink[0]).replace('amp;','')				
            else:
                print "SYSTEM: No further pages - continues to next composer"
                sys.stdout.flush()
                print "COMPLETED"

        # Inserting a random sleep
        rndslp()
    else:
        logging.warn("Nothing found for the period")
    logging.info("Done. %d pagelinks",len(pagelinks))


if __name__ == "__main__":
    base = "http://www.free-scores.com/"
    FORMAT = "%(asctime)-15s %(levelname)s [%(name)s.%(funcName)s]  %(message)s"
    logging.basicConfig(level=logging.DEBUG,format=FORMAT,filename="crawl_freescore.log")
    l = logging.getLogger("crawlsv")
    l.info("Startup run. Base %s",base)
    start = time.time()
    try:
        get_it_all(sys.argv[-1])
    except Exception, e:
        l.warn("Failed with exception: %s. Closing",e)
    stop = time.time()
    l.info("Runtime %f",(start-stop))

