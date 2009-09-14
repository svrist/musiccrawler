import urllib
import unicodedata
import random
import time
import sys
from django.utils import simplejson as json
import logging

MAXSLEEP=30
MAXRETRY=10

def tryalotjson(retrymethod,retry,url,qs=(),maxretry=MAXRETRY,maxsleep=MAXSLEEP):
    try:
        result = urllib.urlopen(url%qs)
        data = json.loads(result.read())
    except Exception, e:
        print "Exception: %s"%e
        if (retry < maxretry):
            rndslp = random.random()*maxsleep
            print "Sleeping %f s of max %d s before retrying"\
                    %(rndslp,maxsleep)
            sys.stdout.flush()
            time.sleep(rndslp)
            retry += 1
            return retrymethod(retry)
        else:
            raise
    else:
        if data['status'].lower() in ["ok","dup"]:
            msg = "Status: %s: %s"%(data['status'],data['msg'])
            print str(unicodedata.normalize('NFKD',msg).encode("ascii","ignore"))
            return data['status'],data['id']
        else:
            print "Status: %s:%s\n=========\n%s"%(data['status'],data['msg'],data)
            raise Exception



class Preomrgae:
    def __init__(self,gaeurl =
                 "http://preomr.appspot.com",maxsleep=MAXSLEEP,maxretry=MAXRETRY):
        self.gaeurl = gaeurl
        self.l = logging.getLogger(self.__class__.__name__)
        self.l.info("Using %s as gae",self.gaeurl)

    def add_work(self,dlurl,authorid,name,retry=0,**kwargs):
        url = self.gaeurl+"/work/create?%s"
        jd = {
            'url':dlurl,
            'author': authorid,
            'type':'pdf',
            'name':name
        }
        jd2 = {}
        jd2.update(kwargs)
        jd2.update(jd)
        qs = urllib.urlencode(jd2)

        return tryalotjson( (lambda r: self.add_work(dlurl,authorid,name,retry=r,**kwargs)),
                           retry,
                      url,qs)


    def add_author(self,name,siteurl,site="free-score",retry=0):
        url = self.gaeurl+"/author/create?%s"
        qs= {
            'name':name,
            'site':site,
            'site-url':siteurl,
        }
        qs = urllib.urlencode(qs)
        return tryalotjson((lambda r: self.add_author(name,siteurl,site,r)),
                           retry, url,qs)
