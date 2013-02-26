import json
import re
import scipy
import math
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from numpy.linalg import solve, norm
from numpy.random import rand

"""
mdict class for storing multiple entries corresponding to a key
"""
class mdict(dict):
  def __setitem__(self, key, value):
    """add the given value to the list of values for this key"""
    self.setdefault(key, []).append(value)

tweet_dict = {}

if __name__ == '__main__':
    global global_dict, tf 
    global_dict = {} 
    tf = {}
    fh = open("mars_tweets_medium.json", 'r');
    tweet_id = 1
    #Parse the file, tokenize it and 
    for line in fh:
        local_dict = {}
        data = json.loads(line)
        data = data.lower()
        #Split the words according to the regex
        words = re.split(r'\W+', data['text'], flags=re.UNICODE)
        #create a local dictionary of words
        for word in words:
            if word in local_dict:
                local_dict[word] = local_dict[word] + 1
            else:
                local_dict[word] = 1

        #Merge the local dictionary to the global one
        for word in local_dict:
            if word in global_dict:
                global_dict[word][tweet_id] = local_dict[word]
            else:
                global_dict[word] = {tweet_id: local_dict[word]}
        tweet_id = tweet_id + 1

    #
    for word in global_dict:
        tf[word] = len(global_dict[word])/tweet_id

    A = lil_matrix((len(global_dict)+1, tweet_id+1))

    count = 1
    #Compute the tf-idf 
    for wrd_key, doc_list in global_dict.iteritems():
        for key, value in doc_list.iteritems():
            A[count, key] = math.log(value)
        count = count +1
    for word in tf:

            #A[wrd_key, key] = value


    

