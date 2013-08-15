__author__ = 'liangrui.hlr'
import urllib
import urllib2
import threading
import time
import logging
import logging.handlers
import os

#const fields
DEBUG = logging.DEBUG
INFO = logging.INFO

class InternalErrorException(Exception):
    def __init__(self, msg):
        Exception.__init__(self,msg)

class RequestData:
    def __init__(self, id, url, data = None):
        self.id = id
        self.url = url
        self.data = data

class WorkThread(threading.Thread):
    def __init__(self, workFunction, sleepTime = None):
        threading.Thread.__init__(self)
        self.task = workFunction
        self.sleepTime = sleepTime

    def run(self):
        self.running = True
        self.__work()

    def stop(self):
        self.running = False

    def __work(self):
        while self.running:
            self.task()
            if self.sleepTime is not None:
                time.sleep(self.sleepTime)


class CookieHandler(urllib2.BaseHandler):
    def __init__(self, cookieDict):
        self.cookieJar = CookieJar()
        self.cookieJar.replaceAllFromDict(cookieDict)

    def http_request(self, request):
        self.cookieJar.extractToRequest(request)
        return request

    def http_response(self, request, response):
        self.cookieJar.addCookieFromResponse(response)
        self.cookieJar.extractToRequest(request)
        return response

    def setLogger(self,logger):
        self.logger = logger

    https_request = http_request
    https_response = http_response


class CookieJar:
    def __init__(self,cookieDict = None):
        self.cookieDict = dict()
        if cookieDict is not None:
            self.replaceAllFromDict(cookieDict)

    def addCookie(self,key,value):
        self.cookieDict[key] = value

    def replaceAllFromDict(self, cookieDict):
        self.cookieDict.clear()
        for key,value in cookieDict.iteritems():
            self.cookieDict[key] = value

    def extractToRequest(self, request):
        request.add_header("Cookie", self.toStr())

    def addCookieFromResponse(self, response):
        headers = response.info()
        if not 'Set-Cookie' in headers:
            return
        ckDict = self.__getCookieFromHeadStr(headers['Set-Cookie'])
        for key,value in ckDict.iteritems():
            self.addCookie(key.strip(' '),value.strip(' '))

    def toStr(self):
        return ";".join("%s=%s" % (key,value) for (key,value) in self.cookieDict.iteritems())

    def __getCookieFromHeadStr(self,setCookieStr):
        resDict = {}
        ckItem = str(setCookieStr).split(',')
        for item in ckItem:
            ckKeyValue = item.split(';')
            if ckKeyValue[0].find("=") == -1:
                continue
            keyValueList = ckKeyValue[0].split('=')
            resDict[keyValueList[0]] = keyValueList[1]
        return resDict

class CookieCrawler:
    def __init__(self, name ,requestData, interval = None, logger_level = DEBUG):
        # build default opener
        self.opener = urllib2.build_opener()

        self.name = name
        self.interval = interval
        self.request = self.__initRequest(requestData)
        self.lastCrawlTime = time.time()

        #init logger
        logger = logging.getLogger(name)
        logger.setLevel(logger_level)
        #create log directory
        cwd = os.getcwd()
        path = cwd + os.sep + "log" + os.sep + self.name
        if not os.path.exists(path):
            os.makedirs(path)

        #create timeRotationHandler
        trh = logging.handlers.TimedRotatingFileHandler(filename=("log" + os.sep + name + os.sep + name + "_log_"), when='s', interval=5 ,backupCount=100)
        trh.setLevel(logger_level)
        trh.suffix = "%Y%m%d-%H%M%S.log"
        #add formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        trh.setFormatter(formatter)

        logger.addHandler(trh)
        self.logger = logger

    def addHandler(self,*handlers):
        for handler in handlers:
            handler.setLogger(self.logger)
        self.opener = urllib2.build_opener(*handlers)

    def start(self,func,interval = None):
        self.handler = func

        if self.request is None:
            raise InternalErrorException("url is not set yet!")

        if interval is None and self.interval is None:
            raise InternalErrorException("interval is not set yet!")

        if self.interval is None:
            self.interval = interval

        print self.interval
        self.thread = WorkThread(self.__mainLoop,self.interval)
        self.thread.start()

    def hotReplaceRequestData(self,requestData):
        self.request = self.__initRequest(requestData)

    # replace the handler function for handling the crawling result
    def hotReplaceHandler(self,func):
        self.handler = func

    def crawl(self,requestData = None):
        if requestData is None and self.request is None:
            raise InternalErrorException("url is not set yet!")
        else:
            self.request = self.__initRequest(requestData)

        result = {}
        for id,req in self.request.iteritems():
            result[id] = self.__crawl(req)

        returnDict = {}
        for id,res in result.iteritems():
            returnDict[id] = res.read()
            res.close()
        return returnDict

    def __initRequest(self,requestData):
        if not isinstance(requestData,list):
            raise InternalErrorException("requestData must be a list")
        requests = {}
        for dataItem in requestData:
            encodeData = None
            if dataItem.data is not None:
                encodeData = urllib.urlencode(dataItem.data)
            request = urllib2.Request(dataItem.url,encodeData)
            requests[dataItem.id] = request
        return requests

    def __mainLoop(self):
        start = time.time()
        returnDict = dict()
        maintainRes = dict()
        for id,req in self.request.iteritems():
            maintainRes[id] = self.__crawl(req)

        end = time.time()
        cost = end - start
        self.logger.debug("complete!")
        self.logger.debug("time cost:" + str(cost) + "s")
        if self.interval is not None and self.interval <= cost:
            self.interval = cost*1.5
            self.logger.debug("interval is less than crawling time!")
            self.logger.debug("adjust interval to " + str(self.interval))

        for id,req in maintainRes.iteritems():
            returnDict[id] = req.read()
        self.lastCrawlTime = time.time()
        self.handler(returnDict)

    # function  use urllib2 to open the request, return the response
    # para      request:single request object, not list
    # return    the response object returned by urllib2.urlopen() function
    def __crawl(self,request):
        self.logger.debug("crawling: " + str(request.get_full_url()))
        result = self.opener.open(request)
        return result
