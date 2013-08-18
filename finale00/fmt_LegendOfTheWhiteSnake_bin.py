'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Legend of White Snake", ".bin")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 26:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(bs.readUInt()))
        if idstring != "serialization::archive":
            return 0
        return 1
    except:
        return 0

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

class Mesh(object):
    
    def __init__(self):
        
        self.name = ""
        self.numIdx = 0
        self.numVerts = 0
        self.vertSize = 0
        self.idxBuff = bytes()
        self.vertBuff = bytes()

class SanaeParser(SanaeObject):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        super(SanaeParser, self).__init__(data)
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
        
    def parse_materials(self, numMat):
            
        for i in range(numMat):
            matName = self.read_name()
            self.inFile.readUInt()
            self.inFile.read('11f')
            self.inFile.seek(3, 1)
            self.inFile.read('2L')
            self.inFile.readShort()
            self.inFile.readUInt()
            texName = self.read_name()
            
            self.inFile.seek(15, 1)
            self.inFile.readUInt()
            self.inFile.read('16f')
            self.inFile.seek(55, 1)
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        pass
    
    def parse_faces(self, numIdx):
        
        pass    
    
    def parse_meshes(self, numMesh):
        
        pass
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.read_name()
        self.inFile.seek(5, 1)
        unk, unk, numMat, unk = self.inFile.read('4L')
        self.inFile.readShort()
        self.parse_materials(numMat)
        