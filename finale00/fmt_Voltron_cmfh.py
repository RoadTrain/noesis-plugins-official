'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Voltron", ".cmfh")
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
        
        self.inFile = NoeBitStream(data, NOE_BIGENDIAN)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []      
        self.meshList = []
        rapi.rpgSetOption(noesis.RPGOPT_BIGENDIAN, 1)
        
    def build_mesh(self, numGroups, vertBuff, idxBuff):
        
        inputName = rapi.getLocalFileName(rapi.getInputName())
        filename, ext = os.path.splitext(inputName)        
        for i in range(numGroups):
            vertOfs, numVerts, idxOfs, numIdx = self.meshList[i]
            
            vertStart = vertOfs * 80
            vertEnd = vertStart + (numVerts * 80)
            idxStart = idxOfs * 2
            idxEnd = idxStart + (numIdx * 2)

            vbuff = vertBuff[vertStart:vertEnd]
            ibuff = idxBuff[idxStart:idxEnd]
        
            rapi.rpgBindPositionBufferOfs(vbuff, noesis.RPGEODATA_FLOAT, 80, 0)
            rapi.rpgBindNormalBufferOfs(vbuff, noesis.RPGEODATA_FLOAT, 80, 60)
            rapi.rpgBindUV1BufferOfs(vbuff, noesis.RPGEODATA_FLOAT, 80, 72)
            
            rapi.rpgSetMaterial(filename + "_d")
            rapi.rpgCommitTriangles(ibuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
                
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(80*numVerts)
        return vertBuff
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_groups(self, numGroups):
        
        for i in range(numGroups):
            vertOfs, numVerts, idxOfs = self.inFile.read('>3L')
            numIdx = self.inFile.readUInt() * 3
            self.inFile.readUInt()
            count = self.inFile.readUInt()
            self.inFile.seek(count*4, 1)
            
            self.meshList.append([vertOfs, numVerts, idxOfs, numIdx])
        
    def parse_file(self):
        idstring = self.inFile.read('4s')
        unk, numVerts = self.inFile.read('>2L')
        numIdx = self.inFile.readUInt() * 3
        vertBuff = self.parse_vertices(numVerts)
        idxBuff = self.parse_faces(numIdx)
        numGroups = self.inFile.readUInt()
        self.parse_groups(numGroups)
        self.build_mesh(numGroups, vertBuff, idxBuff)
        