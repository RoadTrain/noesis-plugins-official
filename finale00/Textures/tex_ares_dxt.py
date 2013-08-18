from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Ares", ".dxt")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadRGBA(handle, noepyLoadRGBA)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    
    return 1

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
        
    def parse_file(self):
        
        size = self.inFile.readUInt() + 4
        name = noeStrFromBytes(self.inFile.readBytes(size))
        width, height = self.inFile.read('2L')
        fmt = noeStrFromBytes(self.inFile.readBytes(4))
        mips = self.inFile.readUInt()
        dataSize = self.inFile.dataSize - self.inFile.tell()
        pixelData = self.inFile.readBytes(dataSize)
        print(fmt)
        if fmt == "DXT1":
            texFmt = noesis.NOESISTEX_DXT1
        elif fmt == "DXT3":
            texFmt = noesis.NOESISTEX_DXT3
        elif fmt == "DXT5":
            texFmt = noesis.NOESISTEX_DXT5
        tex = NoeTexture(name, width, height, pixelData, texFmt)
        self.texList.append(tex)