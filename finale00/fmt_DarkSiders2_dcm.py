'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

_ENDIAN = 0 # 1 for big endian

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Dark Siders 2", ".dcm")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 0:
        return 0
    bs = NoeBitStream(data)
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
        
        self.inFile = NoeBitStream(data, _ENDIAN)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.filename = rapi.getExtensionlessName(rapi.getLocalFileName(rapi.getInputName()))
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readShort())
        return noeStrFromBytes(string)
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts * 52)
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_unk1(self, count):
        
        return self.inFile.readBytes(count * 16)
    
    def parse_unk2(self, count):
        
        return self.inFile.readBytes(count * 4)
    
    def parse_unk3(self, count):
        
        return self.inFile.readBytes(count * 12)
    
    def parse_skinned_meshes(self, numMesh):
        
        for i in range(numMesh):
            mesh = self.meshList[i]
            
            dataSize, structSize = self.inFile.read('2L')
            idxBuff = self.parse_faces(mesh.numIdx)
            self.parse_unk3(mesh.numVerts)
            vertBuff = self.parse_vertices(mesh.numVerts)
            normBuff = self.parse_unk1(mesh.numVerts)
            self.parse_unk2(mesh.numVerts)

            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 52, 4)
            #rapi.rpgBindNormalBufferOfs(normBuff, noesis.RPGEODATA_HALFFLOAT, 16, 6)
            #rapi.rpgSetMaterial("mat")
            #rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, mesh.numVerts, noesis.RPGEO_POINTS, 1)        
            rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)        
            
    def parse_static_meshes(self, numMesh):
        
        for i in range(numMesh):
            mesh = self.meshList[i]
            dataSize, structSize = self.inFile.read('2L')
            idxBuff = self.parse_faces(mesh.numIdx)
            vertBuff = self.inFile.readBytes(mesh.numVerts * 12)
            self.inFile.readBytes(mesh.numVerts * 20)
            self.inFile.readBytes(mesh.count3 * 16)
            
            rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, mesh.numIdx, noesis.RPGEO_TRIANGLE, 1)                    
            
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            self.inFile.readByte()
            self.read_name()
            self.inFile.read('16f')
            self.inFile.readUInt()
            
    def parse_submeshes(self, numSubmesh):
        
        submeshList = []
        for i in range(numSubmesh):
            mesh = Mesh()
            self.inFile.readByte()
            meshName = self.read_name()
            matNum = self.inFile.readUInt()
            self.inFile.readUInt()
            mesh.numVerts, mesh.vertStart, mesh.numIdx, mesh.idxStart = self.inFile.read('4L')
            submeshList.append(mesh)
        return submeshList

    def parse_file(self):
        '''Main parser method'''
        
        meshStart = self.inFile.readUInt()
        numMesh = self.inFile.readUInt()
        for i in range(numMesh):
            mesh = Mesh()
            self.meshList.append(mesh)
        
        numFaceGroups = self.inFile.readUInt()
        for i in range(numFaceGroups):
            self.meshList[i].numIdx = self.inFile.readUShort()
            self.inFile.readUShort()
        
        numVertGroups = abs(self.inFile.readInt())
        for i in range(numVertGroups):
            self.meshList[i].numVerts = abs(self.inFile.readShort())
            self.inFile.readUShort()
            
        # don't know...
        numVertGroups2 = abs(self.inFile.readInt())
        for i in range(numVertGroups2):
            self.meshList[i].count3 = self.inFile.readInt()
            self.inFile.readFloat()
        
        for i in range(numMesh):
            modelType = self.inFile.readByte()
            self.inFile.readByte() #delim?
            numVerts = self.inFile.readUInt()
            self.inFile.read('2L')
            numSubmesh = self.inFile.readUInt()
            numBones = self.inFile.readUInt()
            self.inFile.read('6f')
            
            if modelType == 1:
                self.parse_bones(numBones)
                
            if modelType == 1:
                mesh.submeshes = self.parse_submeshes(numSubmesh)
            elif modelType == 0:
                mesh.submeshes = self.parse_submeshes(numBones) # treated as submesh count
         
        if modelType == 0: # static
            self.parse_static_meshes(numMesh)
        elif modelType == 1: # skinned        
            self.parse_skinned_meshes(numMesh)
        
        print(self.inFile.tell(), self.inFile.tell() == self.inFile.dataSize)