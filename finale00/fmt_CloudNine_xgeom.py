'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Cloud Nine", ".xgeom")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
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

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.matList = []
        self.texList = []
        self.animList = []
        self.boneList = []
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUShort() + 1) # null-term
        return noeStrFromBytes(string)
    
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts * 32)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_materials(self):
        
        matName = self.read_name()
        self.inFile.readByte() # delim?
        self.inFile.read('17f') # mat properties
        self.inFile.readUInt() # num Tex?
        texName = self.read_name()
        self.inFile.readUInt()
        specName = self.read_name()
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(6)
        self.inFile.readShort()
        self.inFile.readShort()
        self.read_name()
        meshName = self.read_name()
        
        self.inFile.readByte() # delim?
        bbox = self.inFile.read('6f')
        
        self.inFile.readUInt()
        self.inFile.readUInt()
        numVerts, numIdx = self.inFile.read('2H')
        vertBuff = self.parse_vertices(numVerts)
        idxBuff = self.parse_faces(numIdx)
        
        self.parse_materials()
        
        rapi.rpgSetName(meshName)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_SHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)