from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Youyou Kengeki Musou", ".mdl")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 19:
        return 0
    bs = NoeBitStream(data)
    try:
        idstring = noeStrFromBytes(bs.readBytes(19))
        if idstring != "MgResourceHeadermdl":
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

class SanaeParser(SanaeObject):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        super(SanaeParser, self).__init__(data)
        self.vertBuffs = []
        self.idxBuffs = []
        
    def read_name(self):
        
        name = self.read_string(self.inFile.readUInt())
        self.inFile.readByte()
        return name
    
    def build_mesh(self):
        
        print(len(self.idxBuffs), len(self.matList))
        for i in range(len(self.idxBuffs)):
            vertBuff, vertSize = self.vertBuffs[i]
            idxBuff, numIdx = self.idxBuffs[i]
            
            if i < len(self.matList):
                matName = self.matList[i].name
            else:
                matName = self.matList[-1].name
            
            if vertSize == 56:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 0)
                rapi.rpgBindPositionUV1Ofs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 12)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 56, 28)
            elif vertSize == 72:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 72, 0)
                rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 72, 28)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 72, 44)   
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
    
    def parse_material(self):
        
        self.inFile.read('3L')
        self.inFile.read('8f')
        self.inFile.seek(44, 1)
        self.inFile.readUInt()
        self.inFile.seek(448, 1) #??
        texName = self.read_name()
        self.inFile.seek(5, 1)
        normTex = self.read_name()
        self.inFile.seek(5, 1)
        specTex = self.read_name()
        print(self.inFile.tell())
        self.inFile.seek(30, 1)
        matName = self.read_name()

        material = NoeMaterial(matName, texName)
        self.matList.append(material)               
        
    def parse_vertices(self, numVerts, vertSize):
        vertBuff = self.inFile.readBytes(numVerts*vertSize)
        self.vertBuffs.append([vertBuff, vertSize])
        
            
    def parse_faces(self, numFaces):
        
        numIdx = numFaces * 3
        idxBuff = self.inFile.readBytes(numIdx*2)
        self.idxBuffs.append([idxBuff, numIdx])
        
    def parse_mesh(self, meshNum):
        
        meshName = "obj[%d]" %meshNum
        meshType, vertSize, numVerts, numFaces = self.inFile.read('4L')
        self.inFile.read('3L')
        self.parse_vertices(numVerts, vertSize)
        self.parse_faces(numFaces)
        
        if meshType == 0:
            meshName = self.read_name()
            
    def parse_bones(self):
        
        numBones = self.inFile.readUInt()
        self.inFile.seek(8, 1)
        for i in range(numBones):
            tag = self.read_string(4)
            boneIdx = self.inFile.readUInt()
            self.inFile.seek(8, 1)
            matrix = self.inFile.read('16f')
            self.inFile.seek(48, 1)
            
        name = self.read_name()
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.read_string(32)
        self.inFile.seek(128, 1)
        
        meshNum = 0
        while (self.inFile.tell() != self.inFile.dataSize):
            chunk = self.read_string(4)
            if chunk == "wwDD":
                self.inFile.seek(120, 1)
                numMesh, unk3 = self.inFile.read('2H')
            elif chunk == "mnd":
                self.inFile.seek(124, 1)
            elif chunk == "msh":
                print(self.inFile.tell(), "mesh")
                self.parse_mesh(meshNum)
                meshNum += 1
            elif chunk == "ski":
                self.parse_bones()
            elif chunk == "mat":
                self.parse_material()
            elif chunk == "skl":
                break
            
        print("%d mesh" %meshNum)
        self.build_mesh()