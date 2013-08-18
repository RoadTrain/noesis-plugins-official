from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Scarlet Legacy Textures", ".pkt")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadRGBA(handle, noepyLoadRGBA)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(3))
    if idstring == "GRO":
        return 1
    return 0

def zlib_decompress(bs):
    
    bs.seek(bs.dataSize - 4)
    size = bs.readUInt()
    bs.seek(0x40)
    zsize = bs.readUInt()    
    cmpData = bs.readBytes(zsize)
    decompData = rapi.decompInflate(cmpData, size)
    return decompData

def noepyLoadRGBA(data, texList):
    '''Load the texture(s)'''
    
    bs = NoeBitStream(data)
    if noeStrFromBytes(bs.readBytes(3)) == "GRO":
        data = zlib_decompress(bs)
        
    parser = SanaeParser(data)
    parser.parse_file()
    texList.extend(parser.texList)
    return 1

class SanaeParser(object):
    
    def __init__(self, data):    
        self.inFile = NoeBitStream(data)
        self.texList = []
        
    def parse_file(self):
        
        self.inFile.readBytes(4)
        texData = self.inFile.readBytes(self.inFile.dataSize - 4)
        tex = rapi.loadTexByHandler(texData, ".dds")
        if tex:
            tex.name = "texture"
            self.texList.append(tex)        