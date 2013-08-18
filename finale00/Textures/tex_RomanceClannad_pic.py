'''Clannad RPG RJ087477'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Romancing Clannad RPG", ".pic")
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
        
        self.inFile.readBytes(4)
        self.inFile.readBytes(6)
        self.inFile.read('2L')
        width, height = self.inFile.read('2L')
        self.inFile.read('2H')
        self.inFile.read('2L')
        self.inFile.read('2L')
        self.inFile.read('2L')
        
        pixData = self.inFile.readBytes(width*height*3)        
        imgPix = rapi.imageDecodeRaw(pixData, width, height, "b8g8r8")
        imgPix = rapi.imageFlipRGBA32(imgPix, width, height, 0, 1)
        tex = NoeTexture("texture", width, height, imgPix, noesis.NOESISTEX_RGBA32)
        self.texList.append(tex)