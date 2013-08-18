from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Fantasy Earth Zero Textures", ".tex")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadRGBA(handle, noepyLoadRGBA)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    
    if len(data) < 4:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(4))
        if idstring != "IMG0":
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
        
        return noeStrFromBytes(self.inFile.readBytes(n))
        
    def parse_file(self):
        
        idstring = self.inFile.readBytes(4)
        filesize = self.inFile.readUInt()
        numTex, null = self.inFile.read('2L')
        for i in range(numTex):
            texSize = self.inFile.readUInt()
            texFmt = self.read_name(4)
            self.inFile.read('2L')
            texName = self.read_name(32)
            texData = self.inFile.readBytes(texSize)
            
            tex = rapi.loadTexByHandler(texData, "." + texFmt)
            if tex is not None:
                tex.name = texName
                self.texList.append(tex)            
    