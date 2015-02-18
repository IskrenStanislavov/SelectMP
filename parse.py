# encoding: cp1251

from dosutil import ANSI, ANSI2OEM
import os, sys
#~ from vikBoiana import parse as scet_parse

import encodings
if encodings.search_function('mbcs') is None:
    encodings._cache['mbcs'] = encodings.search_function('cp1251')
cyr = """� �	� �	� �	� �	� �	� �	� �	� �	� �	� �	
� �	� �	� �	� �	� �	� �	� �	� �	� �	� �	
� �	� �	� �	� �	� �	� �	� �	� �	� �	� �"""
cyrtr = {}
for kv in cyr.split('	'):
    kv = kv.strip()
    k,v = kv.split()
    cyrtr[v] = k
def upper(s):
    for lower, upper in cyrtr.items():
        s = s.replace(lower, upper)
    return s
#print upper(cyr)

class GroupSelectMP(object):
    messages = []
    def __init__(self, fakt_num, fakt_date, inner_num, viddoc, contragent):
        self.fakt_num = fakt_num#nomerfaktura
        self.inner_num = inner_num #numdoc
        #kontr_name = ANSI(kontr_name)
        #self.kontr_name = ANSI2OEM(kontr_name).replace('H', ANSI2OEM('�'))#replace H(h) with �(�) BG n
        self.fakt_date = fakt_date
        self.viddoc = viddoc
        #self.bulstat = bulstat[:9]
        self.contragent = contragent
        self.rows = []

    def addDost(self, kind, line):
        assert kind==2
        if '0' in self.viddoc:
            return
        row={}
        group_name, code, name, single_price, q, price_total_1, price_total_2, vat, total = line.split('|')[1:-1]
        group_name = group_name.strip()
        code = code.strip()
        name = name.strip()
        if not (group_name or code):
            #prodyljava ot predniya red
            row = self.rows.pop()
            row['name'] = "%s %s"%(row['name'], name)
            self.rows.append(row)
            return
        #~ try:
            #~ int(code)
        #~ except ValueError:
            #~ print code
            #~ raise Exception(code)
            #~ row['code'] = code
        #~ else:
        row['code'] = code
        row['name'] = name.strip()
        q = q.strip()
        row['quantity'] = q
        row['measure'] = ANSI2OEM("��.")
        row['ed_cena'] = float(price_total_2) / float(q)
        if self.viddoc == "7":
            row['kind'] = 3
            raise 0,'define this case'
            row['ed_cena'] = 0.0# opisanie.txt; �������� � ���� ��������
        else:
            row['kind'] = kind
        self.rows.append(row)

    def addProd(self, kind, line):
        assert kind == 1
        assert '|' in line, line
        if '0' in self.viddoc:
            return
        row = {}
        group_name, code, name, trade_percent, single_price, q, no_vat_included, vat, without_trade_percent, total = line.split('|')[1:-1]
        if trade_percent.strip() and trade_percent.strip() != '0':
            print group_name, code, name, trade_percent, single_price, q, no_vat_included, vat, without_trade_percent, total
            print line
            assert 0, without_trade_percent
        group_name = group_name.strip()
        code = code.strip()
        name = name.strip()
        if not (group_name or code):
            #prodyljava ot predniya red
            row = self.rows.pop()
            row['name'] = "%s %s"%(row['name'], name)
            self.rows.append(row)
            return
        row['code'] = code
        if __debug__:
            row['name'] = name.strip()
        else:
            row['name'] = ANSI2OEM(name.strip())
        q = q.strip()
        row['quantity'] = q
        row['measure'] = ANSI2OEM("��.")
        row['ed_cena'] = float(no_vat_included) / float(q)
        if self.viddoc == "8":
            row['kind'] = 3
            raise 0,'define this case'
            row['ed_cena'] = 0.0# opisanie.txt; �������� � ���� ��������
        else:
            row['kind'] = kind
        self.rows.append(row)


all_skip_lines = []
for _line in ("""������� - ������ �� ���������� � ����������
������� �� ���������� �� ������H�� �� ������
�������� H� ������H���� �� ��������
�������� Deliveries
�������� �� ����������� �� ��������
��������
+����� � ��� +����� � ���
������� �� ���������� �� ��������� �� �����
�����       : ����� ������
+---------------+----------+------------------------------+----------+--------+------------+------------+----------+------------+
| ����� �����   | �����.No |          ����������          |���� ����.| ���-�� | ����.��-�� | ��-�� ����.| ��-�� ���| ���� ��-�� |
+---------------+----------+------------------------------+----------+--------+------------+------------+----------+------------+
+--------------------------------------------------------------------+--------+------------+------------+----------+------------+
������� - ������ �� ������� � ����������
+---------------+----------+------------------------------+---+----------+------------+------------+------------+------------+------------+
| ����� �����   | �����.No |      ����������              |��%| ����.����| ���������� |��-�� ������| ��-�� ���  | ���� ��-�� | ����. ��-��|
+---------------+----------+------------------------------+---+----------+------------+------------+------------+------------+------------+
""".split('\n')
    ):
    all_skip_lines.append(_line)
    all_skip_lines.append(ANSI2OEM(_line))

#msg_fakt = "FAKTURA No(%s) ostava nevavedena(nyama vaveden bulstat za CONTRAGENT{%s})"
msg_fakt = "������� � (%s) ������ ����������(���� ������� ������� �� ����������{%s})"

def get_groups(kind, lines, yy):
    """vzima grupite ot fajla za import kym sklada
        kind==2 is Dostavka s Faktura
        kind==1 is Prodajba
    """
    contr_key_generator = ContrKeyGOD()

    group = None
    num = ""
    nm = ""
    documents = {}
    last_row = None
    for line in lines:
        line = line.strip()
        ansi_line = ANSI(line)
        assert kind != 0
        #~ if __debug__ and kind==0:
            #~ print ansi_line
        if not line:
            continue
        if ansi_line in all_skip_lines or ansi_line.count("-+-") >= 2:
            #~ print '*!%s'%line
            continue
        if ansi_line[:6] in (
            '������', '| ��� ',
            '�� ���',#SelectMP
            '���� N',#SelectMP
            ):
            #~ print '*!%s'%line
            continue
        if kind == 1 and "���� ��:" in ansi_line:
            if group and group != 'null':
                yield group
            group = None
            continue
        elif kind == 2 and group and group !='null':
            if kind==2 and num and num in line and ("���� ��" in ansi_line):#end of null group
                yield group
                group = None
                num = ""
                continue

        #SelectMP: ��������
        if ansi_line.startswith('���������   :'):
            assert kind == 2,kind
            nm = contrag_name = upper(ansi_line[13:].strip())
            #bulstat = contr_key_generator.get_bulstat(contrag_name)#old
            contragent = contr_key_generator.get_contragent_by_name(contrag_name)
            continue
        if kind == 2 and ansi_line.startswith('������� No :'):## ��������
            fn_and_fdate = ansi_line[12:].partition('/')
            num = fakt_num = fn_and_fdate[0].strip()
            fakt_date = fn_and_fdate[-1].strip()
            d,m,y = fakt_date.split('.')
            inner_prefix = "%s%s0"%(y[1:],m)
            monthly_number = documents[inner_prefix] = documents.setdefault(inner_prefix, 0) + 1
            inner_num = inner_prefix + str(monthly_number).rjust(4,'0')# +str(line_number)
            #~ contrag_name = contrag_name
            viddoc = doc_by_name['dost_faktura']
            contragent = contr_key_generator.get_contragent_by_name(contrag_name)
            assert contragent is None or isinstance(contragent,Contragent), type(contragent)
            group = GroupSelectMP(fakt_num, fakt_date, inner_num, viddoc, contragent)
            if contragent is None:
                group.messages.append(msg_fakt%(fakt_num, contrag_name))
            continue
        if kind == 2 and ansi_line.startswith('|���� ��: ����� ������'):
            continue
        if kind == 2 and nm:
            if ansi_line.startswith("|���� ��: %s"%nm):
                continue
        #SelectMP: ��������
        if ansi_line.startswith('������      :'):
            assert kind == 1,kind
            nm = contrag_name = upper(ansi_line[13:].strip())
            contragent = contr_key_generator.get_contragent_by_name(contrag_name)
            continue
        if kind == 1 and ansi_line.startswith('�������  No :'):## ��������
            fn_and_fdate = ansi_line[13:].partition('/')
            num = fakt_num = fn_and_fdate[0].strip()
            fakt_date = fn_and_fdate[-1].strip("���� :").strip()
            d,m,y = fakt_date.split('.')
            inner_prefix = "%s%s"%(y,m)
            inner_num = fakt_num#inner_prefix + str(monthly_number).rjust(4,'0')# +str(line_number)
            #~ contrag_name = contrag_name
            viddoc = doc_by_name['prod_faktura']
            contragent = contr_key_generator.get_contragent_by_name(contrag_name)
            group = GroupSelectMP(fakt_num, fakt_date, inner_num, viddoc, contragent)
            if contragent is None:
                group.messages.append(msg_fakt%(fakt_num, contrag_name))
            continue
        if kind in (1,2) and nm:
            if ansi_line.startswith("|���� ��: %s"%nm):
                continue
        assert group, "kind=%s, row='"%kind+ANSI(line)
        if kind == 1:
            group.addProd(kind, line)
        else:
            group.addDost(kind, line)

doc_by_name = dict()
doc_by_name['dost_faktura'] = '2'
doc_by_name['dost_drug_doc'] = '7'
doc_by_name['prod_faktura'] = '9'
doc_by_name['prod_kreditno'] = '9-'
doc_by_name['prod_kasa_note'] = '8'

def add_dividers(line, pos, div='|'):
    for i in pos:
        line = line[:i-1]+'|'+line[i:]
    return line

def parse(base_path, parsed_fn, yy):
    if parsed_fn.startswith('prod'):
        import_type = 1
    elif parsed_fn.startswith('dost'):
        import_type = 2
    else:
        print 'should start with prod / dost'
        return
    parsed_fn = os.path.join(base_path, parsed_fn)
    f = open(parsed_fn)
    groups = list(get_groups(import_type, f, yy))
    f.close()
    return groups

def parse_dolphine_dealers(lines):
    res = {}
    previous_line_name = None
    for line in lines.splitlines():
        line = line.strip()
        if not line:continue
        if line.startswith("| ���      |"):
            continue
        line = line.split('|')
        line_number = line[0]
        line = line[1:]
        if not line:continue
        name = upper(line[1].strip())
        bulstat = line[2].strip()
        if not name and not bulstat:
            continue
        if not line_number and name and not bulstat:
            #prodyljava na sledvashtiya red predniq dealer
            contragent = res[upper(previous_line_name)]
            previous_line_name = ' '.join([upper(previous_line_name), upper(name)])
            name = upper(previous_line_name)
            #~ res[name] = bulstat
        else:
            previous_line_name = upper(name)
        #res[name] = bulstat
        assert id, line
        if bulstat.startswith('999'):
            bulstat = bulstat.ljust(15,'9')
            #~ assert 0, bulstat
        res[upper(name)] = Contragent(id, upper(name), bulstat)
    return res

class ArtKeyGOD(object):
    file_name = ""
    work_path = ""
    def __init__(self):
        assert self.file_name
        assert self.work_path
        art_id = open(os.path.join(self.work_path, self.file_name), 'r').readlines()
        art_id = [ANSI(r.strip()).split('=', 2) for r in art_id]
        art_id = dict(art_id)
        self.art_ids = art_id

    def _write_key(self, key):
        k,v = key, self.art_ids[key]
        art_id = [ '%s=%s\n'%(k,v) ]
        f = open(os.path.join(self.work_path, self.file_name), 'a+')#will work faster with append
        f.writelines(art_id)
        f.close()
        
    def get_key(self, lookup_value):
        if lookup_value not in self.art_ids:
            last = getattr(self, 'last', None)
            if last is None:
                if not self.art_ids:
                    self.last = 71110
                else:
                    self.last = max(self.art_ids.values())
            self.last = "%d"% (int(self.last)+1)
            self.art_ids[lookup_value] = self.last
            self._write_key(lookup_value)
        return self.art_ids[lookup_value]

    def update(self, d):
        for k,v in d.iteritems():
            self.art_ids[k] = v
            self._write_key(k)

class Contragent(object):
    def __init__(self, id, name, vatnum):
        self.id = id
        assert name == ANSI(name)
        self.name = upper(name)
        assert isinstance(vatnum, int) or isinstance(vatnum, basestring), type(vatnum)
        self.vatnum = vatnum

    def __str__(self):
        return "id(%d),name:{%s}, VAT:[%s]"%(self.id, self.name, self.vatnum)

class ContrKeyGOD(object):
    file_name = ""
    work_path = ""
    def __init__(self):
        #assert 0, self.file_name
        assert self.file_name
        assert self.work_path
        self.all_contragents = {}
        self.wanted_contragents = []

        art_id = open(os.path.join(self.work_path, self.file_name), 'r+').readlines()
        for line in art_id:
            if not line.startswith('1000~'):
                continue
            line = ANSI(line)
            data = line.split("~")
            id = int(data[1])#.lstrip('0')
            name = upper(ANSI(data[5]))
            d = filter(None, data[6].split('\x7f'))
            if d:
                vatnum = d[0]
            else:
                self.wanted_contragents.append(name)
                continue#dont use these INVOICES
            vatnum = vatnum.lstrip('BG')
            self.all_contragents[upper(name)] = Contragent(id, upper(name), vatnum)

    def update(self, d):
        for k,v in d.iteritems():
            if k in self.all_contragents:
                f = self.all_contragents[k]
                assert v.name == f.name
                if v.vatnum != f.vatnum:
                    GroupSelectMP.messages.append("������� ��� ���/������� �� ���������� {%s}:(1):%s; (2):%s; �������:%s"%(f.name, v.vatnum, f.vatnum, f.vatnum))
                    continue
                continue
            if v.name in self.wanted_contragents:
                self.wanted_contragents.remove(v.name)
            assert isinstance(v, Contragent), type(v)
            self.all_contragents[upper(v.name)] = v

    def iter_all_contragents(self):
        return self.all_contragents.iteritems()

    def get_contragent_by_name(self, lookup):
        lookup = upper(lookup)
        if lookup not in self.all_contragents:
            return None
        res = self.all_contragents[lookup]
        assert isinstance(res,Contragent), type(contragent)
        return res

def start_saldo(fn='saldo_MP.txt'):
    """
     |15027     |������� 63 �                       |       18.00|      0.10|      1.35|      0.92|        1.80|       24.30|       16.56|
     |15029     |����� 2,5 ��                       |        1.00|      0.55|      0.85|      0.58|        0.55|        0.85|        0.58|
     |          |����������                         |            |          |          |          |            |            |            |
     |          |��������                           |            |          |          |          |            |            |            |
     |15030     |����� 2,5 ��                       |        3.00|      0.75|      1.15|      0.78|        2.25|        3.45|        2.34|
     |          |����������                         |            |          |          |          |            |            |            |
     |          |��������                           |            |          |          |          |            |            |            |
     |15095     |���� ����. �. �                    |        1.00|      1.30|      1.96|      1.31|        1.30|        1.96|        1.31|
     |          |/ ���������� /                     |            |          |          |          |            |            |            |
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
    meassure = "��."
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
    execfile("SelectMP.py")
    import unittest
    class test_DNEV_parser(unittest.TestCase):
        "���/���"
        def test_dolphine_parser(self):
            v="""   �����������                   
                 +----------+--------------------------------+---------------+--------------------------------+-----------------+-----------------+----------------------+
                 | ���      | ���                            | ���/���       | �����                          | �������         | ����            | e-mail               |
                 +----------+--------------------------------+---------------+--------------------------------+-----------------+-----------------+----------------------+
                 | 1        | ������ ���                     | 103052149     | ��. �����, ��."�������", 40�   |                 |                 |                      | 
                 | 2        | ���� - ���������� �������� ��  | 813098792     | ��. �����, ��. "���������", 35 |                 |                 |                      | 
                 | 3        | ���� ��                        | 826002475     | ��. �������, ��. "��������", 9 |                 |                 |                      | 
                 | 4        | ���� ��� ����                  | 117048851     | ��. ����, ��. "��������", 21   |                 |                 |                      | 
                 | 5        | ���� - ������ ������ ��        | 103094618     | ��. �����, ��. "���.������ ��� |                 |                 |                      | 
                 +----------+--------------------------------+---------------+--------------------------------+-----------------+-----------------+----------------------+
                
                ���� No 2
                 +----------+--------------------------------+---------------+--------------------------------+-----------------+-----------------+----------------------+
                 | ���      | ���                            | ���/���       | �����                          | �������         | ����            | e-mail               |
                 +----------+--------------------------------+---------------+--------------------------------+-----------------+-----------------+----------------------+
                 | 76       | ������� ����                   | 103766998     | ��. �����, ��. "������", 28, � |                 |                 |                      | 
                 | 85       | ������ �-� ������� - �-�       | 148153124     | ��. �����, ��. "������", 21    |                 |                 |                      | 
                 |          | ��������                       |               |                                |                 |                 |                      | 
                 | 86       | ����� ����                     | 103925728     | ��. �����, ��. "���. ��������" |                 |                 |                      | 
                 | 103      | ���� "�������� ���� �������    | 175748184     | ��. �����, �.�. "������", � 89 |                 |                 |                      | 
                 |          | 1918"                          |               |                                |                 |                 |                      | 
                 | 104      | ��� ����� ����                 | 200758980     | ��. �����, ��. "�. �����", 17  |                 |                 |                      | 
                 +----------+--------------------------------+---------------+--------------------------------+-----------------+-----------------+----------------------+
                """
            r = parse_dolphine_dealers(v)
            assert "������ ���" in r,r.keys()
            assert r["������ ���"] == "103052149"
            assert r["������� ����"] == "103766998"
            assert r["������ �-� ������� - �-�"] == "148153124"
            assert r["������ �-� ������� - �-� ��������"] == "148153124"
            assert r["���� \"�������� ���� �������"] == "175748184"
            assert r["���� \"�������� ���� ������� 1918\""] == "175748184"

        def test_1(self):
            v="""
      1 02/05/2012 ���?��� ?�???��     1080859 (0000036445) ???  ??????  -  ????           200358743  ?�����?? �� ��??��                     13.87         11.56          2.31                            
      2 03/05/2012 ���?��� ?�???��     1080860 (0000036446) ??H? - ?.?H?????? ??           813041859  ?�����?? �� ��??��                     38.93         32.44          6.49                            
      3 04/05/2012 ���?��� ?�???��     1080861 (0000036447) ?.??????? - ??  ????           103608394  ?�����?? �� ��??��                     25.44         21.20          4.24                            
     60 15/05/2012 ���?��� ?�???��     1081575 (0000036748) ?????? ??                      103588015  ?�����?? �� ��??��                     37.97         31.64          6.33
     """
            r = parse_lines_for_faktura(v)
            assert "0000036445" in r,r.keys()
            assert r["0000036445"]["fakt_date"] == "02/05/2012"
            assert r["0000036445"]["fakt_num"] == "0000036445"
            assert r["0000036445"]["bulstat"] == "200358743"

            assert "0000036446" in r
            assert r["0000036446"]["fakt_date"] == "03/05/2012"
            assert r["0000036446"]["fakt_num"] == "0000036446"
            assert r["0000036446"]["bulstat"] == "813041859"

            assert "0000036447" in r
            assert r["0000036447"]["fakt_date"] == "04/05/2012"
            assert r["0000036447"]["fakt_num"] == "0000036447"
            assert r["0000036447"]["bulstat"] == "103608394"

        def test_2013(self):
            v="""
                            � � � � � � �  � �  � � � � � � � � � �
                           �� �� ���� BG202240124
                           ������� ������ 01/01/2013 - 31/01/2013
   
   -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
   |����- |����|���| ����� �� ��������� | ���� ��  |  �� ��        | ��� �� �����������      | ��� �� �������/�������� | ��� ������ �� |    ������     |     �� ��     |�������� ��� ��|
   |���   |    |   |                    |��������� |  ����������   |                         |                         |�� �� �������� | �������� ���  | ���.��������, |  �������� ��  |
   |����� |    |   |                    |          |               |                         |                         |    � ���      |               |  ������ 20%,  |     �.11      |
   |      |    |   |                    |          |               |                         |                         |               |               |���.����.����. |               |
   |      |    |   |                    |          |               |                         |                         |               |               | � ����� ��    |               |
   |      |    |   |                    |          |               |                         |                         |               |               |���������� ��  |               |
   |      |    |   |                    |          |               |                         |                         |               |               |����������� �� |               |
   |      |    |   |                    |          |               |                         |                         |               |               |   ��������    |               |
   | -1-  | -2-|-3-|        -4-         |    -5-   |       -6-     |          -7-            |            -8-          |      -9-      |     -10-      |      -11-     |      -12-     |
   -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
   |     1|     |01|0000000001          |03/01/2013|BG811160793    |��������� ����� �������  |�������� �� ������       |         524.30|         104.86|         524.30|         104.86|
   |     2|     |01|0000000002          |07/01/2013|BG103134692    |�������  -  ���          |�������� �� ������       |          49.61|           9.92|          49.61|           9.92|
   |     3|     |01|0000000003          |07/01/2013|BG200093565    |������� ���� ����        |�������� �� ������       |         223.79|          44.76|         223.79|          44.76|
   |     4|     |01|0000000004          |08/01/2013|BG811160793    |��������� ����� �������  |�������� �� ������       |        3994.53|         798.91|        3994.53|         798.91|
   |     5|     |01|0000000005          |08/01/2013|BG811160793    |��������� ����� �������  |�������� �� ������       |         102.74|          20.55|         102.74|          20.55|
   |     6|     |01|0000000006          |09/01/2013|BG148114598    |���� ����  ���           |�������� �� ������       |         529.91|         105.98|         529.91|         105.98|
   |     7|     |01|0000000007          |09/01/2013|BG813095508    |�������  ���  ��         |�������� �� ������       |        3211.53|         642.31|        3211.53|         642.31|
   |     8|     |01|0000000008          |09/01/2013|BG201661661    |����� ����  -  ���       |�������� �� ������       |         200.86|          40.17|         200.86|          40.17|
   |     9|     |01|0000000009          |11/01/2013|BG148114598    |���� ����  ���           |�������� �� ������       |         165.50|          33.10|         165.50|          33.10|
   |    10|     |01|0000000010          |11/01/2013|BG148114598    |���� ����  ���           |�������� �� ������       |          85.76|          17.15|          85.76|          17.15|
     """
            r = parse_lines_for_faktura2013(v)
            assert "0000000009" in r,r.keys()
            assert r["0000000009"]["fakt_date"] == "11/01/2013"
            assert r["0000000009"]["fakt_num"] == "0000000009"
            assert r["0000000009"]["bulstat"] == "148114598"

            assert "0000000003" in r
            assert r["0000000003"]["fakt_date"] == "07/01/2013"
            assert r["0000000003"]["fakt_num"] == "0000000003"
            assert r["0000000003"]["bulstat"] == "200093565"

            assert "0000000007" in r
            assert r["0000000007"]["fakt_date"] == "09/01/2013"
            assert r["0000000007"]["fakt_num"] == "0000000007"
            assert r["0000000007"]["bulstat"] == "813095508"

    class test_row_parser(unittest.TestCase):
        def setUp(self):
            txt = open(Group._dnev_file).read()
            Group.dnev_info = parse_lines_for_faktura(txt)
            assert Group.dnev_info

        def test_proforma_invoice(self):
            #| �������� �������  No 1000020225  ���.No 1077845 ������� ���������-�H��H���H� ��� ���                                         |

            line = """|220402         �� ������."����"1/2  �/�  ���� ��         4.000|           1.88|           7.51|           2.72|          10.88|"""
            g = Group("0000036445","27.07.1925", "1080859", "���  ������  -  ����", "90", "1234123445")#BULSTAT=None
            assert Group.dnev_info
            assert g.dnev_info
            g.addProd(1,line)
            self.assertEqual(len(g.rows), 0)

        def test_prod(self):
            #| ������� �������   No 0000036445  ���.No 1080859 ������� ���  ������  -  ����                                                 |

            line = """|220402         �� ������."����"1/2  �/�  ���� ��         4.000|           1.88|           7.51|           2.72|          10.88|"""
            g = Group("0000036445","27.07.1925", "1080859", "���  ������  -  ����", "9", "1234123445")#BULSTAT=None
            assert Group.dnev_info
            assert g.dnev_info
            g.addProd(1,line)
            self.assertEqual(g.rows[0]['code'], "220402")
            self.assertEqual(g.rows[0]['name'], """�� ������."����"1/2  �/�  ����""")
            self.assertEqual(g.rows[0]['quantity'], "4.000")
            self.assertEqual(g.rows[0]['measure'], "��")
            self.assertEqual(g.rows[0]['ed_cena'], 2.72)
            self.assertEqual(g.rows[0]['kind'], 1)

        def test_prod_kreditno_izvestie(self):
            #"������� �� ����������"
            #| ���.�������� ���. No 0000035116  ���.No 1077811 ������� �H������� ����� ��H���� ���                                          |

            line = """|220402         �� ������."����"1/2  �/�  ���� ��         4.000|           1.88|           7.51|           2.72|          10.88|"""
            g = Group("0000035116","27.07.1925", "1077811", "�H������� ����� ��H���� ���", "91", "1234123445")#BULSTAT=None
            assert Group.dnev_info
            assert g.dnev_info
            g.addProd(1,line)
            self.assertEqual(g.rows[0]['code'], "220402")
            self.assertEqual(g.rows[0]['name'], """�� ������."����"1/2  �/�  ����""")
            self.assertEqual(g.rows[0]['quantity'], "4.000")
            self.assertEqual(g.rows[0]['measure'], "��")
            self.assertEqual(g.rows[0]['ed_cena'], 2.72)
            self.assertEqual(g.rows[0]['kind'], 1)

        def test_dost(self):
            #1023724-03/05/2012 (0000322651) (������� ) ������: �����  ����                    103796468 �������: 01  ���.���.
            line = """2033030         �5131�� ������� �14 �� ��� ���        1.000 ��.        0.00          2.34         2.34         0.47      2.88         2.88"""
            g = Group("0000322651","27.07.1925", "1023724", "�����  ����", "2", "103796468")
            assert Group.dnev_info
            assert g.dnev_info
            g.addDost(2,line)
            self.assertEqual(g.rows[0]['code'], "2033030")
            self.assertEqual(g.rows[0]['name'], "�5131�� ������� �14 �� ��� ���")
            self.assertEqual(g.rows[0]['quantity'], "1.000")
            self.assertEqual(g.rows[0]['measure'], "��.")
            self.assertEqual(g.rows[0]['ed_cena'], 2.34)
            self.assertEqual(g.rows[0]['kind'], 2)

    class test_parser(unittest.TestCase):
        def setUp(self):
            txt = open(Group._dnev_file).read()
            Group.dnev_info = parse_lines_for_faktura(txt)
            assert Group.dnev_info
        def test_prod(self):#count
            assert Group.dnev_info
            parsed_fn = 'prod.PRN'
            papka = 'test_files'
            err_file = "Eerrs.txt"
            #~ part_exp_command = "gw -p%s Dpe F%s >%s" %(papka, partidi_for_export_fn, err_file)
            #~ part_imp_command = "gw -p%s Dpi F%s >%s" %(papka, partidi_for_import_fn, err_file)
            all_groups = parse(papka, parsed_fn, '31/12/2012')
            v = ANSI2OEM("����:")
            text = open(os.path.join(papka, parsed_fn)).read()
            bv = (ANSI2OEM("| �������� �������"))#�� ������ � ��������������
            total_qty = text.count(v) - text.count(bv)
            self.assertEqual(total_qty,[576-1,1029][0])
            self.assertEqual(len(all_groups),[576-1,1029][0])
        def test_dost(self):#count
            assert Group.dnev_info
            parsed_fn = 'dost.PRN'
            papka = 'test_files'
            err_file = "Eerrs.txt"
            #~ part_exp_command = "gw -p%s Dpe F%s >%s" %(papka, partidi_for_export_fn, err_file)
            #~ part_imp_command = "gw -p%s Dpi F%s >%s" %(papka, partidi_for_import_fn, err_file)
            all_groups = parse(papka, parsed_fn, '31/12/2012')
            text = open(os.path.join(papka, parsed_fn)).read()
            v = ANSI2OEM("���� �� 1")
            b = ANSI2OEM("(�������� ) ������:")
            t = ANSI2OEM("(������� ) ������:     ��  �H��")
            m = ANSI2OEM("(������� ) ������: ��  �H��")
            total_qty = text.count(v) - text.count(b) - text.count(t) - text.count(m)
            self.assertEqual(total_qty,266)
            self.assertEqual(len(all_groups),266)
        def test_case1(self):
            assert Group.dnev_info
            lines = """ 1023985-16/05/2012 (0000000191) (������� ) ������: ������ �����   ����            201957710 �������: 01  ���.���.
                ���             �����                           ���������� �����      ��       ��. ���� 1   �������� 1       ���    �.�� ��.      ��������
                                                                                                                                                          
                350105          ����� �� PVC ����� �110             200.000 ��.        0.00          0.89       177.54        35.51      2.26       452.00
                370721          ��� ���.�����.����� 10 8�100         30.000 ��.        0.00          1.07        32.10         6.42      1.60        48.00
                370741          ���  �-�� ����  12 8�95              50.000 ��.        0.00          0.56        28.02         5.60      0.75        37.50
                370755          ��H ���.����.�� ������ 22          3000.000 ��.        0.00          0.04       122.70        24.54      0.06       180.00
                ���� �� 1023985                                                                                 360.36        72.07                 717.50
            """.split('\n')
            groups = get_groups(1, lines, '31/12/2012')
        def test_case2(self):
            #see 200102 �1347��
            assert Group.dnev_info
            lines = """ 1024030-21/05/2012 (0000078799) (������� ) ���� �: ��H��� ���                     030001738 �������: 01  � �.� �.
                ���             �����                           ���������� �����      ��       ��. ���� 1   �������� 1       ���    �.�� ��.      ��������
                200102 �1347��  �.�.������ - R ���.  ��               3.000 ��.        0.00         36.35       109.05     45.60       136.80
                201202          �9093�� ���-� ���  ��.����.���        3.000 ��.        0.00         38.03       114.09     50.00       150.00
                  ���� �� 1024030                                                                                 360.36        72.07                 717.50
            """
            #~ print ANSI(lines)
            for g in get_groups(2, lines.split('\n'), '31/12/2012'):
                self.assertEqual(g.rows[0]['code'], "200102")
                self.assertEqual(g.rows[0]['name'], ANSI2OEM("�1347��  �.�.������ - R ���.  ��"))
                self.assertEqual(g.rows[1]['code'], "201202")
                self.assertEqual(g.rows[1]['name'], ANSI2OEM("�9093�� ���-� ���  ��.����.���"))
        def test_case3(self):
            #see 280130 874095
            assert Group.dnev_info
            lines = """
     --------------------------------------------------------------------------------------------------------------------------------
     | ������� �������   No 0000035031  ���.No 1077621 ������� �����H�   ����                                                       |
     --------------------------------------------------------------------------------------------------------------------------------
     | ��� � ������������ �� �����                |�����| ����������|���� �� ������.|      ����     |����.����(��� ���)   ����      |
     --------------------------------------------------------------------------------------------------------------------------------
     |280130 874095  �������� ADONIS �� ��� - ����. ��.        1.000|          68.27|          68.27|          46.94|          46.94|
     |224991         ����  ����� �� ����� �������   ��         1.000|          10.50|          10.50|          15.75|          15.75|
     |222041         �������� 3/4�-1/2� �����       ��         1.000|           0.31|           0.31|           1.33|           1.33|
     |230614         ������� ������ 1/2�10 30��     ��.        2.000|           1.49|           2.98|           1.84|           3.68|
     |222801         ������ �����.-10�.�10��.� 0.76 ��         1.000|           0.22|           0.22|           0.29|           0.29|
     --------------------------------------------------------------------------------------------------------------------------------
     | ����:                                                                                   82.28                           67.99|
     | H������� ���:            13.60                                      �������:           -14.29                                |
     --------------------------------------------------------------------------------------------------------------------------------
            """
            #~ print ANSI(lines)
            for g in get_groups(1, lines.split('\n'), '31/12/2012'):
                self.assertEqual(g.rows[0]['code'], "280130")
                self.assertEqual(g.rows[0]['name'], "�������� ADONIS �� ��� - ����.")
                self.assertEqual(g.rows[1]['code'], "224991")
                self.assertEqual(g.rows[1]['name'], "����  ����� �� ����� �������")

        def test_case2013_1(self):
            #see 280130 874095
            assert Group.dnev_info
            lines = """
     ------------------------------------------------------------------------------------------------------------------------
     ������� �� ���������� �� ��������� �� �����
     ------------------------------------------------------------------------------------------------------------------------
     ������: 01/01/2013 - 31/01/2013
     --------------------------------------------------------------------------------------------------------------------------------
     | ������� �������   No 0000000001  ���.No 1000003 ������� ��������� ����� �������  ���                                         |
     --------------------------------------------------------------------------------------------------------------------------------
     | ��� � ������������ �� �����                |�����| ����������|���� �� ������.|      ����     |����.����(��� ���)   ����      |
     --------------------------------------------------------------------------------------------------------------------------------
     |140110         ��� ����� �20�3.4  �.�.- FV    �.       300.000|           0.81|         243.60|           0.91|         273.00|
     |060102         �VC ����� �  25�1.8 - BG       �.       100.000|           0.42|          42.16|           0.58|          57.80|
     |150507         ��.����.�-����� � 22�6         �.       300.000|           0.47|         141.90|           0.65|         193.50|
     --------------------------------------------------------------------------------------------------------------------------------
     | ����:                                                                                  427.66                          524.30|
     | �������� ���:           104.86                                      �������:            96.64                                |
     --------------------------------------------------------------------------------------------------------------------------------
     --------------------------------------------------------------------------------------------------------------------------------
     | ������� �������   No 0000000002  ���.No 1000004 ������� �������  -  ���                                                      |
     --------------------------------------------------------------------------------------------------------------------------------
     | ��� � ������������ �� �����                |�����| ����������|���� �� ������.|      ����     |����.����(��� ���)   ����      |
     --------------------------------------------------------------------------------------------------------------------------------
     |330315         ����� ������ - 5443            ��.        1.000|          39.17|          39.17|          49.61|          49.61|
     --------------------------------------------------------------------------------------------------------------------------------
     | ����:                                                                                   39.17                           49.61|
     | �������� ���:             9.92                                      �������:            10.44                                |
     --------------------------------------------------------------------------------------------------------------------------------
            """
            #~ print ANSI(lines)
            for i, g in enumerate(get_groups(1, lines.split('\n'), '31/12/2012')):
                self.assertEqual(g.rows[0]['code'], ("140110",'330315')[i])
                self.assertEqual(g.rows[0]['name'], ("��� ����� �20�3.4  �.�.- FV", "����� ������ - 5443")[i])
                if i >= 1:
                    continue
                self.assertEqual(g.rows[1]['code'], "060102")
                self.assertEqual(g.rows[1]['name'], "�VC ����� �  25�1.8 - BG")

        def test_case2013_2_dost(self):
            #see 280130 874095
            assert Group.dnev_info
            lines = """

       -----------------------------------
       �������� �� ����������� �� ��������
       -----------------------------------
       ������: 01/01/2013 - 31/01/2013
       -----------------------------------------------------------------------------------------------------------------------------------
       ��������                                 
       1000002-03/01/2013 (7000005550) (������� ) ������: ������ ���������-����   ��     040187401 �������: 01  ������� 
          ���             �����                           ���������� �����      ��       ��. ���� 1   �������� 1   ��. ���� 3   �������� 3 �.�� ��.      ��������
                                                                                                                 +����� � ��� +����� � ���                       
           100506          �� ������ 63                          3.000 ��.       0.00          5.37        16.11         6.44        19.33      6.98        20.94
           011106          ����������� 2                         2.000 ��.       0.00          5.60        11.20         6.72        13.44      7.18        14.36
           140110          ��� ����� �20�3.4  �.�.- FV         375.000 �.        0.00          0.81       304.50         0.97       365.40      1.40       525.00
          ���� �� 1000002                                                                                 331.81                    398.17                 560.30
       1000003-03/01/2013 (0000040225) (������� ) ������: ��� �����  ���                 148063709 �������: 01  ������� 
          ���             �����                           ���������� �����      ��       ��. ���� 1   �������� 1   ��. ���� 3   �������� 3 �.�� ��.      ��������
                                                                                                                 +����� � ��� +����� � ���                       
           060102          �VC ����� �  25�1.8 - BG            100.000 �.       38.00%         0.42        42.16         0.51        50.59      0.68        68.00
           150507          ��.����.�-����� � 22�6              300.000 �.       45.00%         0.47       141.90         0.57       170.28      0.86       258.00
          ���� �� 1000003                                                                                 184.06                    220.87                 326.00
            """
            #~ print ANSI(lines)
            for i,g in enumerate(get_groups(2, lines.split('\n'), '31/12/2012')):
                self.assertEqual(g.rows[0]['kind'], (2,"060102")[i])
                self.assertEqual(g.rows[0]['code'], ("100506","060102")[i])
                self.assertEqual(g.rows[0]['name'], ("�� ������ 63","�VC ����� �  25�1.8 - BG")[i])
                self.assertEqual(g.rows[0]['ed_cena'], ("�� ������ 63","�VC ����� �  25�1.8 - BG")[i])
                self.assertEqual(g.rows[0]['measure'], ("�� ������ 63","�VC ����� �  25�1.8 - BG")[i])
                self.assertEqual(g.rows[0]['quantity'], ("�� ������ 63","�VC ����� �  25�1.8 - BG")[i])
                self.assertEqual(g.rows[1]['code'], ("011106","150507")[i])
                self.assertEqual(g.rows[1]['name'], ("����������� 2","��.����.�-����� � 22�6")[i])
                if i >= 1:
                    continue
                self.assertEqual(g.rows[2]['code'], "140110")
                self.assertEqual(g.rows[2]['name'], "��� ����� �20�3.4  �.�.- FV")

    unittest.main(argv=[__file__,
    #~ 'test_DNEV_parser',
    #~ 'test_DNEV_parser.test_dolphine_parser',
    #~ 'test_parser.test_dost',
    #~ 'test_parser.test_PROD',
    #~ 'test_parser.test_1',
    #~ 'test_parser.test_rRow',
    
    #~ 'test_parser.test_contr_parse',
    ])
