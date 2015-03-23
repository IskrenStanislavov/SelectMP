# encoding: utf8
from collections import OrderedDict
from utils import Proxy
from dosutil import ANSI, ANSI2OEM

from utils import LineSplitFileReader
from utils import FileSaver


"""
  Контрагенти                   
 +----------+--------------------------------+---------------+--------------------------------+-----------------+-----------------+----------------------+
 | Код      | Име                            | ЕИК/ЕГН       | Адрес                          | Телефон         | Факс            | e-mail               |
 +----------+--------------------------------+---------------+--------------------------------+-----------------+-----------------+----------------------+
 | 1        | ДОМЕЛА ООД                     | 103052149     | гр. Варна, ул."Селиолу", 40А   |                 |                 |                      | 
 | 2        | АССА - АЛЕКСАНДЪР ВАНГЕЛОВ ЕТ  | 813098792     | гр. Варна, ул. "Македония", 35 |                 |                 |                      | 
 | 3        | БОГИ ЕТ                        | 826002475     | гр. Разград, ул. "България", 9 |                 |                 |                      | 
 | 4        | СИОН ГЕЦ ЕООД                  | 117048851     | гр. Русе, ул. "Борисова", 21   |                 |                 |                      | 
 | 5        | ЕЛДО - ПЛАМЕН ПАВЛОВ ЕТ        | 103094618     | гр. Варна, ул. "Ген.Георги Поп |                 |                 |                      | 
 | 6        | АТАНАСОВ И КО ООД              | 117096690     | гр. Русе, ул. "Доростол", 28   |                 |                 |                      | 
 | 7        | МКП БЕЛИЯ ГРАД ООД             | 124713397     | гр. Балчик, ул. "Христо Ботев" |                 |                 |                      | 
 | 8        | ПК НАРКООП ВЪЗХОД              | 833711        | гр. Добрич, ул. "Д-р К.Стоилов |                 |                 |                      | 
 | 9        | ЕЛТИ - СЛАВКА ГАЙДАРДЖИЕВА ЕТ  | 124108697     | гр. Балчик, ж.к. "Балик", бл.2 |                 |                 |                      | 
 | 10       | МОНИ 2003 ООД                  | 124627553     | гр. Добрич, ул. "Гоце Делчев", |                 |                 |                      | 

    contractor = ContractorsCollection(config);
        config.do
        config.yy
        config._import
        config._export
        config.skips
        config.encoding

    contractor.parse();
    contractor.format()

"""
class SaldoCollection(object):
    lineSplitChar = "|"
    lineSplitFieldsRequired = 7
    joinRowMap = {"1":Proxy({
        "name": "contractor_name",
        "cast": str
        })
    }
    checkFieldIndex = 0
    fieldMap = OrderedDict({
        "0":Proxy({
            "name": "MP_id",
            "cast": str
        }), "1":Proxy({
            "name": "name",
            "cast": str
        }), "1":Proxy({
            "name": "UIN",
            "cast": str
        }), "2":Proxy({
            "name": "address",
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
    shouldJoin = lambda self,fields: (len(fields[self.checkFieldIndex].strip())==0, fields)

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

        self.importManager = LineSplitFileReader(options._import, options.encoding._import, self.mapper, self.selector, self.shouldJoin) # in super
        self.exportManager = FileSaver(options._export, options.encoding._export)

    def parse(self):
        self.importManager.readFile()
        self.importManager.filterInvalidLines()
        # lastSaldo = jSaldo()
        jSaldo = OrderedDict();
        for (rowIndex, joinFlag, fields) in self.importManager:
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
        lines =  [self.saldo_start_line%self.options.yy]
        lines += [self.toexport_string(s) for s in self.data]
        self.exportManager.writeLines(lines)
        raise Exception("soon")

if __name__ == '__main__':
    # execfile("SelectMP.py")
    import unittest

    unittest.main(argv=[__file__,
    #~ 'test_DNEV_parser',
    ])
