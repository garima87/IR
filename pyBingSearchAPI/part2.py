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

from computeVector import *

READCACHE = True
WRITECACHE = False
pp = pprint.PrettyPrinter(depth = 6)

def read_results2(filename, search_results):
    searchresults_file = open(filename, 'rb')
    search_results = marshal.load(searchresults_file)
    searchresults_file.close()
    return search_results


def write_results2(filename, search_results):
    print 'Saving search results.'
    searchresults_file = open(filename, 'wb')
    marshal.dump(search_results, searchresults_file)
    searchresults_file.close()

class computePerformance():
    def __init__(self, true_class, computed_class, categories):
        self.true_class = true_class
        self.computed_class = computed_class
        self.categories  = categories
        self.table_confusion = {}
        self.confusion_matrix = {}
        self.TP = 0
        self.FP = 0
        self.TN = 0
        self.FN = 0

    def computeTableConfusion(self):
        #print self.true_class
        #print self.computed_class
        for doc_id, category in self.true_class.iteritems(): 
            if category not in self.table_confusion:
                #print "Initializing true cat", category
                self.table_confusion[category] = {}
            com_category = self.computed_class[doc_id]
            if com_category not in self.table_confusion[category]:
                self.table_confusion[category][com_category] = 0
                #print "Initializing comp cat", category, com_category
            self.table_confusion[category][com_category] += 1
            
        #pp.pprint(self.table_confusion)

    def computeConfusionMatrix(self):
        for category in self.categories:
            if category in self.table_confusion[category]:
                TP = self.table_confusion[category][category]
            else:
                TP = 0
            self.TP += TP
            FN = 0
            FP = 0
            for diff_category in self.categories:
                if diff_category == category:
                    continue
                if diff_category in self.table_confusion[category]:
                    FN += self.table_confusion[category][diff_category]
                if category in self.table_confusion[diff_category]:
                    FP += self.table_confusion[diff_category][category]
            self.FN += FN
            self.FP += FP

        P = (float)(self.TP) / (self.TP + self.FP)
        R = (float)(self.TP) / (self.TP + self.FN)


        F = 2 * P * R / (P+R)

        #print "F is %s" %(F)

"""
Naive Bayes classifier, that builds a probability model based on training data, and does classification based on it
"""
class naiveBayesClass():
    def __init__(self, result_set):
        self.classes = result_set.keys()
        self.result_set = {}
        for c_class in result_set:
            self.result_set[c_class] = ""
            for result in result_set[c_class]:
                self.result_set[c_class] += result
                
        self.class_prob = {}
        self.word_prob = {}
        self.nan = {}
        self.total_docs = sum(len(val) for val in result_set.itervalues())

    def train_classifier(self):
        """ Find the probability of each class"""
        for c_class in self.classes:
            self.class_prob[c_class] = math.log(float(len(self.result_set[c_class])) / self.total_docs, 2)
            #print "Class: %s, prob: %d" %(c_class, self.class_prob[c_class])

        """Find the probability of each document"""
        
        """count the total number of unique terms"""
        words_map = {}
        unique_word = 0
        for c_class in self.classes:
            data = self.result_set[c_class]
            words = re.split(r'\W+', data)
            for word in words:
                if word not in words_map:
                    unique_word += 1
                    words_map[word] = 1

        for c_class in self.classes:
            data = self.result_set[c_class]
            words = re.split(r'\W+', data)
            local_word_count = {}
            for word in words:
                if word not in local_word_count:
                    local_word_count[word] = 0
                local_word_count[word] += 1

            num_words = len(words)
            for word in local_word_count:
                if word not in self.word_prob:
                    self.word_prob[word] = {}
                self.word_prob[word][c_class] = math.log((float)(local_word_count[word] + 1) / (num_words + unique_word), 2)
            self.nan[c_class] = math.log((float) (1)/ (num_words + unique_word), 2)
            #print c_class, num_words, unique_word
        
     
   
        """
        for word in self.word_prob:
            print "%s, %s" %(word, self.word_prob[word])
        """

    def classify_doc(self, test_set):
         """Classify the documents based on naive bayes classification scheme"""
         #print "Number of docs are %d" %(len(test_set))
         doc_category_map = {}
         doc_id = 0
         for docs in test_set:
            words = re.split(r'\W+', docs)
            doc_class_prob = {}
            for category in self.classes:
                doc_class_prob[category] = self.class_prob[category]

            for word in words:
                for category in self.classes:
                    if word not in self.word_prob:
                        continue
                    if category not in self.word_prob[word]:
                        doc_class_prob[category] += self.nan[category]
                    else:
                        doc_class_prob[category] += self.word_prob[word][category]
            
            max_prob = -1000000
            doc_category = None
            for category in self.classes:
                #pp.pprint(doc_class_prob)
                if (doc_class_prob[category] > max_prob):
                    max_prob = doc_class_prob[category]
                    doc_category = category
            
            doc_category_map[doc_id] = doc_category
            doc_id += 1
         return doc_category_map

def train(my_key):
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
    classifier = naiveBayesClass(search_result)
    #Train the classifier with the training queries
    classifier.train_classifier()
    return classifier

def test_classifier(classifier):
    filename = "test_result.txt"
    filename1 = "true_class.txt"
    TEST_QUERIES = ["apple", "facebook", "westeros", "gonzaga", "banana"]

    test_result = []
    categories = ["rt_Entertainment", "rt_Business", "rt_Politics"]
    original_category_map = {}
    if READCACHE: 
        test_result = read_results2(filename, test_result)
        original_category_map = read_results2(filename1, original_category_map)
    else:
        search_result = {}
        for query in TEST_QUERIES:
            print 'Executing queries:', query
            result = search.category_search(query)
            for category in result:
                if category not in search_result:   
                    search_result[category] = []
                search_result[category].extend(result[category])
        
        doc_id = 0
        #Generate 10 random from each category to get test set
        for category in search_result:
            result = search_result[category]
            rand_nums =  random.sample(xrange(0, len(result)), 10)
            for num in rand_nums:
               test_result.append(result[num])
               original_category_map[doc_id] = category   
               doc_id += 1
                
        write_results2(filename, test_result)
        write_results2(filename1, original_category_map)
        
    classification = classifier.classify_doc(test_result)
    return original_category_map, classification, categories, test_result

if __name__ == '__main__':
    my_key = "cwszVgNF2K/L0c8xnG09xOEIxEc35oWH4Gflv9fUpug="
    classifier = train(my_key)
    original_category_map, classification, categories, test_result = test_classifier(classifier)
    for cat in categories:
        print "\"", cat, "\""
        for doc, cate in classification.iteritems():
            if cate == cat:
                print original_category_map[doc], ",", test_result[doc]
    
    performance = computePerformance(original_category_map, classification, categories)
    performance.computeTableConfusion()
    performance.computeConfusionMatrix()
