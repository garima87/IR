import os
import sys
import re
import operator
from optparse import OptionParser
from os import listdir
from os.path import isfile, join
from sets import Set
import time
import cPickle

"""
mdict class for storing multiple entries corresponding to a key
"""
class mdict(dict):
  def __setitem__(self, key, value):
    """add the given value to the list of values for this key"""
    self.setdefault(key, []).append(value)

"""
Global dictionary and key to doc name map
"""
global_dict = {}
k_gram = {}
id_name = {}

def read_index(index_file):
    global global_dict, k_gram, id_name
    fh = open(index_file, 'rb')
    global_dict = cPickle.load(fh)
    k_gram = cPickle.load(fh)
    id_name = cPickle.load(fh)
    fh.close()

def write_to_file(file_name):
    fh = open(file_name, 'wb')
    cPickle.dump(global_dict, fh)
    cPickle.dump(k_gram, fh)   
    cPickle.dump(id_name, fh) 
    fh.close()


def tokenize(line):
    line = line.lower()
    word_list = re.findall(r"[\w]+", line)
    return word_list

def find_posting_list(keys):
    query_list = []
    for key in keys:
        if key not in global_dict:
            return None
        else:
            query_list.append(global_dict[key])
    return query_list

def build_k_gram():
    for k in global_dict.iterkeys():
        key = "$" + k + "$"
        for i in xrange(len(key)-1):
            gram = key[0+i:2+i]
            if gram in k_gram:
                k_gram[gram].add(k)
            else:
                k_gram[gram] = Set([k])

"""
Function to build global index for the search
"""
def build_index(dir_name, file_list):
    doc_id = 0
    # Generate the index for each file in the file list
    for name in file_list:
        doc_id += 1
        id_name[doc_id] = name
        # Append the directory name to the file name
        file_name = dir_name + "/" + name
        fh = open(file_name, 'r')
        index = 0
        localdict = {}
        # Process one line at a time and create a local dictionary to the file 
        for line in fh:
            word_list = tokenize(line)
            for word in word_list:
                if word in localdict:
                    localdict[word].add(index)
                else:
                    localdict[word] = Set([index])
                index += 1
    
        # Merge the local dictionary with the global dictionary
        for key, value in localdict.iteritems():
            posting = doc_id, value
            if key in global_dict:
                feq, list2 = global_dict[key]
                list2.append(posting)
                global_dict[key] = feq+1, list2
            else:
                global_dict[key] = 1, [posting] 
    build_k_gram() 

def merge_docs(doc_list):
    temp_list = doc_list[0]
    for docs2 in doc_list[1:]:
        temp_list.intersection_update(docs2)
    return temp_list

"""
Function to process boolean query
"""
def bool_query(query):
    # Tokenize the query the same way we tokenized documents
    query_key = tokenize(query)
    # Generate the list of postings corresponding to each keyword 
    query_list = find_posting_list(query_key)
    if query_list == None: return None
    # Sort the generated postings according to their frequency to increase efficiency
    query_list.sort(key=lambda tup: tup[0])
    temp_list = query_list[0]
    if len(query_key) == 1:
        freq1, ret_value = temp_list
        return zip(*ret_value)[0]

    # Merge all the postings
    for doc_data in query_list[1:]:
        freq1, doc_list1 = temp_list
        freq2, doc_list2 = doc_data
        doc1 = Set(zip(*doc_list1)[0])
        doc2 = Set(zip(*doc_list2)[0])
        com_docs = doc1.intersection(doc2)
        temp_list = freq2, com_docs
 
    freq, ret_value = temp_list
    return ret_value

def search_phrase(phrase):
    query_key = tokenize(phrase)
    # Generate the list of postings corresponding to each keyword 
    query_list = {}
    pos_index = {}
    count = 0
    for key in query_key:
        if key not in global_dict:
            return None
        else:
            query_list[key] = global_dict[key]
            pos_index[key] = count
            count += 1

    query_list = sorted(query_list.iteritems(), key=lambda x: operator.itemgetter(1)(x)[0])
    
    first_index = 0
    key, value = query_list[0]
    first_index = pos_index[key] 
     
    freq, temp_list = value

    # Merge all the postings
    for key, doc_data in query_list[1:]:
        count1 = 0
        count2 = 0
        doc_list = temp_list
        temp_list = []
        freq, docs = doc_data
        diff = pos_index[key] - first_index
        first_index = pos_index[key]
        #merge the already existing doc ids with a new keyword
        while count1 < len(doc_list) and count2 < len(docs):
            doc_id1, list1 = doc_list[count1]
            doc_id2, list2 = docs[count2]

            if doc_id1 < doc_id2:
                count1 += 1
            elif doc_id2 < doc_id1:
                count2 += 1
            else:
                modified_list = Set(map(lambda x: x+diff, list1))
                new_list = modified_list.intersection(list2)
                if new_list:
                    temp_list.append((doc_id1, new_list))
                count1+=1
                count2+=1   
    doc_list = zip(*temp_list)[0]
    return doc_list

"""
Find the documents containing the phrase query
"""
def phrase_query(phrases):
    # Extract phrases from the input
    doc_list = []
    for phrase in phrases:
        doc_list.append(search_phrase(phrase))
    
    return merge_docs(doc_list)

def get_file_list(dir_name):
    file_list = []
    for (dirpath, dirname, filenames) in os.walk(dir_name):
        file_list.extend(filenames)
        break
    return file_list

def get_matching_words(grams):
    working_set = k_gram[grams[0]]
    for gram in grams[1:]:
        if gram in k_gram:
             working_set = k_gram[gram].intersection(working_set)
        else:
            return None
    return working_set

def get_grams(query):
    original_query = query
    query = re.sub("^(?!\*)", "$", query)
    query = re.sub("$(?<!\*)", "$", query)
    grams = []
    for i in xrange(len(query)-1):
       if query[0+i] == '*' or query[1+i] == '*':
           continue
       grams.append(query[0+i:2+i])
    matches = get_matching_words(grams)

    expr = re.sub("^(?!\*)", "^", original_query)
    expr = re.sub("$(?<!\*)", "$", expr)
    expr = expr.replace('*', '.*')
    

    final_match = []
    for match in matches:
        chk_match = re.findall(expr, match)
        if chk_match:
            match_str = ''.join(chk_match)
            final_match.append(match_str)
    
    posting_list = find_posting_list(final_match) 
    for key in final_match:
        if key in global_dict:
            posting_list.append(global_dict[key])

    doc_list = Set([])
    for posting in posting_list:
       freq, p_list = posting
       p_list = Set(zip(*p_list)[0])
       doc_list = doc_list.union(p_list)
    
    return doc_list


if __name__ == '__main__':
    """
    Main function for the code, where the execution starts
    """
    #parse command line options 
    parser = OptionParser()

    parser.add_option("-d", "--directory", action="store", type="string", dest="dir_name", help = "directory in which the documents exist")
    parser.add_option("-b", action="store_true", dest="store_index", help = "store index in a file or not")
    parser.add_option("-i", action="store_true", dest="build_index", help = "create and index")
    parser.add_option("-f", "--index_file", action="store", type="string", dest="index_file", help = "read index from the file", default=None)


    (options, args) = parser.parse_args(sys.argv)
    if options.build_index:
        print "Building index............."
        file_list = get_file_list(options.dir_name)
        build_index(options.dir_name, file_list)
        if options.store_index:
            write_to_file("index_file")

    if options.index_file:
        read_index(options.index_file)

    print "Done with building index........."
    print "Input query to search, Enter to exit"
    query = raw_input()
    while query:
        query = query.lower()
        phrases = re.findall(r'\"(.+?)\"', query)
        final_list = []
        if phrases:
            for phrase in phrases:
                query = query.replace(phrase, "")  
            final_list.append(phrase_query(phrases))
        query = query.replace("\"", "")
     
        for phrase in query.split():
            if phrase.find('*') != -1: 
                query = query.replace(phrase, "")  
                final_list.append(get_grams(phrase))
   
        if query !="" and (not query.isspace()):
            final_list.append(bool_query(query))

        final = merge_docs(final_list)
        if not final:
            print "No document found :("
            print "Input query to search, Enter to exit"
            query = raw_input()
            continue
        for doc_id in final:
            print (id_name[doc_id]) , 
        print "\nInput query to search, Enter to exit"
        query = raw_input()
    print "Exiting"

       
