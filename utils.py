# encoding: utf8

import codecs
import os, sys

class Proxy(dict):
    def __init__(self, data={}):
        self.update(data)
    def __setattr__(self, name, value):
        self[name] = value
    def __getattr__(self, name):
        return self[name]

def formatLabel(label,end=False):
    if end:
        label = " \.%s./ "%label
    else:
        label = "   %s   "%label
    print ("###"*10 + "%s" + "###"*10)%label


class LineSplitFileReader(object):

    def __init__(self, filename, encoding, mapper, selector, shouldJoin):
        self.filename = filename;
        self.encoding = encoding;
        self.mapper = mapper;
        self.selector = selector;
        self.shouldJoin = shouldJoin;

    def readFile(self):
        try:
            with codecs.open(self.filename, 'r', self.encoding) as f:
                self._data = f.readlines()
                f.close()
        except IOError as err:
            print("\n\n Cannot read (%s): \n %s.\n check your config file.\n Exiting" % (self.filename, str(err)))
            sys.exit(1)
        else:
            print "lineread:%s\n"%self._data[0].strip()

    def filterInvalidLines(self):

        self.data = map(self.mapper, self._data);
        self.data = filter(self.selector, self.data);
        self.data = map(self.shouldJoin, self.data);

    def __iter__(self):
        for (i,row) in enumerate(self.data):
            yield i, row[0], map(lambda field: field.strip(), row[1])
