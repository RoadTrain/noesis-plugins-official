from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Touhou Mahjong", ".dat")
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
        
        headerSize = self.inFile.readUInt()
        width, height = self.inFile.read('2L')
        self.inFile.readUInt()
        self.inFile.readUInt()
        pixSize = self.inFile.readUInt()
        self.inFile.read("2L")
        numColors = self.inFile.readUInt()
        self.inFile.readUInt()
        
        if numColors:
            palette = self.inFile.readBytes(numColors*4)
            pixMap = self.inFile.readBytes(width*height)
            pixData = rapi.imageDecodeRawPal(pixMap, palette, height, width, 8, "b8g8r8p8")
        else:
            if pixSize == 0:
                pixSize = width * height * 3            
            pixData = self.inFile.readBytes(pixSize)
            pixData = rapi.imageDecodeRaw(pixData, width, height, 'b8g8r8')
        pixData = rapi.imageFlipRGBA32(pixData, width, height, 0, 1)
        tex = NoeTexture("tex", width, height, pixData, noesis.NOESISTEX_RGBA32)
        self.texList.append(tex)        