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
            str += (key+"="+value+";")
        return str

class CookieCrawler:
    def __init__(self,requestData,interval = None,cookieDict = None,option = None):
        global timerList
        timerList = list()
        # option definition
        self.showLog = False
        if option is not None:
            if option.has_key('showLog'):
                self.showLog = option['showLog']
        # initial fields
        self.cookieStr = CookieStr()
        self.interval = interval
        self.timerIndex = -1
        self.request = self.__initRequest(requestData,cookieDict)
        self.interval = interval

    def start(self,func,interval = None):
        self.handler = func
        if self.request is None:
            raise InternalErrorException("url is not set yet!")
        if interval is None:
            if self.interval is None:
                raise InternalErrorException("interval is not set yet!")
        else:
            self.interval = interval

        self.timerIndex = len(timerList)
        res = dict()
        for id,req in self.request.items():
            res[id] = self.__crawl(req)
        self.__mainLoop(self.request,res,self.cookieStr)

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

    def end(self):
        t = timerList[self.timerIndex]
        t.cancel()

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
                cookieStr.replaceCookie(key,value)

            request.add_header('Cookie',cookieStr.toStr())
            if self.showLog:
                print "receive new cookies: " + str(ckDict)
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

    def __mainLoop(self,request,response,cookieStr):
        if isinstance(request,dict):
            returnDict = dict()
            maintainRes = dict()
            for id,req in request.items():
                self.__maintainCookie(req,response[id],cookieStr)
                response[id].close()
                maintainRes[id] = self.__crawl(req)

            for id,req in maintainRes.items():
                returnDict[id] = req.read()

            self.handler(returnDict)
            interval = self.interval
            t = threading.Timer(interval,self.__mainLoop,(request,maintainRes,cookieStr))
            timerList.append(t)
            t.start()

    # function  use urllib2 to open the request, return the response
    # para      request:single request object, not list
    # return    the response object returned by urllib2.urlopen() function
    def __crawl(self,request):
        start = time.time()
        if self.showLog:
            print "crawling: " + str(request.get_full_url())
        result = urllib2.urlopen(request)

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

        return result
