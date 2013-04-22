READCACHE = False
WRITECACHE = True

def read_results():
    search_results = {}
    searchresults_file = open(filename, 'rb')
    search_results.update(marshal.load(searchresults_file))
    searchresults_file.close()
    return search_results

def write_results(search_results):
    print 'Saving search results.'
    searchresults_file = open(filename, 'wb')
    marshal.dump(search_results, searchresults_file)
    searchresults_file.close()
    
  
if READCACHE: 
    search_results = read_results()
else:
    search_results = {}
    for query in QUERIES:
        print 'Executing queries:', query
        search_results[query] = bing.search(query)
    
if WRITECACHE: write_results(search_results)
