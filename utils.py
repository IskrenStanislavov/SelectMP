# encoding: utf8
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

