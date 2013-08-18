'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Chinese Paladin 5", ".dff")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    bs = NoeBitStream(data)
    chunk, size = bs.read('2L')
    if chunk != 0x10 or size != bs.dataSize - 12:
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

class Mesh(object):
    
    def __init__(self):
        
        self.numVerts = 0
        self.idxDict = {}
        self.vertBuff = bytes()
        self.normBuff = bytes()
        self.uvBuff = bytes()
        self.materials = []

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
            rapi.rpgBindPositionBuffer(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgBindNormalBuffer(mesh.normBuff, noesis.RPGEODATA_FLOAT, 12)
            
            if mesh.uvBuff:
                rapi.rpgBindUV1Buffer(mesh.uvBuff, noesis.RPGEODATA_FLOAT, 8)
            
            for matNum in mesh.idxDict:
                idxBuff = mesh.idxDict[matNum]
                numIdx = len(idxBuff) // 2
                rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
                ##rapi.rpgSetMaterial(matName)
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
        
    def parse_material(self):
            
        count = self.inFile.readUInt()
        self.read_name()
        self.inFile.read("2L")
        name = self.read_name()
        for i in range(count - 1):
            self.read_name()
            self.inFile.read("3L")
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts*12)
    
    def parse_normals(self, numVerts):
        
        return self.inFile.readBytes(numVerts*12)
    
    def parse_uv(self, count):
        
        return self.inFile.readBytes(count*8)
    
    def parse_unk(self, numVerts):
        
        return self.inFile.readBytes(numVerts*4)
    
    def parse_unk2(self, numVerts):
            
        return self.inFile.readBytes(numVerts*8)    
    
    def parse_faces(self, numFaces):
        
        idxBuff = {}
        for i in range(numFaces):
            temp = self.inFile.readBytes(4)
            matNum = self.inFile.readUShort()
            if matNum not in idxBuff:
                idxBuff[matNum] = bytes()
            temp = temp.join([b"", self.inFile.readBytes(2)])
            idxBuff[matNum] = idxBuff[matNum].join([b"", temp])
        return idxBuff
    
    def parse_mesh(self, mesh):

        meshType, unk = self.inFile.read("2H")
        numFaces, numVerts, unk = self.inFile.read('3L')
        
        if meshType:
            if meshType in [0x3B, 0x7B]:
                self.parse_unk(numVerts)
            elif meshType in [0x1E, 0x3E, 0x3F, 0x5f, 0x1F, 0x7F]:
                self.parse_unk(numVerts)
                mesh.uvBuff = self.parse_uv(numVerts)
            elif meshType in [0xBB]:
                self.parse_unk(numVerts)
                mesh.uvBuff = self.parse_uv(numVerts)
                self.parse_unk2(numVerts)
            elif meshType in [0x72, 0x73]:
                pass
            elif meshType in [0x36, 0x37, 0x76, 0x77]:
                mesh.uvBuff = self.parse_uv(numVerts)
            else:
                print("unk mesh type", hex(meshType))
            mesh.idxDict = self.parse_faces(numFaces)
            self.inFile.read('4f')
            self.inFile.read('2l')
            mesh.vertBuff = self.parse_vertices(numVerts)
            mesh.normBuff = self.parse_normals(numVerts)
        else:
            self.inFile.read('4f')
            self.inFile.read('2l')            
    
    def parse_bones(self, numBones):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        while not self.inFile.checkEOF():        
            chunk, size, unk = self.inFile.read("3L")
            if chunk == 0x10:
                pass
            elif chunk == 0x1A:
                pass
            elif chunk == 0x0F:
                self.inFile.read("3L")
                mesh = Mesh()
                self.parse_mesh(mesh)
                self.meshList.append(mesh)
            elif chunk == 0x03:
                pass
            elif chunk == 0x11F:
                print('material', self.inFile.tell())
                material = self.parse_material()
                mesh.materials.append(material)
            else:
                self.inFile.seek(size, 1)
        self.build_meshes()