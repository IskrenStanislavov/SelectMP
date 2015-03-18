# encoding: utf8
class Proxy(dict):
    def __init__(self, data={}):
        self.update(data)
    def __setattr__(self, name, value):
        self[name] = value
    def __getattr__(self, name):
        return self[name]
