from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("LithTech Textures", ".dtx")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadRGBA(handle, noepyLoadRGBA)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    
    if len(data) < 8:
        return 0
    try:
        bs = NoeBitStream(data)
        int1 = self.inFile.readUInt()
        int2 = self.inFile.readInt()
        
        if int1 != 0 or int2 != -5:
            return 0
        return 1
    except:
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
        
    def get_pixels(self, width, height, fmt1, fmt2, fmt3):
        
        dx = (width + 3) >> 2
        dy = (height + 3) >> 2
        
        if fmt3 in [0, 3]:
            pixelData = self.inFile.readBytes(4*width*height)
            if fmt1 == 0x8:
                imgData = rapi.imageEncodeRaw(pixelData, width, height, 'b8g8r8')
                return NoeTexture("texture", width, height, imgData, noesis.NOESISTEX_RGB24)
            elif fmt1 == 0x88:
                imgData = rapi.imageEncodeRaw(pixelData, width, height, 'b8g8r8a8')
                return NoeTexture("texture", width, height, imgData, noesis.NOESISTEX_RGBA32)
        elif fmt3 == 4:                
            pixelData = self.inFile.readBytes(8 * dx * dy)
            return NoeTexture("texture", width, height, pixelData, noesis.NOESISTEX_DXT1)
        elif fmt3 == 6:
            pixelData = self.inFile.readBytes(16 * dx * dy)
            return NoeTexture("texture", width, height, pixelData, noesis.NOESISTEX_DXT5)
            
    def parse_file(self):
        
        #width and height might be stored in different places
        check = self.inFile.readUInt()
        if check != 0:
            self.inFile.seek(-4, 1)
            height, width = self.inFile.read('2H')
            self.inFile.read("2L")
        else:
            self.inFile.readInt()
            height, width = self.inFile.read('2H')            
        mipmaps = self.inFile.readUInt()
        fmt1 = self.inFile.readUInt()
        fmt2 = self.inFile.readUInt()
        self.inFile.readUShort()
        fmt3 = unk2 = self.inFile.readUShort()
        self.inFile.seek(136, 1)
        pixSize = 4 * width * height
        tex = self.get_pixels(width, height, fmt1, fmt2, fmt3)
        self.texList.append(tex)  
