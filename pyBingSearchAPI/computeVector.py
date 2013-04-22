#!/bin/python
import re
import pdb
import os
import math
import json
import random
import copy
import pprint
import marshal

from bing_search_api import *

READCACHE = True
WRITECACHE = False
filename = "results.txt"

def read_results():
    search_results = {}
    topic = {}
    searchresults_file = open(filename, 'rb')
    search_results.update(marshal.load(searchresults_file))
    searchresults_file.close()
    searchresults_file = open("topic", 'rb')
    topic.update(marshal.load(searchresults_file))
    searchresults_file.close()
    return search_results, topic

def write_results(search_results, topic):
    print 'Saving search results.'
    searchresults_file = open(filename, 'wb')
    marshal.dump(search_results, searchresults_file)
    searchresults_file.close()
    searchresults_file = open("topic", 'wb')
    marshal.dump(topic, searchresults_file)
    searchresults_file.close()

"""
This is a class which calls the BingSearchAPI to get the top 30 results for that query

"""
class Search():
    def __init__(self, key):
        self.key = key

    def category_search(self, query):
        categories = ["rt_Entertainment", "rt_Business", "rt_Politics"]
        result = {}
        for category in categories:
            result[category] = self.search_query(query, category)
        return result
            
    def search_query(self, query, category=None):
        #Use the BingSearchAPI class to call the bing api and get the search results for the query
        skip = 0
        final_result = []
        for i in range(0, 2):
            bing = BingSearchAPI(self.key)
            params = {'$format': 'json',
                      '$top': 15,
                      '$skip': skip} 
            if category != None:
                cate = "'" + category + "'"
                params['NewsCategory'] = cate
            result =  bing.search(query,params)
            if (result.status_code != 200):
                print "Error in retrieving document. Error is %s" %(result.status_code)
                return None
            result = (json.loads(result.text))['d']['results']
            final_result.extend(result)
            skip = skip + 15
            
        procesed_result = []
        for result in final_result:
            procesed_result.append((result['Description'] + " "+result['Title']))
            
        return procesed_result
         #Extract the results from the text

"""
This class processess the results, computing tf-idfs for a set of results
"""
class process_results():
    def __init__(self, key):
        self.key = key
        self.tf_idf = {}
        self.result_set = {}
        self.doc_topic = {}
        self.doc = 0
        self.dim = {}
        self.query_num = 0
    
    def query(self, query):
       search = Search(self.key)
       search_result = search.search_query(query) 
      
       for result in search_result:
            """
            text_doc = result['Description'] + " "+result['Title']; 
            self.result_set[self.doc] = text_doc
            """
            self.result_set[self.doc] = result
            self.doc_topic[self.doc] = self.query_num
            self.doc = self.doc + 1
       self.query_num = self.query_num + 1

    def get_result_set(self): 
        return self.result_set, self.doc_topic

    def set_results(self, result_set, topic_doc):
        self.result_set = result_set
        self.doc_topic = topic_doc
        self.doc = len(topic_doc.keys())
    
    def compute_tf_idf(self, top_words = None):
        idf = {}
        for doc_id, result in self.result_set.iteritems():
            result = result.lower()
            local_dict = {}
            words = re.split(r'\W+', result)

            #compute the frequency of each word in the document
            for word in words:
                if word in local_dict:
                    local_dict[word] = local_dict[word] + 1
                else:
                    local_dict[word] = 1
           
            #update the document frequency of the words that just occured in the document
            for key, value in local_dict.iteritems():
                if key in idf:
                    idf[key] = idf[key] + 1 
                else:
                    idf[key] = 1
                #take the log vaue for the tf    
                local_dict[key] = math.log(value, 2) + 1    

            self.tf_idf[doc_id] = local_dict 
           

        if top_words != None:
            for doc_id, word_list in self.tf_idf.iteritems():
                for word, tf in word_list.iteritems():
                    if word in top_words:
                        self.tf_idf[doc_id][word] = self.tf_idf[doc_id][word] * 2
        
        # Multiply the tf with the idf to get tf_idf vector for the document   
        for doc_id, word_list in self.tf_idf.iteritems():
           dim = 0
           for word, tf in word_list.iteritems():
                tf_idf = tf * math.log((float) (self.doc-1)/idf[word], 2)
                self.tf_idf[doc_id][word] = tf_idf
                dim = dim + math.pow(self.tf_idf[doc_id][word], 2)
           self.dim[doc_id] = math.pow(dim, .5)
       
        #print self.tf_idf
        return self.tf_idf, self.dim, idf, self.doc_topic

    def clear(self):
        self.tf_idf = {}
        self.result_set = {}
        self.doc = 0
        self.doc_topic = {}


if __name__ == '__main__':
    my_key = "cwszVgNF2K/L0c8xnG09xOEIxEc35oWH4Gflv9fUpug="
    search = process_results(my_key)
    QUERIES = ["texas longhorns"]
    #QUERIES = ["texas longhorns", "duke blue devils", "dallas cowboys", "dallas mavericks"]
    
    if READCACHE: 
        search_results, topic = read_results()
        search.set_results(search_results, topic)
    else:
        for query in QUERIES:
            print 'Executing queries:', query
            search.query(query)
        search_results, topic = search.get_result_set()
        write_results(search_results, topic)

    tf_idf, dim, idf, doc_topic = search.compute_tf_idf()

