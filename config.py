# encoding:cp1251
from dosutil import ANSI, ANSI2OEM
import parse

import time, os
import ConfigParser
from datetime import datetime
from proxy import Proxy

class IniParser(ConfigParser.ConfigParser):
    def __init__(self, ini_path="SelectMP.ini"):
        ConfigParser.ConfigParser.__init__(self)
        #os.path.splitext(__file__)[0] +'.ini'
        self.read([ini_path,])

        self.db                             = Proxy()
        self.db.obj                         = self.getint("SelectMP", "obj1")
        self.db.yy                          = self.get("SelectMP", "yy") # 2 digits year format

        self.paths                          = Proxy()
        self.paths.magisDB                  = self.get("SelectMP", 'magisPath')
        self.paths.importFiles              = self.get("SelectMP", 'import_path')
        self.paths.magisDataDir             = os.path.join(self.paths.magisDB, "data/", str(self.db.obj).zfill(8))

        self.files                          = Proxy()
        self.files.products                 = self.get("SelectMP", 'art_id_file')
        self.files.saldo                    = self.get("SelectMP", 'saldo')
        self.files.contractors              = self.get("SelectMP", 'contr_id_file')
        self.files.dolphine_dealers_file    = os.path.join(self.paths.importFiles, self.get("SelectMP", 'dealers'))
        self.files.file_dost                = self.get("SelectMP", 'file_dost') #'dost_MP.PRN'
        self.files.file_prod                = self.get("SelectMP", 'file_prod') #'prod_MP.PRN'

        self.files.export                   = Proxy()
        self.files.export.artikuli          = os.path.join(self.paths.magisDB, 'artikuli-new.txt')
        self.files.export.kontragenti       = os.path.join(self.paths.magisDB, 'contragenti-new.txt')


        self.options                        = Proxy()
        self.options.import_saldo           = self.getint("SelectMP", "saldo_import_run")

        self.errors                         = Proxy()
        self.errors.missingEIK              = "Липсва ЕИК към %s № (%s) от дата:%s; "
        self.errors.timeStamp               = "\n\n!!! Date & time: %s\n"%(datetime.now())
