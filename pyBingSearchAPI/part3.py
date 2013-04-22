import os
import sys
import re
import operator

from computeVector import *
from part1 import *
from part2 import *

filename1 = "results.txt"
filename2 = "topic3"

READCACHE = True
WRITECACHE = False

"""Used for testing, dumps the result of queries from bing to a file, so that they can be used later"""
def read_results():
    searchresults_file = open(filename1, 'rb')
    search_results = marshal.load(searchresults_file)
    searchresults_file.close()
    searchresults_file = open(filename2, 'rb')
    topic = marshal.load(searchresults_file)
    searchresults_file.close()
    return search_results, topic


def write_results(search_results, topic):
    print 'Saving search results.'
    searchresults_file = open(filename1, 'wb')
    marshal.dump(search_results, searchresults_file)
    searchresults_file.close()
    searchresults_file = open(filename2, 'wb')
    marshal.dump(topic, searchresults_file)
    searchresults_file.close()

class documentPreprocessing():
    def __init__(self, documents):
        self.docs = documents
        self.stop_words_list = ["a","able","about","across","after",
                                "all","almost","also","am","among",
                                "an","and","any","are","as","at",
                                "be","because","been","but","by",
                                "can","cannot","could","dear","did",
                                "do","does","either","else","ever",
                                "every","for","from","get","got","had",
                                "has","have","he","her","hers","him","his",
                                "how","however","i","if","in","into","is",
                                "it","its","just","least","let","like",
                                "likely","may","me","might","most","must",
                                "my","neither","no","nor","not","of","off",
                                "often","on","only","or","other","our","own",
                                "rather","said","say","says","she","should",
                                "since","so","some","than","that","the","their",
                                "them","then","there","these","they","this","tis",
                                "to","too","twas","us","wants","was","we","were",
                                "what","when","where","which","while","who","whom",
                                "why","will","with","would","yet","you","your"]

    def remove_stopwords(self):
        for doc_id in self.docs.keys():
            orig_data = " " + self.docs[doc_id] + " "
            new_data = orig_data.lower()
            for word in self.stop_words_list:
                word = " " + word + " "
                new_data = new_data.replace(word, "")
            self.docs[doc_id] = new_data

        return self.docs
    
    def remove_stopwords_list(self):
        for doc_id in xrange(0, len(self.docs)):
            orig_data = " " + self.docs[doc_id] + " "
            new_data = orig_data.lower()
            for word in self.stop_words_list:
                word = " " + word + " "
                new_data = new_data.replace(word, "")
            self.docs[doc_id] = new_data
        return self.docs
            

    def compute_top_words(self, no):
        word_freq = {}
        print "Total documents %d" %(len(self.docs))
        for doc_id in self.docs.keys():
            words = re.split(r'\W+', self.docs[doc_id])
            for word in words:
                if word not in word_freq:  word_freq[word] = 0
                word_freq[word] += 1
        
        self.top_words = set(zip(*(sorted(word_freq.iteritems(), key=operator.itemgetter(1), reverse=True))[:no])[0])
        return self.top_words
    
def clustering(my_key):
    search =  process_results(my_key)
    filename = "result3.txt"
    QUERIES = ["texas aggies", "texas longhorns", "duke blue devils", "dallas cowboys", "dallas mavericks"]
    
     
    if READCACHE: 
        search_results, topic = read_results()
        search.set_results(search_results, topic)
    else:
        search_results = {}
        for query in QUERIES:
            print 'Executing queries:', query
            search.query(query)

        search_results, topic = search.get_result_set()

    if WRITECACHE:
        write_results(search_results, topic)

    process = documentPreprocessing(search_results)
    search_results = process.remove_stopwords()
    top_words = process.compute_top_words(50)
    tf_idf, dim, idf, doc_topic = search.compute_tf_idf(top_words)
    clus = Cluster(tf_idf, dim, doc_topic)
    rss, purity, ri, clusters = clus.get_clusters(5)  
    for cluster in clusters:
        print 
        print "cluster ", cluster 
        docs = clusters[cluster]
        for doc in docs:
            print QUERIES[doc_topic[doc]], "," ,search_results[doc]

def improved_train(my_key):
    search = Search(my_key)
    TRAIN_QUERIES = ["bing", "amazon", "twitter", "yahoo", "google",
             "beyonce", "bieber", "television", "movies", "music",
             "obama", "america", "congress", "senate", "lawmakers"]
    filename = "result2.txt"
    search_result = {}
    if READCACHE: 
        search_result = read_results2(filename, search_result)
    else:
        for query in TRAIN_QUERIES:
            print 'Executing queries:', query
            result = search.category_search(query)
            for category in result:
                if category not in search_result:   
                    search_result[category] = []
                search_result[category].extend(result[category])
        
        write_results2(filename, search_result)
    
    for category in search_result:
        process = documentPreprocessing(search_result[category])
        search_result[category] = process.remove_stopwords_list()
    
    classifier = naiveBayesClass(search_result)
    #Train the classifier with the training queries
    classifier.train_classifier()
    return classifier

def classification(my_key):
    classifier = improved_train(my_key)
    original_category_map, classification, categories, test_result = test_classifier(classifier)
    for cat in categories:
        print "\"", cat, "\""
        for doc, cate in classification.iteritems():
            if cate == cat:
                print original_category_map[doc], ",", test_result[doc]
    performance = computePerformance(original_category_map, classification, categories)
    performance.computeTableConfusion()
    performance.computeConfusionMatrix()
    
if __name__ == "__main__":
    my_key = "cwszVgNF2K/L0c8xnG09xOEIxEc35oWH4Gflv9fUpug="
    clustering(my_key)
    classification(my_key) 
