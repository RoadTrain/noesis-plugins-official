from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Titan Quest", ".tex")
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
        
        idstring = self.inFile.readBytes(3)
        numTex = self.inFile.readUInt()
        self.inFile.readByte()
        dataSize = self.inFile.readUInt() - 4
        self.inFile.seek(4, 1)
        imgData = bytes()
        
        imgData += b"\x44\x44\x53\x20"
        imgData += self.inFile.readBytes(dataSize)
        tex = rapi.loadTexByHandler(imgData, '.dds')
        if tex:
            self.texList.append(tex)