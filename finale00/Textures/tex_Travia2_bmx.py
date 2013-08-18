from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Travia 2 Textures", ".bmx")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadRGBA(handle, noepyLoadRGBA)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    
    if len(data) < 3:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(3))
        if idstring != "BMX":
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
        
        idstring = self.inFile.readBytes(3)
        imgType = self.inFile.readByte()
        self.inFile.seek(143, 1)
        self.inFile.readUInt()
        size = self.inFile.readUInt()
        texData = self.inFile.readBytes(size)
        
        tex = None
        if imgType == 0:
            tex = rapi.loadTexByHandler(texData, ".jpg")
        elif imgType in [1, 2]:
            tex = rapi.loadTexByHandler(texData, ".tga")
        else:
            print("unknown image type: %d" %imgType)
        if tex is not None:
            tex.name = "texture"
            self.texList.append(tex)                        