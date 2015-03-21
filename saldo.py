# encoding: utf8

"""
            saldo = SaldoCollection(config);
                config.do
                config.yy
                config._import
                config._export
                config.skips
                config.encoding

            saldo.parse();
            saldo.format()
"""
from collections import OrderedDict
from utils import Proxy
from dosutil import ANSI, ANSI2OEM

from utils import LineSplitFileReader

class SaldoCollection(object):
    lineSplitChar = "|"
    lineSplitFieldsRequired = 9
    joinRowMap = {"1":Proxy({
        "name": "art_name",
        "cast": str
        })
    }
    checkFieldIndex = -1
    fieldMap = OrderedDict({
        "0":Proxy({
            "name": "MP_id",
            "cast": str
        }), "1":Proxy({
            "name": "art_name",
            "cast": str
        }), "2":Proxy({
            "name": "qty",
            "cast": float
        }), "6":Proxy({
            "name": "price_bought_total",
            "cast": float
        })
    })

    calculatedFields = OrderedDict({
        "price_single":lambda self, data: (data.get("price_bought_total") / data.get("qty")),
        "magis_id": lambda self, data: (self.products.get_native_magis_key(MP_id))
        })
    mapper = lambda self,line: ANSI(line.encode("cp1251")).split(self.lineSplitChar)[1:-1] # in super
    selector = lambda self,fields: (len(fields) == self.lineSplitFieldsRequired) and (not fields[0] or ANSI(fields[0]) not in ANSI(self.options.skips.encode("cp1251"))) # in super
    shouldJoin = lambda self,fields: (len(fields[-1].strip())==0, fields)

    # exports
    saldo_start_line = ''.join([
        "15~1~01.01.20%s~0000000001~!~0000000000~_______R________~1~0000000000~",
        "0.000000000000000e+000~"*3,"!~0~!~!~!~!~!~!~!~!~!~!~","0.000000000000000e+000~"*23, '\n'])
    saldo_artikul_line = "15~0~%s~01.01.20%s~%.15e~%.15e~%.15e~\n"


    def __init__(self, options):
        self.options = options;
        self.products = options.products;
        self.products = [];
        self.data = [];
        self.errors = [];

        self.fileWorker = LineSplitFileReader(options._import, options.encoding, self.mapper, self.selector, self.shouldJoin) # in super

    def parse(self):
        self.fileWorker.readFile()
        self.fileWorker.filterInvalidLines()
        # lastSaldo = jSaldo()
        jSaldo = OrderedDict();
        for (rowIndex, joinFlag, fields) in self.fileWorker:
            if joinFlag:
                #use the same saldo
                fieldMap = self.joinRowMap
            else:
                if jSaldo:
                    self.data.append(jSaldo)
                    jSaldo = OrderedDict();
                fieldMap = self.fieldMap

            for (i, fieldValue) in enumerate(fields):
                fieldCfg = fieldMap.get(str(i), None)
                if fieldCfg is not None:
                    jSaldo[fieldCfg.name] = fieldCfg.cast(jSaldo.get(fieldCfg.name, "") + fieldValue)
        if jSaldo:
            self.data.append(jSaldo)

    def toexport_string(self, s):
        yy = self.options.yy
        s["price_single"] = s.get("price_bought_total") / s.get("qty")
        return self.saldo_artikul_line%(s.get("magis_id"), yy, s.get("qty"), s.get("price_single"), s.get("price_bought_total"))

    def format(self):
        fn = self.options.get("replic")
        with open(self.options._export, 'w+') as saldo_writer:
            lines =  [self.saldo_start_line%self.options.yy]
            lines += [self.toexport_string(s) for s in self.data]
            saldo_writer.writelines(lines)
            saldo_writer.close()
        raise Exception("soon")

if __name__ == '__main__':
    # execfile("SelectMP.py")
    import unittest

    unittest.main(argv=[__file__,
    #~ 'test_DNEV_parser',
    ])
