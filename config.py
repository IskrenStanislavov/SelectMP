# encoding: utf8
from dosutil import ANSI, ANSI2OEM
import parse

import time, os
import ConfigParser
from datetime import datetime
from utils import Proxy

class IniParser(ConfigParser.ConfigParser):
    def __init__(self, ini_path="SelectMP.ini"):
        ConfigParser.ConfigParser.__init__(self)
        #os.path.splitext(__file__)[0] +'.ini'
        self.read([ini_path,])

        self._export                        = Proxy()
        self._export.path                   = self.get("_export", 'path')
        self._export.data                   = self.get("_export", 'data')

        self._import                        = Proxy()
        self._import.path                   = self.get("_import", 'path')
        # self.paths._exportDataDir         = os.path.join(self._export.path, self._export.path)

        # self.files                          = Proxy()
        # self.files.products                 = self.get("SelectMP", 'art_id_file')

        
        # self.files.contractors              = self.get("SelectMP", 'contr_id_file')
        # self.files.dolphine_dealers_file    = os.path.join(self._import.path, self.get("SelectMP", 'dealers'))
        # self.files.file_dost                = self.get("SelectMP", 'file_dost') #'dost_MP.PRN'
        # self.files.file_prod                = self.get("SelectMP", 'file_prod') #'prod_MP.PRN'

        # self.files.export                   = Proxy()
        # self.files.export.artikuli          = os.path.join(self._export.path, 'artikuli-new.txt')
        # self.files.export.kontragenti       = os.path.join(self._export.path, 'contragenti-new.txt')

        self.saldo = Proxy()
        self.saldo.do                       = self.get("saldo", "do")
        self.saldo.yy                       = self.get("saldo", "YearYY")
        self.saldo._import                  = os.path.join(self._import.path, self.get("saldo", "import_file"))
        self.saldo._export                  = os.path.join(self._export.path, self.get("saldo", "replic"))
        # self.saldo.skips                    = map(lambda line: line.split('|')[1],self.get("saldo", "skips").split())
        self.saldo.skips                    = self.get("saldo", "skips")
        self.errors                         = Proxy()
        self.errors.missingEIK              = "Липсва ЕИК към %s № (%s) от дата:%s; "
        self.errors.timeStamp               = "\n\n!!! Date & time: %s\n"%(datetime.now())

        if __debug__:
            print "skips:\n",self.saldo.skips.split()
