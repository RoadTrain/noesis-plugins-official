'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

_ENDIAN = 0 # 1 for big endian

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Rise of Flight", ".mgm")
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
        
        self.inFile = NoeBitStream(data, _ENDIAN)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.filename = rapi.getLocalFileName(rapi.getInputName())
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
        
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*36)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 12)
    
    def parse_faces(self, numIdx):
        
        idxBuff = self.inFile.readBytes(numIdx*2)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def parse_file(self):
        '''Main parser method'''
        
        # hardcoded for infantry.mgm
        
        # forget parsing, just go to where the info we need is
        self.inFile.seek(1821)
        numVerts = self.inFile.readUInt()
        numIdx = self.inFile.readUInt()
        vertOfs, idxOfs, vertSize = self.inFile.read('3L')
        self.inFile.seek(vertOfs)
        self.parse_vertices(numVerts)
        
        self.inFile.seek(idxOfs)
        self.parse_faces(numIdx)
                         
        
        