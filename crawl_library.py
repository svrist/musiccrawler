# 
# python version  2.6.2
# crawl_library.py
# 
# 
# 
# 
# 
# 


import re, os, os.path
import html5lib
from html5lib import treebuilders
import BeautifulSoup as Soup
from urlgrabber.grabber import URLGrabber, URLGrabError
import random
import time

URLGRABBER = URLGrabber(keepalive=0, retries=10)
SKIPPEDLINKS = []
#MAIN_STORAGE = '/home/bsm/Documents/Bachelor/data/'

def downloadFile(linelink, folderPath, path):
	''' Library function to download 'link' and save it to 'path'

'''
	if os.path.isfile(path) == False: # only download files we don't already have
		try:
			print "SYSTEM: trying to download " + linelink
			download = URLGRABBER.urlread(linelink)
		except URLGrabError, e:
			print "SYSTEM ERROR: download failed!"
			print e
			SKIPPEDLINKS.append(path)
			return False
		if (os.path.exists(folderPath + '/') == False):
			os.mkdir(folderPath + '/')
		fd = file(path, 'w')
		fd.write(download)
		fd.close()
		print "SYSTEM: writing file: " + path
		return True
	else:
		print "SYSTEM WARNING: file skipped, already existed: " + path
		SKIPPEDLINKS.append(path)
		return False

#CHANGED: har faet domain som argument
def getSoup(spec_url, hset,domain):
	if domain not in spec_url:
		url = domain + spec_url
	else:
		url = spec_url
	data = URLGRABBER.urlread(url)

	parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("beautifulsoup"))
	soup = parser.parse(data)


	#soup = Soup.BeautifulSoup(data)
	return soup



def getLinks(soup, getNameFunc=None, composer=None):
	''' using BeautifulSoup to organize the htm documents
	then find all <a tags and extract the actual links
	names are extracted from <a> tag contents
'''
	pagelinks = []
	for line in soup.findAll('a'): # find all 'a' tags
		getNameFunc(line, pagelinks, composer)

	return pagelinks

def rndslp(maxtime=10):
    rndslp = random.random()*maxtime
    print "SLEEP: %f s of a max %d s"%(rndslp,maxtime)
    time.sleep(rndslp)
    return rndslp

