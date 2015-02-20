# encoding:cp1251
from dosutil import ANSI, ANSI2OEM
import parse

import time, os
import ConfigParser
from datetime import datetime

class Proxy(dict):
    def __init__(self, data={}):
        self.update(data)
    def __setattr__(self, name, value):
        self[name] = value
    def __getattr__(self, name):
        return self[name]

class IniParser(ConfigParser.ConfigParser):
    def __init__(self, ini_path="SelectMP.ini"):
        ConfigParser.ConfigParser.__init__(self)
        #os.path.splitext(__file__)[0] +'.ini'
        self.read(self.ini_path)

        self.paths                          = Proxy()
        self.paths.magisDB                  = self.get('magisPath')
        self.paths.importFiles              = self.get('import_path')
        self.paths.magisDataDir             = os.path.join(config.paths.magisDB, "data/", str(obj).zfill(8))

        self.files                          = Proxy()
        self.files.products                 = self.get('art_id_file')
        self.files.saldo                    = self.get('saldo')
        self.files.contractors              = self.get('contr_id_file')
        self.files.dolphine_dealers_file    = os.path.join(cfg.paths.importFiles, self.get('dealers'))
        self.files.file_dost                = self.get('file_dost') #'dost_MP.PRN'
        self.files.file_prod                = self.get('file_prod') #'prod_MP.PRN'

        self.files.export                   = Proxy()
        self.files.export.artikuli          = os.path.join(self.paths.magisDB, 'artikuli-new.txt')
        self.files.export.kontragenti       = os.path.join(self.paths.magisDB, 'contragenti-new.txt')


        self.db                             = Proxy()
        self.db.obj                         = self.getint("obj1", 1)
        self.db.yy                          = self.get("yy") # 2 digits year format

        self.options                        = Proxy()
        self.options.import_saldo           = self.getint("saldo_import_run", 0)

        self.errors                         = Proxy()
        self.errors.missingEIK              = "Липсва ЕИК към %s № (%s) от дата:%s; "
        self.errors.timeStamp               = "\n\n!!! Date & time: %s\n"%(datetime.now())
