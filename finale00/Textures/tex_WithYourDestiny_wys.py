from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("With Your Destiny Texture", ".wys")
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
        
        idstring = self.inFile.read('5s')
        headerSize = self.inFile.readUInt()
        flags = self.inFile.read('4B')
        height, width, pitch, depth, mips = self.inFile.read('5L')
        
        #lazy
        self.inFile.seek(85)
        fmt = noeStrFromBytes(self.inFile.readBytes(4))
        if fmt == "2z73":
            texFmt = noesis.NOESISTEX_DXT1
        elif fmt == "7x0s":
            texFmt = noesis.NOESISTEX_DXT3
        else:
            print("unknown pixel format")
            
        #lazy again
        self.inFile.seek(129)
        dataSize = self.inFile.dataSize - self.inFile.tell()
        pixelData = self.inFile.readBytes(dataSize)
            
        name = rapi.getLocalFileName(rapi.getInputName()).split('.')[0]
        tex = NoeTexture(name, width, height, pixelData, texFmt)
        self.texList.append(tex)
        