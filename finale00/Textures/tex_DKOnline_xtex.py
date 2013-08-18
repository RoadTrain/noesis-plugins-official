from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("DK Online Texture", ".xtex")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadRGBA(handle, noepyLoadRGBA)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    
    if len(data) < 10:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(6))
        version = bs.readUInt()
        if idstring != "xbin\r\n" or version != 3328:
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
        
    def parse_file(self):
        self.inFile.seek(16)
        name = self.inFile.readString()
        self.inFile.seek(16, 1)
        type, height, width, null = self.inFile.read('4L')
        dxt = noeStrFromBytes(self.inFile.readBytes(4))
        mips = self.inFile.readUInt()
        datSize = self.inFile.dataSize - self.inFile.tell()
        pixelData = self.inFile.readBytes(datSize)
        if dxt == "DXT1":
            texFmt = noesis.NOESISTEX_DXT1
        elif dxt == "DXT3":
            texFmt = noesis.NOESISTEX_DXT3
        elif dxt == "DXT5":
            texFmt = noesis.NOESISTEX_DXT5
        else:
            print("unknown pixel format")
        tex = NoeTexture(name, width, height, pixelData, texFmt)
        self.texList.append(tex)
        