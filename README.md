AutoCrawler
===========

This is a simple crawler with a timer and cookie support implemented by python.

Install
-----------------------

    git clone https://github.com/nekonanu/AutoCrawler.git
    

Quick Start
---------------------
###Sample1
    
    import AutoCrawler

    
    #define a handler
    def handler(msg): 
      print msg
      
    #define the cookie dictionary
    cookieDict = { 
      'token':'23897SADFJ23497YASDFKU23',
      'uid':'nekosama'
    }
    
    #define the interval
    interval = 3
    
    #define the request url and data
    url = "http://www.example.com/crawpage?page=1"
    data = {
        "keyword":"test",
        "type":0
    }

    #define the requestData object
    requestData = AutoCrawler.RequestData(url,data)
    
    #construct the CookieCrawler object
    crawler = AutoCrawler.CookieCrawler(url,[requestData],interval)

    #set the crawl process handler
    crawler.addHandler(AutoCrawler.CookieHandler(cookieDict))
    
    #set the pre-defined handler below, and now you can start it
    crawler.start(handler)
    
