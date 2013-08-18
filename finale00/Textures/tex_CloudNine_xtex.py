from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Cloud Nine Texture", ".xtex")
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
        bs.readShort()
        idstring2 = bs.readString()
        if idstring != "xbin\r\n" or idstring2 != "xTexture":
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
        self.inFile.readBytes(6)
        type = self.inFile.readUShort()
        self.inFile.readUShort()
        self.inFile.readUShort()
        name = self.inFile.readString()
        height, width = self.inFile.read('2L')
        dxt = noeStrFromBytes(self.inFile.readBytes(4))
        mips = self.inFile.readUInt()
        self.inFile.readUInt()
        if type in [25392, 25667]:
            self.inFile.seek(8, 1)
        elif type in [4669]:
            pass
        else:
            print("unknown type: %d" %type)
        
        datSize = self.inFile.dataSize - self.inFile.tell()
        pixelData = self.inFile.readBytes(datSize)
        if dxt == "DXT1":
            texFmt = noesis.NOESISTEX_DXT1
        elif dxt == "DXT3":
            texFmt = noesis.NOESISTEX_DXT3
        elif dxt == "DXT5":
            texFmt = noesis.NOESISTEX_DXT5
        else:
            texFmt = noesis.NOESISTEX_RGBA32
            print("unknown pixel format")
        tex = NoeTexture(name, width, height, pixelData, texFmt)
        self.texList.append(tex)
        