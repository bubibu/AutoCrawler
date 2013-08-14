__author__ = 'liangrui.hlr'

import urllib
import urllib2
import threading
import time

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


class CookieHandler(urllib2.BaseHandler):
    def __init__(self,cookieDict):
        self.cookieJar = CookieJar()
        self.cookieJar.replaceAllFromDict(cookieDict)

    def http_request(self, request):
        self.cookieJar.extractToRequest(request)
        return request

    def http_response(self, request, response):
        self.cookieJar.addCookieFromResponse(response)
        self.cookieJar.extractToRequest(request)
        return response

    https_request = http_request
    https_response = http_response


class CookieJar:
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

    def extractToRequest(self,request):
        request.add_header("Cookie",self.toStr())

    def addCookieFromResponse(self,response):
        headers = response.info()
        if headers.has_key('Set-Cookie'):
            ckDict = self.__getCookieFromHeadStr(headers['Set-Cookie'])
            print "receive cookie: " + str(ckDict)
            for key,value in ckDict.items():
                self.addCookie(key.strip(' '),value.strip(' '))

    def toStr(self):
        str = ""
        for key,value in self.cookieDict.items():
            str += (key.strip(' ')+"="+value.strip(' ')+";")
        return str

    def __getCookieFromHeadStr(self,setCookieStr):
        resDict = dict()
        ckItem = str(setCookieStr).split(',')
        for item in ckItem:
            ckKeyValue = item.split(';')
            if ckKeyValue[0].find("=") != -1:
                keyValueList = ckKeyValue[0].split('=')
                resDict[keyValueList[0]] = keyValueList[1]
        return resDict

class CookieCrawler:
    def __init__(self,requestData,interval = None,option = None):
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
        self.cookieStr = CookieJar()
        self.interval = interval
        self.request = self.__initRequest(requestData)
        self.interval = interval
        self.lastCrawlTime = time.time()

    def addHandler(self,*handlers):
        self.opener = urllib2.build_opener(*handlers)
        urllib2.install_opener(self.opener)

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

    def __initRequest(self,requestData):
        if isinstance(requestData,list):
            requests = dict()
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
        for id,req in self.request.items():
            maintainRes[id] = self.__crawl(req)

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
