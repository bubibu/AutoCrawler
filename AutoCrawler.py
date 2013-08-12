__author__ = 'liangrui.hlr'

import urllib
import urllib2
import threading
import time
import sys

class InternalErrorException(Exception):
    def __init__(self,msg):
        Exception.__init__(self,msg)

class RequestData:
    def __init__(self,id,url,data = None):
        self.id = id
        self.url = url
        self.data = data

class WorkThread(threading.Thread):
    def __init__(self,workFunction,sleepTime = None):
        threading.Thread.__init__(self)
        self.task = workFunction
        self.sleepTime = sleepTime

    def run(self):
        self.running = True
        self.__work()

    def __work(self):
        while self.running:
            self.task()
            if self.sleepTime is not None:
                time.sleep(self.sleepTime)

    def stop(self):
        self.running = False



class CookieStr:
    def __init__(self,cookieDict = None):
        self.cookieDict = dict()
        if cookieDict is not None:
            self.replaceAllFromDict(cookieDict)

    def addCookie(self,key,value):
        self.cookieDict[key] = value

    def replaceCookie(self,key,value):
        self.addCookie(key,value)

    def replaceAllFromDict(self,cookieDict):
        self.cookieDict.clear()
        for key,value in cookieDict.items():
            self.cookieDict[key] = value

    def toStr(self):
        str = ""
        for key,value in self.cookieDict.items():
            str += (key.strip(' ')+"="+value.strip(' ')+";")
        return str

class CookieCrawler:
    def __init__(self,requestData,interval = None,cookieDict = None,option = None):
        # const fields
        self.checkInterval = 3
        self.breakInterval = 3

        # option definition
        self.showLog = False
        self.debug = False
        if option is not None:
            if option.has_key('showLog'):
                self.showLog = option['showLog']
            if option.has_key('debug'):
                self.debug = option['debug']

        if self.debug:
            self.errorFile = file(str(time.time()) + "debug.log","w")
        # initial fields
        self.cookieStr = CookieStr()
        self.interval = interval
        self.request = self.__initRequest(requestData,cookieDict)
        self.interval = interval
        self.lastCrawlTime = time.time()

    def start(self,func,interval = None):
        self.handler = func
        self.isFirstLoop = True
        if self.request is None:
            raise InternalErrorException("url is not set yet!")
        if interval is None:
            if self.interval is None:
                raise InternalErrorException("interval is not set yet!")
        else:
            self.interval = interval

        self.thread = WorkThread(self.__mainLoop,self.interval)
        self.thread.start()

        checkThread = WorkThread(self.__checkStatus)
        checkThread.start()

    def __checkStatus(self):
        # every x intervals where x is defined by the checkInterval
        # the program will check the crawler status to make sure the crawler work normally
        while self.thread.isAlive():
            self.thread.join(self.checkInterval * self.interval)
            if self.showLog:
                print "check status!"
                print time.time()
                print self.lastCrawlTime
            if time.time() - self.lastCrawlTime >= self.breakInterval * self.interval:
                # the program has something wrong
                # stop the current crawl process and restart
                print "join!"
                self.thread.stop()
                self.thread.join()
                print "restart the thread"
                self.thread.start()

    def setUrl(self,url):
        self.request = self.__initRequest(url,self.cookieStr)

    def hotReplaceRequestData(self,requestData,cookieDict):
        self.request = self.__initRequest(requestData,cookieDict)

    def hotReplaceCookie(self,cookieDict):
        self.cookieStr.replaceAllFromDict(cookieDict)

    # replace the handler function for handling the crawling result
    def hotReplaceHandler(self,func):
        self.handler = func

    def setOption(self,option):
        if option.has_key('showLog'):
            self.showLog = option['showLog']

    def crawl(self,requestData = None):
        if requestData is None:
            if self.request is None:
                raise InternalErrorException("url is not set yet!")
        else:
            self.request = self.__initRequest(requestData)

        result = dict()
        for id,req in self.request.items():
            result[id] = self.__crawl(req)

        returnDict = dict()
        if isinstance(result,dict):
            for id,res in result.items():
                returnDict[id] = res.read()
                res.close()
            return returnDict
        else:
            content = result.read()
            result.close()
            return content

    def __log(self,msg):
        self.errorFile.write(msg + "\n")
        self.errorFile.flush()

    def __initRequest(self,requestData,cookieDict = None):
        if cookieDict is not None:
            self.cookieStr.replaceAllFromDict(cookieDict)
        if isinstance(requestData,list):
            requests = dict()
            for dataItem in requestData:
                encodeData = None
                if dataItem.data is not None:
                    encodeData = urllib.urlencode(dataItem.data)
                request = urllib2.Request(dataItem.url,encodeData)
                request.add_header('Cookie',self.cookieStr.toStr())
                requests[dataItem.id] = request
            return requests

    def __maintainCookie(self,request,response,cookieStr):
        headers = response.info()
        if 'Set-Cookie' in headers:
            ckDict = self.__getCookieFromHeadStr(headers['Set-Cookie'])
            for key,value in ckDict.items():
                cookieStr.replaceCookie(key.strip(' '),value.strip(' '))
            for id,req in self.request.items():
                req.add_header('Cookie',cookieStr.toStr())
            if self.showLog:
                print "receive new cookies: " + str(ckDict)
                print "cookieHeader:" + self.cookieStr.toStr()
        return request

    def __getCookieFromHeadStr(self,setCookieStr):
        resDict = dict()
        ckItem = str(setCookieStr).split(',')
        for item in ckItem:
            ckKeyValue = item.split(';')
            if ckKeyValue[0].find("=") != -1:
                keyValueList = ckKeyValue[0].split('=')
                resDict[keyValueList[0]] = keyValueList[1]
        return resDict

    def __mainLoop(self):
        start = time.time()
        returnDict = dict()
        maintainRes = dict()
        for id,req in self.request.items():
            maintainRes[id] = self.__crawl(req)
            self.__maintainCookie(req,maintainRes[id],self.cookieStr)

        end = time.time()
        cost = end - start
        if self.showLog:
            print "complete!"
            print "time cost:" + str(cost) + "s"
        if self.interval is not None and self.interval <= cost:
            self.interval = cost*1.5
            if self.showLog:
                print "interval is less than crawling time!"
                print "adjust interval to " + str(self.interval)

        for id,req in maintainRes.items():
            returnDict[id] = req.read()
        self.lastCrawlTime = time.time()
        self.handler(returnDict)
        if self.debug:
            self.__showStatus()

    def __showStatus(self):
        self.__log("crawler status[" + str(time.strftime("%Y-%m-%d %X",time.localtime())) + "]:")
        self.__log("craw interval:" + str(self.interval))
        self.__log("craw cookie:" + self.cookieStr.toStr())
        self.__log("craw request:" + str(self.request))
        self.__log("craw thread alive?:" + str(self.thread.isAlive()))
        self.__log("last craw time:" + str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.lastCrawlTime))))
        if time.time() - self.lastCrawlTime >= self.breakInterval * self.interval:
            self.__log("crawl breakdown!")

    # function  use urllib2 to open the request, return the response
    # para      request:single request object, not list
    # return    the response object returned by urllib2.urlopen() function
    def __crawl(self,request):
        if self.showLog:
            print "crawling: " + str(request.get_full_url())
        result = urllib2.urlopen(request)
        return result
