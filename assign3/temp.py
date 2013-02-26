import os

class mdict(dict):
  def __setitem__(self, key, value):
    """add the given value to the list of values for this key"""
    self.setdefault(key, []).append(value)


if __name__ == '__main__':
    dic = {}
    dic[u'garima'] = 1 
    dic[u'garima'] = dic[u'garima'] + 1
    print dic[u'garima']
