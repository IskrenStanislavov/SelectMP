# encoding: utf8
from dosutil import ANSI, ANSI2OEM

import time, os
from datetime import datetime


from config import IniParser
from utils import Proxy, formatLabel
import parse

from saldo import SaldoCollection

try:
    from products import ProductCollection
except ImportError as ie:
    ProductCollection = None

class SelectMP(object):
    def __init__(self, ini_path="SelectMP.ini"):
        self.config = IniParser(ini_path)
        if (ProductCollection is not None):
            self.products = ProductCollection();


    def art(self, fn, fp, ofnnew, ofcnew, salda):#otdelq artikuli i kontragenti!!!!!
        mode = "w+"
        outnew = open(ofnnew, mode) # artikuli 
        outcnew = open(ofcnew, mode)
        contr = {}
        art = {}
        for s in salda:
            if s.name in art:
                continue
            art[s.magis_id] = (s.meassure, s.name,)
        art_key_generator = parse.ArtKeyGOD()
        contr_key_generator = parse.ContrKeyGOD()
        for g in fn+fp:
            for r in g.rows:
                key = art_key_generator.get_key(r['code'])
                if r['name'] in art:continue
                art[key] = (r['measure'], r['name'], )
            contragent = g.contragent
            if contragent is None or contragent.name in contr:
                continue
            contr[contragent.vatnum] = contragent.name
        for name, contragent in contr_key_generator.iter_all_contragents():
            contr[contragent.vatnum] = name
        for code, (meassure, nm) in art.iteritems():
            artikul = ANSI2OEM("%s~20%%~0%%~4294901761~%s~%s~~~0.000000000000000e+000~01.01.2012/00:00:01~0.000000000000000e+000""~\n"%(
                code,meassure, nm))
            outnew.write(artikul)
        for code, nm in contr.iteritems():
            contragent = ANSI2OEM("%s~%s~ ~ ~%s~~~~~~~~~~~~!~""~\n" %(code,code,nm))
            outcnew.write(contragent)
        outnew.close()
        outcnew.close()

    def make_replic(self, info, save_path, yyYearId):
        errors = []
        art_key_generator = parse.ArtKeyGOD()
        rep02 = os.path.join(save_path, "replic02." + yyYearId)#Доставка с фактура
        rep07 = os.path.join(save_path, "replic07." + yyYearId)#Доставка с касова бележка/друг документ
        rep08 = os.path.join(save_path, "replic08." + yyYearId)#Касови продажби
        rep09 = os.path.join(save_path, "replic09." + yyYearId)#Продажба с фактура
        mode='w+'
        f2 = open(rep02, mode)
        f7 = open(rep07, mode)
        f8 = open(rep08, mode)
        f9 = open(rep09, mode)
        #out = open(ofn, 'wt')
        t1 = ''
        for group in info:
            if group.viddoc == "9-":#kreditno izvestie kym prodagba
                v_str = "%s~0~%s~%s~%s~%s~\n"
                group.viddoc = "9"
                err_kind = "Кредитно известие към продажба"
            elif group.viddoc in ("8", "9"):#prodagba
                v_str = "%s~0~%s~%s~-%s~%s~\n"#qty goes down
                err_kind = "Фактура за Продажба"
            elif group.viddoc in ("2", "7",):#dostavka
                v_str = "%s~0~%s~%s~%s~%s~\n"
                err_kind = "Фактура за Доставка"
                
            numdoc = group.inner_num
            nomerfaktura = group.fakt_num
            date_faktura = group.fakt_date.replace('/', '.')
            contragent = group.contragent
            if contragent is None:
                errors.append(config.missingEIKmessage %(err_kind, nomerfaktura,date_faktura))
                continue
            contragent_id = contragent.vatnum
            for v in group.rows:
                kolichestwo = v['quantity']
                ed_cena = v['ed_cena']
                assert kolichestwo != 0 #може и кредитни и търг. отстъпки
                ed_cena = '%1.15e' % (ed_cena)
                kolichestwo ='%1.15e' % float(kolichestwo)
                t1 += v_str % (numdoc, art_key_generator.get_key(v['code']), date_faktura, kolichestwo, ed_cena)
            ###write end of document here
            if group.viddoc == "2":# доставка с фактура
                t_vars = (numdoc, group.viddoc, date_faktura, numdoc, date_faktura, nomerfaktura, contragent_id, date_faktura)
            else:
                t_vars = (numdoc, group.viddoc, date_faktura, nomerfaktura, date_faktura, nomerfaktura, contragent_id, date_faktura)
                
            t = "%s~%s~%s~%s~%s~%s~_______R________~1~%s~%s~"%t_vars
            assert group.viddoc in "2789"
            if group.viddoc == "2":#dostavka с фактура
                out = f2
            elif group.viddoc == "7":#dostavka с документ
                out = f7
            elif group.viddoc == "9":#prodagba с фактура
                out = f9
            elif group.viddoc == "8":#prodagba/касова продажба
                out = f8
            else:
                raise Exception("cant format document:%s" % numdoc)
            out.write(t+'\n')
            out.write(t1+'EOD'+'\n')
            t1 = ""
        f2.flush()
        f2.close()
        f7.flush()
        f7.close()
        f8.flush()
        f8.close()
        f9.flush()
        f9.close()
        return errors

    def saldo(self):
        formatLabel("SALDO")
        options = self.config.saldo;
        if (ProductCollection is not None):
            options.products = self.products;
        else:
            options.products = None

        saldo = SaldoCollection(options);
        saldo.parse();
        saldo.format();
        formatLabel("SALDO",end=True)
        print ""

    def main(self):
        if self.config.saldo.do:
            self.saldo();
        if (ProductCollection is None):
            return;
        os.chdir(self.config.paths.magisDB)

        parse.ArtKeyGOD.work_path = self.config.paths.magisDB
        parse.ArtKeyGOD.file_name = self.config.files.products

        parse.ContrKeyGOD.work_path = self.config.paths.magisDB
        parse.ContrKeyGOD.file_name = self.config.files.contractors

        print self.config.paths.importFiles, self.config.files.dolphine_dealers_file
        print self.config.paths.magisDataDir

        txt = open(self.config.files.dolphine_dealers_file).read()
        txt = ANSI(txt)
        contr_key_generator = parse.ContrKeyGOD()
        contr_key_generator.update(parse.parse_dolphine_dealers(txt))

        parsed_dostavki = parse.parse(self.config.paths.importFiles, self.config.files.file_dost, self.config.db.yy)
        parsed_prodagbi = parse.parse(self.config.paths.importFiles, self.config.files.file_prod, self.config.db.yy)
        ### артикули и контрагенти
        self.art(parsed_dostavki, parsed_prodagbi, self.config.files.export.artikuli, self.config.files.export.kontragenti, salda)
        if __debug__:
            print 'kraj na otdelqneto na articuli i contragenti'
        ### операции
        errors = self.make_replic(parsed_dostavki+parsed_prodagbi, self.config.paths.magisDataDir, self.config.db.yy)
        if __debug__:
            print 'kraj na syzdavaneto na repic-files'
        ### imports
        if errors or parse.GroupSelectMP.messages:
            raise Exception(config.errorMessage + '\n' .join((errors+parse.GroupSelectMP.messages)))

if __name__=='__main__':

    a = Proxy({})
    a.test = 5
    assert a.test == 5

    SelectMP(os.path.splitext(__file__)[0] +'.ini').main()