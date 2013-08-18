from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Croixleur", ".rin")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadRGBA(handle, noepyLoadRGBA)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    
    if len(data) < 8:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(8))
        if idstring != "ringtex2":
            return 0
        return 1
    except:
        return 0

def noepyLoadRGBA(data, texList):
    '''Load the texture(s)'''
    
    parser = SanaeParser(data)
    parser.parse_file()
    texList.extend(parser.texList)
    return 1

class SanaeParser(object):
    
    def __init__(self, data):    
        self.inFile = NoeBitStream(data)
        self.texList = []
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
        
    def parse_file(self):
        
        idstring = self.read_name(8)
        self.inFile.readUInt()
        texName = self.read_name(32)
        width, height = self.inFile.read('2L')
        self.inFile.read("3L")
        pixData = self.inFile.readBytes(width*height*4)
        
        tex = NoeTexture(texName, width, height, pixData, noesis.NOESISTEX_RGBA32)
        self.texList.append(tex)