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
from computeVector import *
from sets import Set

READCACHE = True
WRITECACHE = False
MAX_ITER = 20
pp = pprint.PrettyPrinter(depth = 6)
filename1 = "results.txt"
filename2 = "topic"

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

"""
This class implements the main clustering algorithm.
As input, it takes the tf-idf vector for each documents, and clusters these documents based on it.
"""
class Cluster():
    """Initializer for the cluster class
       Input - tf_idf       tf_idf vectors for each document
               dim          magnitude of each vector
               doc_topic    true classification of each document
    """
    def __init__(self, tf_idf, dim, doc_topic):
        self.no_docs = len(tf_idf)
        self.actual_cluster = doc_topic
        self.tf_idf = tf_idf
        self.clusters = {}
        self.centroids = {}
        self.centroids = {}
        self.centroids_dim = {}
        self.dim = dim

    """Function to find the initial random centroids. 
       It takes as input the number of cluster, and picks that many random centroids from the input set of documents
       Input - number of clusters
    """
    def get_initial_seeds(self, no_clusters):
        num =  random.sample(xrange(1, self.no_docs), no_clusters)
        for count in xrange(0, no_clusters):
            self.centroids[count] = self.tf_idf[num[count]]
            self.centroids_dim[count] = self.dim[num[count]]
    
    """Computes the cosine similarity of two vectors
       Input - 
            vec1 - tf_idf vector
            vec2 - tf_idf vector
       Output - their cosine similarity
    """
    def compute_cos(self, vec1, vec2):
        cos_vector = dict( (n, (vec1.get(n, 0) * vec2.get(n, 0)))  for n in set(vec2).intersection(set(vec1)) )
        cos_sim = sum(cos_vector.itervalues())
        return cos_sim
    
    """Computes the euclidean distance between two vectors
       Input - 
            vec1 - tf_idf vector
            vec2 - tf_idf vector
       Output - euclidean distance between them
    """
    def compute_euclidean(self,vec1, vec2, dim1, dim2):
        vector_diff = dict( (n, (vec1.get(n, 0)/dim1 - vec2.get(n, 0)/dim2) **2)  for n in set(vec1)|set(vec2) )
        euc_dist = sum(vector_diff.itervalues()) **.5
        return euc_dist
    

    """Computes the cluster to which a document belongs
       Input - 
            doc_vector  - tf_idf vector of the document which needs to be classified
            dim         - magnitude of the vector
            no_clusters - total number of clusters
    """
    def compute_cluster(self, doc_vector, dim, no_clusters):
        max_sim = 0
        cluster = 0
        for key, cent in self.centroids.iteritems():
            sim = self.compute_cos(cent, doc_vector) / (dim * self.centroids_dim[key])
            #As this is cosine similarity, we take the cluster with maximum cosine similarity 
            if sim > max_sim:
                max_sim = sim
                cluster = key

        return cluster

    """Recomputes the magnitude of centroid vectors
    """
    def recompute_dim(self):
        for doc_id, word_list in self.centroids.iteritems():
           dim = 0
           for word, tf in word_list.iteritems():
                dim = dim + math.pow(tf, 2)
                
           #If there is no element in this cluster, set the magnitude of this cluster to 1
           if dim == 0: 
            self.centroids_dim[doc_id] = 1
           else:
            self.centroids_dim[doc_id] = math.pow(dim, .5)


    """
    Functions for computing the performance of clusters
    """
    
    """ Computes the rand_index of the cluster
    Input - 
        clustes - dictionary of all the clusters, and the documents assigned to them
    Output - 
        rand_index for the clusters
    """
    def compute_ri(self, clusters):
        computed_cluster = {}
        TP = 0
        FP = 0
        TN = 0
        FN = 0
        for cluster_id, cluster_docs in clusters.iteritems():
            for doc in cluster_docs:
                computed_cluster[doc] = cluster_id 
        
        for doc_id1 in computed_cluster:
            for doc_id2 in computed_cluster:
                if (doc_id1 == doc_id2):
                    continue
                if (computed_cluster[doc_id1] == computed_cluster[doc_id2]):
                    if(self.actual_cluster[doc_id1] == self.actual_cluster[doc_id2]):
                        TP += 1
                    else:
                        FP += 1
                else:
                    if(self.actual_cluster[doc_id1] == self.actual_cluster[doc_id2]):
                        FN += 1
                    else:
                        TN += 1

        rand_index = (float) (TP + TN) / (TP + TN + FP + FN)
        return rand_index
    
    """
    Computes the RSS for the clusters
    Input - 
        clustes - dictionary of all the clusters, and the documents assigned to them
    Output - 
        rss for the clusters
    """
    def compute_rss(self, clusters): 
        rss = 0
        for cluster_id, doc_list in clusters.iteritems():
            if cluster_id not in self.centroids:
                continue
            cluster_vector = self.centroids[cluster_id]
            distance_sum = 0
            for doc_id in doc_list: 
                doc_vector = self.tf_idf[doc_id]
                euc_dist = (self.compute_euclidean(cluster_vector, doc_vector,self.centroids_dim[cluster_id] , self.dim[doc_id])) **2
                #euc_dist = (self.compute_euclidean(cluster_vector, doc_vector)/(self.dim[doc_id] * self.centroids_dim[cluster_id])) **2
                distance_sum += euc_dist
            rss = rss + distance_sum
        return rss

    """
    Computes the purity for the clusters
    Input - 
        clustes - dictionary of all the clusters, and the documents assigned to them
    Output - 
        purity for the clusters
    """
    def compute_purity(self, clusters):
        purity = 0
        #print "Actual class mapping is %s" %(self.actual_cluster)
        for cluster_id, docs in clusters.iteritems():
            class_count = {}
            for doc in docs:
                actual_class = self.actual_cluster[doc]
                if actual_class not in class_count:
                    class_count[actual_class] = 0
                class_count[actual_class] += 1    
            #pp.pprint(class_count)
            if class_count:
                purity += max(class_count.itervalues())
        
        #print "Docs in same cluster %d" %(purity)
        #print "Total docs %d" %(self.no_docs)
        return (float(purity) / self.no_docs)
        
    """Function called from the main program, to find the cluster distribution given the number of clusters
       Input - no_clusters - number of clusters 
       Output - ri       - rand index for the cluster computed 
                purity   - purity of the cluster computed
                RSS      - rss of the cluster computed
    """
    
    def get_clusters(self, no_clusters):
        #Get the initial set of random points from the cluster
        self.get_initial_seeds(no_clusters)
        best_cluster = {}
        cluster_count = {}  #map for number of documents in each cluster
        cluster_points = {} #map for maintaining the tf_idf sum for the documents seen in a cluster so far
        
        old_clusters = {}   #old cluster distribution 
        clusters = {}       #new cluster distribution
       
        max_ri = 0
        max_purity = 0
        min_rss = 10000
        count = 0
        """We iterate for MAX_ITER times"""
        while count < MAX_ITER:
            count = count + 1
            #print "Iteration is %d" %(count)

            #Initialize loop variables
            cluster_points = {}
            for i in xrange(0, no_clusters):
                cluster_count[i] = 0
                clusters[i] = []
                
            #Loop to iterate through all the documents which need to be classified
            for doc_id, doc in self.tf_idf.iteritems():
                #get the cluster with maximum cosine similarity to the document
                doc_cluster = self.compute_cluster(doc, self.dim[doc_id], no_clusters)

                #append this document to the list of documents belonging to this cluster
                clusters[doc_cluster].append(doc_id)
                cluster_count[doc_cluster] += 1

                #Add the tf_idf of this document to this cluster, used in recomputing the centriod
                if doc_cluster in cluster_points: 
                    cluster_data = cluster_points[doc_cluster]
                    cluster_points[doc_cluster] = dict( (n, cluster_data.get(n, 0)+doc.get(n, 0)) for n in set(cluster_data)|set(doc) )
                else:
                    cluster_points[doc_cluster] = copy.deepcopy(doc)

            #Recompute the centriod
            self.centroids = {}
            for cluster_id, vector in cluster_points.iteritems():
                self.centroids[cluster_id] = dict( (n, cluster_points[cluster_id].get(n)/cluster_count[cluster_id]) for n in set(cluster_points[cluster_id]) )

            for cluster_id in xrange(0, no_clusters):
                if cluster_id not in self.centroids:
                    self.centroids[cluster_id] = {}

            #Recompute the magnitude of the centriods 
            self.recompute_dim()

            #Find the purity, rand_index and rss for the computed cluster
            rss = self.compute_rss(clusters)
            ri = self.compute_ri(clusters)
            purity = self.compute_purity(clusters)

            if rss < min_rss:
                min_rss = rss
                max_purity = purity
                max_ri = ri
                best_cluster = copy.deepcopy(clusters)

               
            #If the cluster mapping hasn't changed from the previous iteration, use a random restart
            if (old_clusters == clusters):
                self.get_initial_seeds(no_clusters)
            old_clusters = copy.deepcopy(clusters)
        return min_rss, max_purity, max_ri, clusters

if __name__ == '__main__':
    my_key = "cwszVgNF2K/L0c8xnG09xOEIxEc35oWH4Gflv9fUpug="
    search =  process_results(my_key)

    filename = "result.txt"
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

    tf_idf, dim, idf, doc_topic = search.compute_tf_idf()
    k_rss = {}
    k_ri = {}
    k_purity = {}
    clus = Cluster(tf_idf, dim, doc_topic)
    rss, purity, ri, clusters = clus.get_clusters(5)  
    for cluster in clusters:
        print 
        print "cluster ", cluster 
        docs = clusters[cluster]
        for doc in docs:
            print QUERIES[doc_topic[doc]], "," ,search_results[doc]

    """
    for no in xrange(2, len(tf_idf), 5):
        clus = Cluster(tf_idf, dim, doc_topic)
        rss, purity, ri = clus.get_clusters(no)  
        k_rss[no] = rss
        k_ri[no] = ri
        k_purity[no] = purity
    
    """
    """
    print "Rss is:"
    for key in sorted(k_rss.keys()):
        print key, k_rss[key]

    print "Purity is:"
    for key in sorted(k_purity.keys()):
        print key, k_purity[key]

    print "Rand index is:"
    for key in sorted(k_ri.keys()):
        print key, k_ri[key]

    """
