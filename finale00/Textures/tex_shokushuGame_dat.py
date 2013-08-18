from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Shokushu game", ".dat")
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
        
        self.inFile.readUInt()
        pixType = self.inFile.readUInt()
        pixSize = self.inFile.readUInt()
        width, height = self.inFile.read('2H')
        self.inFile.readBytes(4)
        self.inFile.read('3L')
        
        size = width * height * 4
        if size != pixSize:
            print("width off by 1")
            width += 1
            size = width * height * 4
        # RGBA
        if size == pixSize:
            pixData = self.inFile.readBytes(width*height*3)
            pixData = rapi.imageDecodeRaw(pixData, width, height, 'b8g8r8')
            tex = NoeTexture("test", width, height, pixData, noesis.NOESISTEX_RGBA32)
            self.texList.append(tex)
        else:
            #total = 0
            #for i in range(pixSize // 2):
                #count = self.inFile.readByte()
                #self.inFile.readByte()
                #total += count
            #print(total)
            print('unk')
            self.texList.append(None)