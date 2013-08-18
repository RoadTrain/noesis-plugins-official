'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("9 Dragon", ".x3d")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    bs = NoeBitStream(data)
    idstring = bs.readUInt()
    if idstring != 44545:
        return 0
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
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.dirpath = rapi.getDirForFilePath(rapi.getInputName())
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
        
    def parse_materials(self, meshType):
            
        texName = self.read_name()
        if meshType == 1:
            texName2 = self.read_name()
            
        texPath = self.dirpath + "textures\\" + texName
        matName = "material[%d]" %len(self.matList)
        material = NoeMaterial(matName, texPath)
        self.matList.append(material)
        return matName
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts, meshType):
        
        if meshType == 0:
            vertBuff = self.inFile.readBytes(numVerts*32)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
        elif meshType == 1:
            vertBuff = self.inFile.readBytes(numVerts*40)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 24)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_weights(self, numWeights):
            
        for i in range(numWeights):
            unk = self.inFile.readUInt()
            for j in range(unk):
                self.inFile.readFloat()
                self.inFile.readUInt()
        if numWeights:
            count2 = self.inFile.readUInt()
            self.inFile.seek(count2 * 2, 1)
    
    def parse_meshes(self, numMesh, meshType):
        '''meshType 1 == static, type 0 == skinned'''
        
        for i in range(numMesh):
            self.inFile.readUInt()
            meshName = self.read_name()
            self.inFile.readInt()
            self.read_name()
            matrix = self.inFile.read('16f')
            
            matName = self.parse_materials(meshType)
            numVerts = self.inFile.readUInt()
            self.parse_vertices(numVerts, meshType)
            numIdx = self.inFile.readUInt()
            idxBuff = self.parse_faces(numIdx)
            numWeights = self.inFile.readUInt()
            if numWeights:
                self.parse_weights(numWeights)
            
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readUInt()
        meshType = round(self.inFile.readFloat(), 2)
        self.inFile.seek(60, 1)
        numMesh = self.inFile.readUInt()
        print(meshType)
        if meshType == 0.73:
            self.parse_meshes(numMesh, 1)
        elif meshType == 0.72:
            self.parse_meshes(numMesh, 0)