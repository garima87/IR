import os
from sets import Set
import cPickle

if __name__ == '__main__':
    d = {}
    fh = open('index_file', 'rb')
    d1 = cPickle.load(fh)
    print d1["ebook"]
    d3 = cPickle.load(fh)
    fh.close()
