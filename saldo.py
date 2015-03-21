# encoding: utf8

"""
            # saldo =  # saldo_MP.txt
            # salda, errlog = parse.start_saldo(saldo)
            # parse.make_saldo_replic(salda, self.config.magisDataDir, self.config.db.yy)

            saldo = SaldoCollection(Proxy({
                "importFile": configParser.get( 'saldo'),
                "magisDataDir": self.config.magisDataDir,
                "yyYearId": self.config.db.yy
            });
            saldo.parse();
            saldo.make_replic()
"""
from collections import OrderedDict
from utils import Proxy

class LineSplitFileReader(object):

    def __init__(self, filename, mapper, selector, shouldJoin):
        self.filename = filename;
        self.mapper = mapper;
        self.selector = selector;
        self.shouldJoin = shouldJoin;

    def readFile(self):
        try:
            with open(self.filename) as f:
                self.data = f.readlines()
        except IOError as err:
            print("\n\n Cannot read (%s): \n %s.\n check your config file.\n Exiting" % (self.filename, str(err)))
            sys.exit(1)
        else:
            f.close()

        self._data = open(self.filename).readlines()

    def filterInvalidLines(self):

        self.data = map(self.mapper, self._data);
        self.data = filter(self.selector, self.data);
        self.data = map(self.shouldJoin, self.data);

    def __iter__(self):
        for (i,row) in enumerate(self.data):
            yield i, row[0], map(lambda field: field.strip(), row[1])

# joiner = 

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

    mapper = lambda self,line: ANSI(line).split(self.lineSplitChar)[1:-1] # in super
    selector = lambda self,fields: (len(fields) == self.lineSplitFieldsRequired) and (not fields[0] or ANSI(fields[0]) not in ANSI(self.options.skips)) # in super
    shouldJoin = lambda self,fields: (len(fields[-1].strip())==0, fields)

    # exports
    saldo_start_line = ''.join([
        "15~1~01.01.20%s~0000000001~!~0000000000~_______R________~1~0000000000~",
        "0.000000000000000e+000~"*3,"!~0~!~!~!~!~!~!~!~!~!~!~","0.000000000000000e+000~"*23, '\n'])
    saldo_artikul_line = "15~0~%s~01.01.20%s~%.15e~%.15e~%.15e~\n"


    def __init__(self, options):
        self.options = options;

        # self.products = options.products; #ArtKeyGOD
        self.products = [];
        self.data = [];
        self.errors = [];

        self.fileWorker = LineSplitFileReader(options._import, self.mapper, self.selector, self.shouldJoin) # in super

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

def start_saldo(fn='saldo_MP.txt'):
    """
     |15027     |Капачка 63 А                       |       18.00|      0.10|      1.35|      0.92|        1.80|       24.30|       16.56|
     |15029     |Клема 2,5 мм                       |        1.00|      0.55|      0.85|      0.58|        0.55|        0.85|        0.58|
     |          |двуполюсна                         |            |          |          |          |            |            |            |
     |          |порцелан                           |            |          |          |          |            |            |            |
     |15030     |Клема 2,5 мм                       |        3.00|      0.75|      1.15|      0.78|        2.25|        3.45|        2.34|
     |          |триполюсна                         |            |          |          |          |            |            |            |
     |          |порцелан                           |            |          |          |          |            |            |            |
     |15095     |Ключ несв. Н. К                    |        1.00|      1.30|      1.96|      1.31|        1.30|        1.96|        1.31|
     |          |/ калпазанче /                     |            |          |          |          |            |            |            |
    """
    art_key_generator = ArtKeyGOD()
    salda = []
    errlog = []
    for i,line in enumerate(open(fn).readlines()):
        line = ANSI(line)
        line = line.split('|')[1:-1]
        if len(line) < 9:
            continue
        if not line[-1].strip():
            #many lines
            last_saldo = salda[-1]
            kwa = dict(art_name = ' '.join([last_saldo.name, line[1].strip()]))
            for nm in "magis_id MP_id qty price_bought price_bought_total".split(' '):
                kwa[nm] = getattr(last_saldo, nm)
            salda[-1] = SalDo(**kwa)
            continue

        assert line[-1].strip()
        assert len(line) == 9,line
        try: 
            float(line[2])
        except ValueError:
            continue
        MP_id = line[0].strip()
        art_name = line[1].strip()
        qty = float(line[2]) #quantity
        #~ p1, p2, p3, p4, p5, p6 = map(float, line[-6:])
        #~ assert abs(p6/qty - p3) < 1e-10, (p6/qty,p3)
        # price_bought = float(line[6]) / qty
        price_bought_total = float(line[6])
        salda.append(SalDo(MP_id, art_name, qty, price_bought_total))
    return salda, errlog


from dosutil import ANSI, ANSI2OEM
import os, sys
#~ from vikBoiana import parse as scet_parse

# import encodings
# if encodings.search_function('mbcs') is None:
#     encodings._cache['mbcs'] = encodings.search_function('866')
cyr = """А а	Б б	В в	Г г	Д д	Е е	Ж ж	З з	И и	Й й	
К к	Л л	М м	Н н	О о	П п	Р р	С с	Т т	У у	
Ф ф	Х х	Ц ц	Ч ч	Ш ш	Щ щ	Ъ ъ	Ь ь	Ю ю	Я я"""
cyrtr = {}
for kv in cyr.split('	'):
    kv = kv.strip()
    k,v = kv.split()
    cyrtr[v] = k
def upper(s):
    for lower, upper in cyrtr.items():
        s = s.replace(lower, upper)
    return s
# if __debug__:
#     print upper(cyr)
#     print cyr.upper()


saldo_artikul_line = "15~0~%s~01.01.20%s~%.15e~%.15e~%.15e~\n"

def make_saldo_replic(salda, data_path, yy):
    fn = "replic01.%s"% yy #01 is saldo
    saldo_writer = open(os.path.join(data_path, fn), 'w+')
    saldo_writer.write(saldo_start_line%yy)
    saldo_writer.writelines([s.toexport_string(yy) for s in salda])

class SalDo(object):
    meassure = "бр."
    def __init__(self, magis_id, MP_id, art_name, qty, price_bought_total):
        self.magis_id = magis_id
        self.MP_id = MP_id
        self.name = art_name
        self.qty = qty
        self.p1 = self.price_bought
        self.p2 = self.price_bought_total = price_bought_total
    @property
    def price_bought(self):
        return self.price_bought_total / self.qty
    
    @property
    def magis_id(self):
        return art_key_generator.get_key(MP_id)
    
    def toexport_string(self, yy):
        '15~0~102657~01.01.2013~1.000000000000000e+000~5.570000000000000e+000~1.114000000000000e+000~'
        return saldo_artikul_line % (self.magis_id, yy, self.qty, self.p1, self.p2)


if __name__ == '__main__':
    # execfile("SelectMP.py")
    import unittest

    unittest.main(argv=[__file__,
    #~ 'test_DNEV_parser',
    ])
