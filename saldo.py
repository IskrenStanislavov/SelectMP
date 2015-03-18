# encoding: utf8

from dosutil import ANSI, ANSI2OEM
import os, sys
#~ from vikBoiana import parse as scet_parse

import encodings
if encodings.search_function('mbcs') is None:
    encodings._cache['mbcs'] = encodings.search_function('cp1251')
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
if __debug__:
    print upper(cyr)

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
        line = line.split('|')[1:-1]
        line = ANSI(line)
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
        price_bought = float(line[6]) / qty
        price_bought_total = float(line[6])
        magis_id = art_key_generator.get_key(MP_id)
        salda.append(SalDo(magis_id, MP_id, art_name, qty, price_bought, price_bought_total))
    return salda, errlog

saldo_start_line = ''.join([
    "15~1~01.01.20%s~0000000001~!~0000000000~_______R________~1~0000000000~",
    "0.000000000000000e+000~"*3,"!~0~!~!~!~!~!~!~!~!~!~!~","0.000000000000000e+000~"*23, '\n'])

saldo_artikul_line = "15~0~%s~01.01.20%s~%.15e~%.15e~%.15e~\n"

def make_saldo_replic(salda, data_path, yy):
    fn = "replic01.%s"% yy #01 is saldo
    saldo_writer = open(os.path.join(data_path, fn), 'w+')
    saldo_writer.write(saldo_start_line%yy)
    saldo_writer.writelines([s.toexport_string(yy) for s in salda])

class SalDo(object):
    meassure = "бр."
    def __init__(self, magis_id, MP_id, art_name, qty, price_bought, price_bought_total):
        self.magis_id = magis_id
        self.MP_id = MP_id
        self.name = art_name
        self.qty = qty
        self.p1 = self.price_bought = price_bought
        self.p2 = self.price_bought_total = price_bought_total

    def toexport_string(self, yy):
        '15~0~102657~01.01.2013~1.000000000000000e+000~5.570000000000000e+000~1.114000000000000e+000~'
        return saldo_artikul_line % (self.magis_id, yy, self.qty, self.p1, self.p2)


if __name__ == '__main__':
    # execfile("SelectMP.py")
    import unittest

    unittest.main(argv=[__file__,
    #~ 'test_DNEV_parser',
    ])
