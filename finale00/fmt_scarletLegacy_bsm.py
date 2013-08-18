'''
Scarlet Legacy plugin
Updated Jun 20, 2012
'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Scarlet Legacy", ".bsm")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify the file format matches this plugin. Return 1 if yes,
    0 otherwise'''
    
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(3))
    bs.readByte()
    bs.readUInt()
    delimiter = bs.readByte()
    if idstring == "UJV" or delimiter == 1:
        return 1
    return 0

def zlib_decompress(bs):
    
    bs.seek(bs.dataSize - 4)
    size = bs.readUInt()
    bs.seek(0x40)
    zsize = bs.readUInt()    
    cmpData = bs.readBytes(zsize)
    decompData = rapi.decompInflate(cmpData, size)
    return decompData

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    bs = NoeBitStream(data)
    if noeStrFromBytes(bs.readBytes(3)) == "UJV":
        data = zlib_decompress(bs)
    
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
        self.vertBuff = bytes()
        self.numVerts = 0
        self.idxBuff = bytes()
        self.numIdx = 0

class SanaeParser(object):
    
    def __init__(self, data):    
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
      
    def read_name(self):

        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
    
    def build_meshes(self):
        
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            print(mesh.name)
            if "lod01" not in mesh.name:
                continue
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, mesh.vertSize, 0)
            rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_HALFFLOAT, mesh.vertSize, 6)
            rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_HALFFLOAT, mesh.vertSize, 10)
            matName = self.matList[i].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
    
    def parse_vertices(self, numVerts, vertSize):
        
        return self.inFile.readBytes(numVerts*vertSize)
           
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
            
    def parse_unkData1(self):
        
        unk1 = self.inFile.readUInt()
        for i in range(unk1):
            self.read_name()
            self.read_name()
            self.inFile.read('7b')
            self.inFile.read('48f')
            check = self.inFile.readUInt()
            while check:
                self.read_name()
                self.inFile.read('7b')
                self.inFile.read('48f')
                check = self.inFile.readUInt()
        
    def parse_materials(self):
        
        unk2 = self.inFile.readUInt()
        self.inFile.read('2L')
        for i in range(unk2):
            self.inFile.read('2L')
        if unk2 == 1:
            matName = self.read_name()
            
            material = NoeMaterial(matName, "")
            material.setTexture(matName + "_D")
            self.matList.append(material)
        else:
            count = self.inFile.readUInt()
            for i in range(count):
                matName = self.read_name()
            material = NoeMaterial(matName, "")
            material.setTexture(matName + "_D")
            self.matList.append(material)            
                
    def parse_meshBones(self, numBones):
        
        for i in range(numBones):
            self.read_name()
                
    def parse_mesh(self, numMesh):
        
        for i in range(numMesh):
            mesh = Mesh()
            self.inFile.readUByte()
            mesh.name = self.read_name()
            meshType = self.inFile.readUInt()
            self.inFile.readUInt()
            if meshType == 6:
                self.inFile.seek(98, 1)
            elif meshType == 5:
                self.inFile.seek(81, 1)
                
            mesh.numVerts, mesh.vertSize = self.inFile.read('2L')
            self.inFile.readUByte()
            mesh.vertBuff = self.parse_vertices(mesh.numVerts, mesh.vertSize)
            
            mesh.numIdx, idxSize = self.inFile.read('2L')
            self.inFile.readUByte()
            mesh.idxBuff = self.parse_faces(mesh.numIdx)
            self.inFile.readUInt()
            self.inFile.read('6f')
            numBones = self.inFile.readUInt()
            self.parse_meshBones(numBones)
            self.parse_unkData1()
            self.parse_materials()
            self.meshList.append(mesh)

    def parse_file(self):
        '''Main parser method. Can be replaced'''
        
        self.inFile.readUInt()
        numMesh = self.inFile.readUInt()
        self.parse_mesh(numMesh)
        self.build_meshes()