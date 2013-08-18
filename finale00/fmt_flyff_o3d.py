from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("FlyFF", ".o3d")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    noesis.logPopup()
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    return 1

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    ctx = rapi.rpgCreateContext()
    parser = SanaeParser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class SanaeParser(SanaeObject):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        super(SanaeParser, self).__init__(data)
        
    def read_name(self, n=0):
        
        if n:
            string = self.inFile.readBytes(n)
        else:
            string = self.inFile.readBytes(self.inFile.readUByte())
        new_str = ""
        for byte in string:
            new_str += chr(byte ^ 0xCD)
        return new_str
        
    def parse_file(self):
        '''Main parser method'''
        
        filename = self.read_name()
        version = self.inFile.readUInt()
        crc = self.inFile.readUInt()
        self.inFile.read('6f')
        if version == 0x16:
            self.inFile.read('6f')
        self.inFile.read('2L')
        self.inFile.read
        print(self.inFile.tell())