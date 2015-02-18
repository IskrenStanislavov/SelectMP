# encoding:cp1251
from dosutil import ANSI, ANSI2OEM
import parse

import time, os
import ConfigParser
from datetime import datetime

class Proxy(object):
    def __init__(self, data):
        self.__dict__["mainData"] = data
    def __setitem__(self, name, value):
        self.mainData[name] = value
    def __getitem__(self, name):
        return self.mainData[name]
    def __setattr__(self, name, value):
        self.mainData[name] = value
    def __getattr__(self, name):
        return self.__dict__["mainData"][name]
config = Proxy({
    "ini_path": 'SelectMP.ini', #os.path.splitext(__file__)[0] +'.ini'
    "missingEIKmessage": "Липсва ЕИК към %s № (%s) от дата:%s; ",
    "exportFiles": Proxy({
        "artikuli": 'artikuli-new.txt',
        "kontragenti": 'contragenti-new.txt'
    }),
    "paths": Proxy({
        "magisDB":"",
        "importFiles":"",
    }),

    "errorMessage": "\n\n!!! Date & time: %s\n"%(datetime.now())
    #missingEIKmessage : "FAKTURA No(%s) ostava nevavedena(nyama vaveden bulstat za CONTRAGENT{%s})"
});


def art(fn, fp, ofnnew, ofcnew, salda):#otdelq artikuli i kontragenti!!!!!
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

def make_replic(info, save_path, yyYearId):
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

def main():
    
    configParser = ConfigParser.ConfigParser()
    configParser.read(config.ini_path)
    config.paths.magisDB = configParser.get('magisPath')
    config.paths.importFiles = configParser.get('import_path')

    parse.ArtKeyGOD.work_path = config.paths.magisDB
    parse.ContrKeyGOD.work_path = config.paths.magisDB

    parse.ArtKeyGOD.file_name = configParser.get( 'art_id_file')
    parse.ContrKeyGOD.file_name = configParser.get( 'contr_id_file')
    obj = configParser.getint('obj1')
    yyYearId = configParser.get('yy')
    dolphine_dealers_file = configParser.get('dealers')
    print config.paths.importFiles, dolphine_dealers_file
    data_path = os.path.join(config.paths.magisDB, "data/", str(obj).zfill(8))
    print data_path
    os.chdir(config.paths.magisDB)
    ### files
    file_dost = configParser.get('file_dost') #'dost_MP.PRN'
    file_prod = configParser.get('file_prod') #'prod_MP.PRN'

    #SALDO
    if configParser.getint( 'saldo_import_run', 0):
        saldo = configParser.get( 'saldo') # saldo_MP.txt
        salda, errlog = parse.start_saldo(saldo)
        parse.make_saldo_replic(salda, data_path, yyYearId)
    else:
        salda = []
    del configParser
    a_new = config.exportFiles.artikuli
    c_new = config.exportFiles.kontragenti
    txt = open(os.path.join(config.paths.importFiles, dolphine_dealers_file)).read()
    txt = ANSI(txt)
    contr_key_generator = parse.ContrKeyGOD()
    contr_key_generator.update(parse.parse_dolphine_dealers(txt))

    parsed_dostavki = parse.parse(config.paths.importFiles, file_dost, yyYearId)
    parsed_prodagbi = parse.parse(config.paths.importFiles, file_prod, yyYearId)
    ### артикули и контрагенти
    art(parsed_dostavki, parsed_prodagbi, os.path.join(config.paths.magisDB, a_new), os.path.join(config.paths.magisDB, c_new), salda)
    if __debug__:
        print 'kraj na otdelqneto na articuli i contragenti'
    ### операции
    errors = make_replic(parsed_dostavki+parsed_prodagbi, data_path, yyYearId)
    if __debug__:
        print 'kraj na syzdavaneto na repic-files'
    ### imports
    if errors or parse.GroupSelectMP.messages:
        raise Exception(config.errorMessage + '\n' .join((errors+parse.GroupSelectMP.messages)))

if __name__=='__main__':
    a = Proxy({})
    a.test = 5
    assert a.test == 5
    main()