'''
This is designed for the new Azure Marketplace Bing Search API (released Aug 2012)

Inspired by https://github.com/mlagace/Python-SimpleBing and 
http://social.msdn.microsoft.com/Forums/pl-PL/windowsazuretroubleshooting/thread/450293bb-fa86-46ef-be7e-9c18dfb991ad
'''

import requests # Get from https://github.com/kennethreitz/requests
import string
import json

class BingSearchAPI():
    bing_api = "https://api.datamarket.azure.com/Bing/Search/News?"
    
    def __init__(self, key):
        self.key = key

    def replace_symbols(self, request):
        # Custom urlencoder.
        # They specifically want %27 as the quotation which is a single quote '
        # We're going to map both ' and " to %27 to make it more python-esque
        request = string.replace(request, "'", '%27')
        request = string.replace(request, '"', '%27')
        request = string.replace(request, '+', '%2b')
        request = string.replace(request, ' ', '%20')
        request = string.replace(request, ':', '%3a')
        return request
        
    def search(self, query, params):
        ''' This function expects a dictionary of query parameters and values.
            Sources and Query are mandatory fields. 
            Sources is required to be the first parameter.
            Both Sources and Query requires single quotes surrounding it.
            All parameters are case sensitive. Go figure.

            For the Bing Search API schema, go to http://www.bing.com/developers/
            Click on Bing Search API. Then download the Bing API Schema Guide
            (which is oddly a word document file...pretty lame for a web api doc)
        '''
        request = 'Query="'  + str(query) + '"'
        for key,value in params.iteritems():
            request += '&' + key + '=' + str(value) 
        request = self.bing_api + self.replace_symbols(request)
        print "request url is %s" %(request)
        return requests.get(request, auth=(self.key, self.key))


if __name__ == "__main__":
    my_key = "cwszVgNF2K/L0c8xnG09xOEIxEc35oWH4Gflv9fUpug="
    bing = BingSearchAPI(my_key)
    params = {'$format': 'json',
              '$top': 15,
              '$skip': 15}
    result =  bing.search('Your Name',params)

    print "result is %s" %(result.text)
#    print  (json.loads(result.text))['d']['results']

