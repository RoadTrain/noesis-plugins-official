'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Seven Souls", ".msh")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    # file ID is the numeric part of the filename
    filename = rapi.getLocalFileName(rapi.getInputName())
    fileID = ''.join(c for c in filename if c.isdigit())
    bs = NoeBitStream(data)
    idstring = bs.readUInt()
    if idstring == int(fileID) or idstring == 1213416781: #MESH
        return 1
    return 0

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    ctx = rapi.rpgCreateContext()
    filename = rapi.getLocalFileName(rapi.getInputName())
    fileID = ''.join(c for c in filename if c.isdigit())    
    bs = NoeBitStream(data)
    idstring = bs.readUInt()
    idstring2 = bs.readUInt()
    
    if idstring == 1213416781: #MESH
        if idstring2 == 1:
            parser = StaticParser1(data)
        elif idstring2 == 2:
            parser = StaticParser2(data)
    else:
        parser = SanaeParser(data)
    print(idstring)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class Mesh(object):
    '''A generic mesh object, for convenience'''
    
    def __init__(self):
        
        self.positions = bytes()
        self.normals = bytes()
        self.uvs = bytes()
        self.numVerts = 0
        self.numIdx = 0
        self.idxBuff = bytes()
        self.matName = ""
        self.meshName = ""
        
class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        
    def build_mesh(self):
        
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
   
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_UINT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)         
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
    
    def parse_vertices(self, numVerts):
    
        return self.inFile.readBytes(numVerts*32)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 4)
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readUInt()
        idstring2 = self.inFile.readBytes(4)
        mesh = Mesh()
        
        mesh.meshName = self.read_name()
        mesh.numVerts = self.inFile.readUInt()
        mesh.numIdx = self.inFile.readUInt() * 3
        numWeights1, numWeights2 = self.inFile.read('2L')
        mesh.vertBuff = self.parse_vertices(mesh.numVerts)
        mesh.idxBuff = self.parse_faces(mesh.numIdx)
        
        #self.parse_weights1(numWeights1)
        #self.parse_weights2(numWeights2)
        self.meshList.append(mesh)
        
        #texFile = rapi.loadPairedFileOptional("Seven Souls Textures", ".*")
        
        self.build_mesh()
        
class StaticParser1(SanaeParser):
    '''For static meshes. Idstring "MESH".'''
    
    def build_mesh(self):
        
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 52, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 52, 12)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 52, 24)
   
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_UINT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)                 
    
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(52*numVerts)
    
    def parse_file(self):
        
        idstring = self.inFile.readBytes(4)
        self.inFile.read('3L')
        modelName = self.read_name()
        
        mesh = Mesh()
        mesh.numVerts = self.inFile.readUInt()
        mesh.numIdx = self.inFile.readUInt() * 3
        mesh.vertBuff = self.parse_vertices(mesh.numVerts)
        mesh.idxBuff = self.parse_faces(mesh.numIdx)
        self.meshList.append(mesh)
        
        self.build_mesh()

class StaticParser2(StaticParser1):
    
    def build_mesh(self):
            
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 68, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 68, 12)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 68, 24)
   
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)                 
    
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts*68)
    
    def parse_unk(self):
        
        count = self.inFile.readUByte()
        self.inFile.seek(count, 1)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_file(self):
        
        idstring = self.inFile.readBytes(4)
        self.inFile.read('3L')
        modelName = self.read_name()
        
        mesh = Mesh()
        mesh.numVerts = self.inFile.readUInt()
        mesh.numIdx = self.inFile.readUInt() * 3
        mesh.vertBuff = self.parse_vertices(mesh.numVerts)
        self.parse_unk()
        mesh.idxBuff = self.parse_faces(mesh.numIdx)
        self.meshList.append(mesh)
        
        self.build_mesh()    