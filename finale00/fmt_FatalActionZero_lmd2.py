'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Fatal Action Zero", ".lmd2")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    bs = NoeBitStream(data)
    idstring = bs.readUInt()
    if idstring == 0x17:
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

class Mesh(object):
    
    def __init__(self):
        
        self.name = ""
        self.numIdx = 0
        self.numVerts = 0
        self.vertSize = 0
        self.idxBuff = bytes()
        self.vertBuff = bytes()

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
        
    def build_meshes(self):
        
        for mesh in self.meshList:
            
            if mesh.vertType == 3:
                rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 48, 0)
            elif mesh.vertType == 9:
                rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 72, 0)
                rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 72, 52)
                rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 72, 40)
            
            for numIdx, idxBuff, matName in mesh.faceGroups:
                rapi.rpgSetMaterial(matName)
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readShort())
        return noeStrFromBytes(string)
        
    def parse_materials(self, numMat):
            
        for i in range(numMat):
            self.inFile.read('17f')
            matName = self.read_name()
            self.inFile.readUInt()
            numTex = self.inFile.readUInt()
            
            texNames = []
            for j in range(numTex):
                texName = self.read_name()
                self.inFile.readUInt()
                texNames.append(texName)
                
            material = NoeMaterial(matName, "")
            if texNames:
                material.setTexture(texNames[0])
            self.matList.append(material)
        
    def parse_textures(self, numTex):
            
        for i in range(numTex):
            texName = self.read_name()
            texSize = self.inFile.readUInt()
            texData = self.inFile.readBytes(texSize)
            
            tex = rapi.loadTexByHandler(texData, ".dds")
            if tex:
                tex.name = texName
                self.texList.append(tex)
        
    def parse_vertices(self, numVerts, vertType):
        
        if vertType == 9:
            return self.inFile.readBytes(numVerts * 72)
        elif vertType == 3:
            return self.inFile.readBytes(numVerts * 48)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_face_groups(self, numGroups):
        
        faceGroups = []
        
        for i in range(numGroups):
            numIdx = self.inFile.readUInt()
            idxBuff = self.parse_faces(numIdx)
            self.inFile.readUInt()
            matName = self.read_name()
            faceGroups.append([numIdx, idxBuff, matName])
        return faceGroups
    
    def parse_meshes(self, numMesh):
        
        for i in range(numMesh):
            print(self.inFile.tell())
            mesh = Mesh()
            self.inFile.readUInt()
            mesh.meshName = self.read_name()
            self.inFile.read('16f')
            mesh.vertType = self.inFile.readUInt()
            mesh.numVerts = self.inFile.readUInt()
            self.inFile.readByte() #delim?
            mesh.vertBuff = self.parse_vertices(mesh.numVerts, mesh.vertType)
            
            # face groups
            self.inFile.readUInt() # zero
            numGroups = self.inFile.readUInt() # face groups
            mesh.faceGroups = self.parse_face_groups(numGroups)
            
            count = self.inFile.readUInt()
            self.inFile.readBytes(count*4)
            self.inFile.readUInt()            
            self.inFile.readByte()
            self.meshList.append(mesh)
        
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readUInt()
        base = self.read_name()
        self.inFile.readUInt()
        self.inFile.readUInt()
        numMesh = self.inFile.readUInt()
        self.parse_meshes(numMesh)
        
        self.inFile.read('2L')
        self.read_name()
        numMat = self.inFile.readUInt()        
        self.parse_materials(numMat)
        
        numTex = self.inFile.readUInt()
        self.parse_textures(numTex)
        self.build_meshes()