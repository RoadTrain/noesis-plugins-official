from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Deadly Premonition", ".xpc")
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

class Texture(object):
    
    def __init__(self):
        
        name = ""
        offset = 0
        size = 0

class SanaeParser(object):
    
    def __init__(self, data):    
        
        self.inFile = NoeBitStream(data)
        self.texList = []
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
        
    def parse_file(self):
        
        idstring = self.inFile.readBytes(4)
        filesize = self.inFile.readUInt()
        
        numTex = self.inFile.readUShort()
        self.inFile.readUShort()
        self.inFile.seek(52, 1)
        
        texInfo = []
        for i in range(numTex):
            tex = Texture()
            tex.name = self.read_name(16)
            tex.offset = self.inFile.readUInt()
            tex.size = self.inFile.readUInt()
            self.inFile.read('4H')
            texInfo.append(tex)
            
        for entry in texInfo:
            self.inFile.seek(entry.offset)
            data = self.inFile.readBytes(entry.size)
            tex = rapi.loadTexByHandler(data, '.dds')
            if tex:
                tex.name = entry.name
                self.texList.append(tex)