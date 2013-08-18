'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Legend of Edda", ".mod")
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
        if idstring != 2:
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

class Mesh(object):
    
    def __init__(self):
        
        self.numVerts = 0
        self.numUV = 0
        self.numIdx = 0
        self.numFaceGroups = 0
        self.vertBuff = bytes()
        self.uvBuff = bytes()
        self.idxBuffs = []

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
        
    def plot_points(self, numVerts):
            
        rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, numVerts, noesis.RPGEO_POINTS, 1)    
        
    def build_mesh(self):
        
        for i in range(len(self.meshList)):
            mesh = self.meshList[i]
            rapi.rpgBindPositionBuffer(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 12)
            self.plot_points(mesh.numVerts)
            
            #for j in range(1):
                #idxBuff, numIdx = mesh.idxBuffs[j]
                #rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
        
    def read_name(self, n):
        
        string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)
        
    def parse_material(self):
            
        self.inFile.seek(156, 1)
        texName = self.read_name(1152)
        matName = self.read_name(128)
        self.inFile.read('2L')
        
    def parse_vertices(self, numVerts, mesh):
        
        vertBuff = self.inFile.readBytes(numVerts*12)
        uvBuff = self.inFile.readBytes(numVerts*8)
        return vertBuff, uvBuff
    
    def parse_unk1(self, count):
        
        self.inFile.readBytes(count*4)
        
    def parse_unk2(self, count):
        
        for i in range(count):
            self.inFile.readByte()
            self.inFile.readUInt()
            
    def parse_unk3(self, count):
        
        self.inFile.readBytes(count*44)
        
        
    def parse_normals(self, numNorms):
    
        return self.inFile.readBytes(numNorms*12)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)    
    
    def parse_face_unk(self, count):
        
        self.inFile.readBytes(count*8)
        
    def parse_face_groups(self, numFaceGroups, mesh):
        
        for i in range(numFaceGroups):
            self.inFile.read('2L')
            numIdx = self.inFile.readUInt() * 3
            numIdx2 = self.inFile.readUInt() * 3
            null = self.inFile.readUInt()
            count = self.inFile.readUInt()
            null = self.inFile.readUInt()
            idxBuff = self.parse_faces(numIdx)
            self.parse_face_unk(count)
            
            mesh.idxBuffs.append([idxBuff, numIdx])
    
    def parse_mesh(self):
        
        mesh = Mesh()
        self.inFile.seek(188, 1)
        self.inFile.read('2L')
        meshName = self.read_name(128)
        numVerts, numUV = self.inFile.read('2L')
        if numVerts != numUV:
            numVerts, numUV = self.inFile.read('2L')
        unk0, unk1, numNorms = self.inFile.read('3L')
        unk = self.inFile.readInt()
        numFaceGroups = self.inFile.readUInt()
        self.inFile.read('2L')
        vertBuff, uvBuff = self.parse_vertices(numVerts, mesh)
        self.inFile.read('3f')
        
        self.parse_unk1(unk1)
        self.parse_face_groups(numFaceGroups, mesh)
        
        unk2, unk3, unk6 = self.inFile.read('3L')
        self.parse_unk2(unk2)
        self.parse_unk3(unk3)
        normBuff = self.parse_normals(numNorms)
        
        mesh.numVerts = numVerts
        mesh.vertBuff = vertBuff
        mesh.uvBuff = uvBuff
        mesh.normBuff = normBuff
        mesh.numFaceGroups = numFaceGroups
        self.meshList.append(mesh)

    def parse_bone(self):
        
        pass
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readUInt()
        numBones, numMat, numMesh, null, null, numChunk = self.inFile.read('6L')
        
        while self.inFile.tell() != self.inFile.dataSize:
            tag, size = self.inFile.read('2L')
            if tag == 0xF4000000:
                self.parse_mesh()
            elif tag == 0xF5000000:
                #self.parse_bone()
                self.inFile.seek(size, 1)
            elif tag == 0x000F0000:
                self.parse_material()
            else:
                self.inFile.seek(size, 1)
                
        self.build_mesh()