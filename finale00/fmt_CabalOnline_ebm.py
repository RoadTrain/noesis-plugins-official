'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi
import math

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Cabal Online", ".ebm;.ech")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = bs.readUInt()
        if idstring not in [0x0003ED03, 0x0003EE03, 0x0003EF03, 0x0003F003]:
            return 0
        return 1
    except:
        return 0
    
def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    

    parser = SanaeParser(data)
    parser.parse_file()
    ctx = rapi.rpgCreateContext()
    
    for i in range(len(parser.vertBuffs)):
        
        vertBuff, numVerts = parser.vertBuffs[i]
        idxBuff, numIdx, matNum = parser.idxBuffs[i]
        matList = [parser.matList[matNum]]
        texList = [parser.texList[matNum]]
        matName = matList[0].name
        
        rapi.rpgReset()
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)        
        rapi.rpgSetMaterial(matName)
        rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)    
        
        
        mdl = rapi.rpgConstructModel()
        
        mdl.setModelMaterials(NoeModelMaterials(texList, matList))
        mdl.setBones(parser.boneList)
        mdl.setAnims(parser.animList)
        mdlList.append(mdl)
    return 1

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.vertBuffs = []
        self.idxBuffs = []
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []        
        self.numBones = 0
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUShort())
        try:
            return noeStrFromBytes(string)
        except:
            return "mesh"
        
    def parse_texture(self):
        texName = self.read_name()
        texSize = self.inFile.readUInt()
        texData = self.inFile.readBytes(texSize)
        self.inFile.seek(26, 1)
        
        tex = rapi.loadTexByHandler(texData, ".dds")
        if tex is not None:
            tex.name = texName
            
            self.texList.append(tex)
        return texName
        
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            diffuse = self.inFile.read('4f')
            ambient = self.inFile.read('4f')
            specular = self.inFile.read('4f')
            emissive = self.inFile.read('4f')
            power = self.inFile.readFloat()
            
            matName = "material[%d]" %len(self.matList)
            texName = self.parse_texture()
            
            material = NoeMaterial(matName, texName)
            material.setDefaultBlend(0)
            self.matList.append(material)
    
    def parse_animations(self, numAnims):
        
        for i in range(numAnims):
            name = self.read_name()
            numBones = self.inFile.readUShort()
            for j in range(numBones):
                boneName = self.read_name()
                numTranslate = self.inFile.readUInt()
                for k in range(numTranslate):
                    keyFrameSec = self.inFile.readFloat()
                    x, y, z = self.inFile.read('3f')
                    keyFrameIndex = int(math.floor(keyFrameSec*100))
                    
                numRotate = self.inFile.readUInt()
                for k in range(numRotate):
                    keyFrameSec = self.inFile.readFloat()
                    x, y, z, w = self.inFile.read('4f')
                    keyFrameIndex = int(math.floor(keyFrameSec*100))                    
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            boneName = self.read_name()
            parentIndex = self.inFile.readUInt()
            boneMatrix = self.inFile.read('16f')
            parentMatrix = self.inFile.read('16f')
    
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(32*numVerts)
        
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
    
    def parse_weights(self):
        
        numWeights = self.inFile.readUShort()
        for i in range(numWeights):
            for j in range(self.numBones):
                count = self.inFile.readUInt()
                boneIDs = self.inFile.read('%dL' %count)
                weights = self.inFile.read('%df' %count)
    
    def parse_meshes(self, numMesh):
        
        print(numMesh, "meshes")
        for i in range(numMesh):
            meshName = self.read_name()
            worldMatrix = self.inFile.read('16f')
            localMatrix = self.inFile.read('16f')
            self.inFile.readInt()
            matNum = self.inFile.readByte()
            numVerts = self.inFile.readUShort()
            numIdx = self.inFile.readUShort() * 3
            vertBuff = self.parse_vertices(numVerts)
            idxBuff = self.parse_faces(numIdx)
            chunk = self.inFile.readUInt()
            if chunk == 0x41470205:
                self.parse_weights()
            else:
                self.inFile.seek(-4, 1)
            
            self.vertBuffs.append([vertBuff, numVerts])
            self.idxBuffs.append([idxBuff, numIdx, matNum])
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readUInt()
        self.inFile.readUShort()
        self.inFile.readUInt()
        bbMin = self.inFile.read('3f')
        bbMax = self.inFile.read('3f')
        self.inFile.readUInt()
        
        while self.inFile.tell() != self.inFile.dataSize:
            chunk = self.inFile.readUInt()
            
            if chunk in [0x41470201]:
                numMat = self.inFile.readUShort()
                self.parse_materials(numMat)
            elif chunk == 0x41470202:
                numMesh = self.inFile.readUShort()
                self.parse_meshes(numMesh)
            elif chunk == 0x41470203:
                numBones = self.inFile.readUShort()
                self.numBones = numBones
                self.parse_bones(numBones)
            elif chunk == 0x41470204:
                
                numAnims = self.inFile.readUShort()
                self.parse_animations(numAnims)