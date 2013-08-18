from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Loong", ".fsm")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 8:
        return 0
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(8), 'utf-16')
    if idstring == "SMM":
        return 1
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

class SanaeParser(object):
    
    def __init__(self, data):    
        
        self.inFile = NoeBitStream(data)
        self.texList = []
        self.matList = []     
        self.boneList = []
        self.animList = []
        self.idxBuffs = []
        
    def build_meshes(self):
        
        self.invert_faces()
        for i in range(len(self.idxBuffs)):
            numIdx, idxBuff = self.idxBuffs[i]
            matName = self.matList[i].name
            
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)            
        
    def read_ustring(self, n):
            
        string = self.inFile.readBytes(n*2)
        return noeStrFromBytes(string, 'utf-16')
    
    def invert_faces(self):
        '''Negates the x-coord of all vertices in the mesh'''
        
        trans = NoeMat43((NoeVec3((-1, 0, 0)),
                         NoeVec3((0, 1, 0)),
                         NoeVec3((0, 0, 1)),
                         NoeVec3((0, 0, 0))))
        rapi.rpgSetTransform(trans)    
    
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            matNum = self.inFile.readUInt()
            matName = "material[%d]" %matNum
            material = NoeMaterial(matName, "")
            
            self.inFile.read('16f')
            self.inFile.readFloat()
            self.inFile.readUShort()
            matType = self.inFile.readShort()
            if matType == 242:
                diffTex = self.read_ustring(768)
                normTex = self.read_ustring(256)
                normTex2 = self.read_ustring(256)
                material.setNormalTexture(normTex)
            else:
                diffTex = self.read_ustring(1296)
            
            material.setTexture(diffTex)           
            self.matList.append(material)
        
    def parse_faces(self, numFaceGroups):
        
        for i in range(numFaceGroups):
            index = self.inFile.readShort()
            self.inFile.readUInt()
            self.inFile.readUShort()
            self.inFile.read('6f')
            numIdx = self.inFile.readUInt() * 3
            idxBuff = self.inFile.readBytes(numIdx*2)
            self.inFile.read('5L')
            self.idxBuffs.append([numIdx, idxBuff])
    
    def parse_vertices(self, numVerts, vertType):
        
        if vertType == 0x01:
            vertBuff = self.inFile.readBytes(numVerts*32)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24) 
        elif vertType == 0x17:
            vertBuff = self.inFile.readBytes(numVerts*44)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 44, 36)
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.read_ustring(4)
        numMesh, vertType, numVerts, vertOfs, numFaceGroups, faceOfs, numMat, matOfs, \
            unk3, unkOff = self.inFile.read('10L')
        self.inFile.read('6f')
        self.inFile.seek(256, 1)
        self.parse_vertices(numVerts, vertType)
        
        self.inFile.seek(faceOfs)
        self.parse_faces(numFaceGroups)
                
        self.inFile.seek(matOfs)        
        self.parse_materials(numMat)
        
        self.build_meshes()
        