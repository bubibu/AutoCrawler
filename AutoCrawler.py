__author__ = 'liangrui.hlr'

import urllib2
import threading

class InternalErrorException(Exception):
    def __init__(self,msg):
        Exception.__init__(self,msg)


class CookieStr:
    def __init__(self):
        self.cookieDict = dict()

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
    def __init__(self,url = None,interval = None,cookieDict = None):
        global timerList
        timerList = list()
        self.request = None
        self.cookieStr = CookieStr()
        self.interval = None
        self.timerIndex = -1
        if url is not None:
            self.request = self.__initRequest(url,cookieDict)
        self.interval = interval

    def start(self,func,interval = None):
        if self.request is None:
            raise InternalErrorException("url is not set yet!")
        if interval is None:
            if self.interval is None:
                raise InternalErrorException("interval is not set yet!")
        else:
            self.interval = interval

        self.timerIndex = len(timerList)
        if isinstance(self.request,dict):
            res = dict()
            for url,request in self.request.items():
                res[url] = urllib2.urlopen(request)
            self.__mainLoop(self.request,res,self.cookieStr,self.interval,func)
        else:
            res = urllib2.urlopen(self.request)
            self.__mainLoop(self.request,res,self.cookieStr,self.interval,func)

    def setUrl(self,url):
        self.request = self.__initRequest(url,self.cookieStr)

    def craw(self,url = None):
        if url is None:
            if self.request is None:
                raise InternalErrorException("url is not set yet!")
        else:
            if isinstance(url,list):
                self.request = dict()
                for urlitem in url:
                    req = urllib2.Request(urlitem)
                    req.add_header('Cookie',self.cookieStr.toStr())
                    self.request[urlitem] = req
            else:
                self.request = urllib2.Request(url)
                self.request.add_header('Cookie',self.cookieStr.toStr())
        returnDict = dict()

        if isinstance(self.request,dict):
            for url,request in self.request.items():
                returnDict[url] = urllib2.urlopen(request).read()
            return returnDict
        else:
            res = urllib2.urlopen(self.request)
            return res.read()

    def end(self):
        t = timerList[self.timerIndex]
        t.cancel()

    def __initRequest(self,url,cookieDict = None):
        if cookieDict is not None:
            self.cookieStr.replaceAllFromDict(cookieDict)
        if isinstance(url,list):
            requests = dict()
            for urlitem in url:
                request = urllib2.Request(urlitem)
                request.add_header('Cookie',self.cookieStr.toStr())
                requests[urlitem] = request
            return requests
        else:
            request = urllib2.Request(url)
            request.add_header('Cookie',self.cookieStr.toStr())
            return request

    def __maintainCookie(self,request,response,cookieStr):
        headers = response.info()
        if 'Set-Cookie' in headers:
            ckDict = self.__getCookieFromHeadStr(headers['Set-Cookie'])
            for key,value in ckDict.items():
                cookieStr.replaceCookie(key,value)

            request.add_header('Cookie',cookieStr.toStr())
            print ckDict
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

    def __mainLoop(self,request,response,cookieStr,interval,func):
        if isinstance(request,dict):
            returnDict = dict()
            maintainRes = dict()
            for url,req in request.items():
                self.__maintainCookie(req,response[url],cookieStr)
                res = urllib2.urlopen(req)
                maintainRes[url] = res
                returnDict[url] = res.read()
            func(returnDict)
            t = threading.Timer(interval,self.__mainLoop,(request,maintainRes,cookieStr,interval,func))
            timerList.append(t)
            t.start()
        else:
            self.__maintainCookie(request,response,cookieStr)
            res = urllib2.urlopen(request)
            func(res.read())
            t = threading.Timer(interval,self.__mainLoop,(request,res,cookieStr,interval,func))
            timerList.append(t)
            t.start()
