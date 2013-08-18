from inc_noesis import *
import noesis
import rapi
import struct

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("AliceSoft", ".pol")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin.'''
    
    if len(data) < 3:
        return 0
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(4))
    if idstring in ["ZLB", "POL"]:
        return 1
    return 0

def zlib_decompress(bs):
    
    unk, size, zsize = bs.read('3L')
    cmpData = bs.readBytes(zsize)
    decompData = rapi.decompInflate(cmpData, size)
    return decompData

def noepyLoadModel(data, mdlList):
    '''Load the model'''
    
    ctx = rapi.rpgCreateContext()

    #check for compression
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(4))
    if idstring == "ZLB":
        data = zlib_decompress(bs)
    
    parser = RanceQuest_POL(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdlList.append(mdl)
    return 1

class Mesh(object):
    
    def __init__(self):
        
        self.name = ""
        self.matNum = -1
        self.vertBuff = bytes()
        self.numVerts = 0
        
        self.normBuff = bytes()
        self.uvBuff = bytes()
        self.uv2Buff = bytes()
        self.numUV = 0
        self.idxList = []
        self.uvList = []
        self.numFaces = 0

class RanceQuest_POL(object):
    
    def __init__(self, data):    
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        
    def check_padding(self):
        
        unk = self.inFile.readInt()
        while unk == -1:
            unk = self.inFile.readInt()
        return unk

    def read_name(self):

        string = bytes()
        char = self.inFile.readBytes(1)
        while char != b'\x00':
            string += char
            char = self.inFile.readBytes(1)
        try:
            return noeStrFromBytes(string)
        except:
            return noeStrFromBytes(string, "shift-JIS")
        
    def invert_faces(self):
        '''Negates the x-coord of all vertices in the mesh'''
        
        trans = NoeMat43((NoeVec3((-1, 0, 0)),
                         NoeVec3((0, 1, 0)),
                         NoeVec3((0, 0, 1)),
                         NoeVec3((0, 0, 0))))
        rapi.rpgSetTransform(trans)    
        
    #def build_buffers(self, mesh):

        #idxBuff = bytes()
        #normBuff = bytes()
        #vertBuff = bytes()
        #uvBuff = bytes()
        #count = 0
        
        #for i in range(mesh.numFaces):
            #for j in range(3):
                #index = mesh.idxList[i][j]
                #uvIdx = mesh.uvList[i][j]
                #vertBuff += mesh.vertBuff[index*4: index*4 + 12]
                #uvBuff += mesh.uvBuff[uvIdx*4 : uvIdx*4 + 8]
                #idxBuff += struct.pack('L', count)
                #count += 1
                
        #mesh.vertBuff = vertBuff
        #mesh.uvBuff = uvBuff
        #mesh.idxBuff = idxBuff
        #mesh.numIdx = len(idxBuff) // 4
        #mesh.numVerts = len(vertBuff) // 12
    
    def build_meshes(self):
        
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            if mesh.numVerts > 0:
                
                rapi.rpgBindPositionBuffer(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 12)
                self.invert_faces()
                
                if mesh.matNum != -1:
                    matName = self.matList[mesh.matNum].name
                    rapi.rpgSetMaterial(matName)
                rapi.rpgCommitTriangles(mesh.idxBuff, noesis.RPGEODATA_UINT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            boneName = self.read_name()
            unk1, unk2 = self.inFile.read('2L')
            self.inFile.read('7f')
        
    def parse_submaterials(self, numMat):
        
        for i in range(numMat):
            matName = self.read_name()
            index = self.inFile.readUInt()
            if index >= 1:
                texName = self.read_name()
                unk2  = self.inFile.readUInt()
            if index >= 2:
                texName2 = self.read_name()
                unk3 = self.inFile.readUInt()
            if index >= 3:
                self.read_name()
                self.inFile.readUInt()
            if index >= 4:
                self.read_name()
                self.inFile.readUInt()                
        
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            matName = self.read_name()
            material = NoeMaterial(matName, "")
            index = self.inFile.readUInt()
            if index == 0:
                #submaterials
                numSubMat = self.inFile.readUInt()
                self.parse_submaterials(numSubMat)
            else:
                texName = self.read_name()
                material.setTexture(texName)
                if index >= 2:
                    self.inFile.readUInt()
                    specName = self.read_name()
                if index >= 3:
                    self.inFile.readUInt()
                    glareName = self.read_name()
                if index >= 4:
                    self.inFile.readUInt()
                    normName = self.read_name()
                if index >= 5:
                    self.inFile.readUInt()
                    heightName = self.read_name()
                unk2, unk3 = self.inFile.read('2L')
            self.matList.append(material)
        
    def parse_vertices(self, numVerts):
        
        vertBuff = bytes()
        if self.meshType == 1:
            for i in range(numVerts):
                
                verts = self.inFile.readBytes(12)
                unk1, unk2 = self.inFile.read('2H')
                if unk1 == 1 and unk2 != 0: 
                    self.inFile.readFloat()
                else:
                    for j in range(unk1):
                        boneIndex = self.inFile.readUInt()
                        boneWeight = self.inFile.readFloat()
                vertBuff += verts
            
        elif self.meshType == 2:
        
            for i in range(numVerts):
                verts = self.inFile.readBytes(12)
                unk1 = self.inFile.readUShort()
                for j in range(unk1):
                    boneIndex = self.inFile.readUShort()
                    boneWeight = self.inFile.readFloat()
                vertBuff += verts
        return vertBuff
            
    def parse_UV(self, numUV):
        
        return self.inFile.readBytes(numUV * 8)
            
    def parse_UV2(self, numUV):
        
        return self.inFile.readBytes(numUV * 8)
            
    def parse_faces(self, numFace, numUV2, unk2):
        
        idxBuff = bytes()
        uvList = []
        for j in range(numFace):
            indexes = self.inFile.readBytes(12)
            #indexes = self.inFile.read('3L')
            uvs = self.inFile.read('3L')
            
            if numUV2 or unk2:
                uv21, uv22, uv23 = self.inFile.read('3L')
            self.inFile.read('3L')
            self.inFile.read('9f')
            self.inFile.readUInt()
            idxBuff += indexes
            uvList.append(uvs)
        return idxBuff, uvList
            
    def parse_unk(self, count):
        
        if self.meshType == 1:
            self.inFile.seek(count*12, 1)
        elif self.meshType == 2:
            self.inFile.seek(count*4, 1)
                
    def parse_unk2(self, count):
        
        self.inFile.seek(count, 1)
    
    def parse_meshes(self, numMesh):
        
        for i in range(numMesh):
            mesh = Mesh()
            mesh.name = self.read_name()
            mesh.matNum = self.inFile.readInt()
            mesh.numVerts = self.inFile.readUInt()
            mesh.vertBuff = self.parse_vertices(mesh.numVerts)
            mesh.numUV = self.inFile.readUInt()
            mesh.uvBuff = self.parse_UV(mesh.numUV)
            numUV2 = self.inFile.readUInt()
            self.parse_UV2(numUV2)
            
            numUnk = self.inFile.readUInt()
            self.parse_unk(numUnk)
            
            numUnk2 = 0
            if self.meshType == 2:
                numUnk2 = self.inFile.readUInt()
                self.parse_unk2(numUnk2)
            
            mesh.numFaces = self.inFile.readUInt()
            mesh.idxBuff, mesh.uvList = self.parse_faces(mesh.numFaces, numUV2, numUnk2)
            mesh.numIdx = mesh.numFaces * 3
            
            if self.meshType == 1:
                self.inFile.seek(8, 1)
                
            self.meshList.append(mesh)
            
            numBones = self.check_padding()
            if numBones > 0:
                break
        #self.parse_bones(numBones)
                
    def parse_file(self):

        idstring = self.inFile.readBytes(4)
        self.meshType = self.inFile.readUInt()
        numMat = self.inFile.readUInt()
        
        self.parse_materials(numMat)
        numMesh = self.inFile.readUInt()
        self.check_padding()
        self.parse_meshes(numMesh)
        self.build_meshes()