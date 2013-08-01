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
        self.request = None
        self.cookieStr = CookieStr()
        self.interval = None
        if url is not None:
            self.request = self.__initRequest(url,cookieDict)
        self.interval = interval

    def start(self,func,interval = None):
        if self.request is None:
            raise InternalErrorException("url is not set yet!")
        if self.interval is None:
            if interval is None:
                raise InternalErrorException("interval is not set yet!")
            self.interval = interval
        self.interval = interval
        res = urllib2.urlopen(self.request)
        self.__mainLoop(self.request,res,self.cookieStr,self.interval,func)

    def setUrl(self,url):
        self.request = self.__initRequest(url,self.cookieStr)

    def craw(self,url = None):
        if url is None:
            if self.request is None:
                raise InternalErrorException("url is not set yet!")
            res = urllib2.urlopen(self.request)
            return res.read()
        else:
            self.request = urllib2.Request(url)
            self.request.add_header('Cookie',self.cookieStr.toStr())
            res = urllib2.urlopen(self.request)
            return res.read()

    def end(self):
        t.cancel()

    def __initRequest(self,url,cookieDict = None):
        if cookieDict is not None:
            self.cookieStr.replaceAllFromDict(cookieDict)
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
        self.__maintainCookie(request,response,cookieStr)
        res = urllib2.urlopen(request)
        func(res.read())
        global t
        t = threading.Timer(interval,self.__mainLoop,(request,res,cookieStr,interval,func))
        t.start()
