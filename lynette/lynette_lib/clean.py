import sys
import codecs

from subprocess import ( Popen, PIPE, check_output as co,
                         CalledProcessError )

Python3 = sys.version_info[0] == 3
BaseString = str if Python3 else getattr( str, '__base__' )
Encoding = 'utf-8' if Python3 else None
class NullCodec( object ):
    "Null codec for Python 2"
    @staticmethod
    def decode( buf ):
        "Null decode"
        return buf

    @staticmethod
    def encode( buf ):
        "Null encode"
        return buf

if Python3:
    def decode( buf ):
        "Decode buffer for Python 3"
        return buf.decode( Encoding )

    def encode( buf ):
        "Encode buffer for Python 3"
        return buf.encode( Encoding )
    getincrementaldecoder = codecs.getincrementaldecoder( Encoding )
else:
    decode, encode = NullCodec.decode, NullCodec.encode

    def getincrementaldecoder():
        "Return null codec for Python 2"
        return NullCodec

def sh( cmd ):
    "Print a command and send it to the shell"
    # info( cmd + '\n' )
    result = Popen( [ '/bin/sh', '-c', cmd ], stdout=PIPE ).communicate()[ 0 ]
    return decode( result )