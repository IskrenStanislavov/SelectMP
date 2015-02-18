# encoding: cp1251
import string
import ctypes

_oem = string.join( map( chr, range(128,192) ), '' )
_ansi = string.join( map( chr, range(192,256) ), '' )

def ANSI( s, __trt=string.maketrans( _oem, _ansi ) ):
    #~ print s
    return s.translate( __trt )

def ANSI2OEM( s, __trt=string.maketrans( _ansi, _oem ) ):
    #~ print s
    return s.translate( __trt )

def oemstr(cls,a):
    d = getattr(cls,a)
    def _text( self ):
        v = d.__get__(self)
        #~ print ANSI(v)
        return ANSI(str(v)).rstrip()
    def _text_( self, v ):
        d.__set__(self, ANSI2OEM(v))
    return property(_text,_text_)

def makeOEM2ANSI(TX,TY):
    for a,k in TX._fields_:
        if k._type_ is ctypes.c_char:
            setattr( TY, a, oemstr(TX,a) )


if __name__=='__main__':
    pass
