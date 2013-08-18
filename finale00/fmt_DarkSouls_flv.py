'''Dark Souls .flv/.flver model importer.

Note that there are little and big endian versions of the game, and they
are basically the same format. Therefore, all'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Dark Souls", ".flv;.flver")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 12:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(6))
        if idstring == "FLVER":
            return 1
        return 0
    except:
        return 0
    
def get_endian(data):
    
    bs = NoeBitStream(data)
    bs.seek(6)
    endian = bs.readByte()
    if endian == 0x4C: # "L"
        return 0
    elif endian == 0x42: # "B"
        return 1 

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''
    
    endian = get_endian(data)
    ctx = rapi.rpgCreateContext()
    parser = SanaeParser(data, endian)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class FLVER_mesh(object):
    
    def __init__(self):
        
        self.numFaceGroups = 0
        self.numIndices = []
        self.idxOffsets = []
        self.idxBuffs = [] #one mesh may have multiple parts
        self.numVerts = 0
        self.vertSize = 0
        self.vertOfs = 0
        self.vertSectionSize = 0
        self.vertBuff = bytes()

class SanaeParser(object):
    
    def __init__(self, data, endian=0):
        
        self.inFile = NoeBitStream(data, endian)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.dataOfs = 0 #offset to mesh data        
        if endian:
            rapi.rpgSetOption(noesis.RPGOPT_BIGENDIAN, 1)
        
    def build_meshes(self):
        
        rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
        for mesh in self.meshList:
            
            print(mesh.vertSize)
            if mesh.vertSize == 28:
                rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 28, 0)
            elif mesh.vertSize == 32:
                rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
                #rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 20)
                rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_HALFFLOAT, 32, 16)
            elif mesh.vertSize == 36:
                rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 36, 0)
            elif mesh.vertSize == 40:
                rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 40, 0)
            elif mesh.vertSize == 44:
                rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 44, 0)
            
            
            #for j in range(mesh.numFaceGroups): # Not sure
            for j in range(1):
                numIdx = mesh.numIndices[j]
                idxBuff = mesh.idxBuffs[j]
                rapi.rpgSetMaterial("WP_A_1550small.tga")
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE_STRIP, 1)
            #rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, mesh.numVerts, noesis.RPGEO_POINTS, 1)
                
            
    def get_indices(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)

    def parse_faces(self):
        
        for mesh in self.meshList:
            for i in range(mesh.numFaceGroups):
                numIdx = mesh.numIndices[i]
                idxOfs = mesh.idxOffsets[i]
                self.inFile.seek(idxOfs)
                idxBuff = self.get_indices(numIdx)
                mesh.idxBuffs.append(idxBuff)
                
    def parse_vertices(self):
        
        for mesh in self.meshList:
            self.inFile.seek(mesh.vertOfs)
            print(mesh.vertOfs, mesh.vertSectionSize)
            mesh.vertBuff = self.inFile.readBytes(mesh.vertSectionSize)
        
    def parse_materials(self, numMat):
        
        for i in range(numMat):
            self.inFile.read('8L')
            
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            self.inFile.seek(64, 1)
            
    def parse_unk1(self, count):
        
        for i in range(count):
            self.inFile.seek(128, 1)
            
    def parse_part_info(self, numParts):
        
        for mesh in self.meshList:    
            self.inFile.read('8L')
            numFaceGroups = self.inFile.readUInt()
            self.inFile.read('3L')
            
            mesh.numFaceGroups = numFaceGroups
            
    def parse_face_info(self):
        
        for mesh in self.meshList:
            for i in range(mesh.numFaceGroups):
                groupNum = self.inFile.readUInt()
                self.inFile.readUInt()
                numIdx = self.inFile.readUInt()
                idxOfs = self.inFile.readUInt() + self.dataOfs
                idxSize = self.inFile.readUInt()
                self.inFile.read('3L')
                
                mesh.numIndices.append(numIdx)
                mesh.idxOffsets.append(idxOfs)
                            
    def parse_vertex_info(self):
        
        for mesh in self.meshList:
            self.inFile.read('2L')
            vertSize = self.inFile.readUInt()
            numVerts = self.inFile.readUInt()
            self.inFile.readUInt()
            unk = self.inFile.readUInt()
            sectionSize = self.inFile.readUInt()
            vertOfs = self.inFile.readUInt() + self.dataOfs
            
            mesh.numVerts = numVerts
            mesh.vertSize = vertSize
            mesh.vertOfs = vertOfs
            mesh.vertSectionSize = sectionSize
            
    def parse_file(self):
        '''Main parser method'''
        
        #header
        idstring = self.inFile.readBytes(6)
        
        #version?
        unk, type1, type2 = self.inFile.read('3H')
        
        self.dataOfs = self.inFile.readUInt()
        dataSize = self.inFile.readUInt()
        numBones = self.inFile.readUInt()
        numMat = self.inFile.readUInt()
        count = self.inFile.readUInt()
        numParts = self.inFile.readUInt()
        numMesh = self.inFile.readUInt()
        
        #create some mesh objects
        for i in range(numMesh):
            mesh = FLVER_mesh()
            self.meshList.append(mesh)
        
        self.inFile.read('6f')
        self.inFile.seek(64, 1)
        self.parse_bones(numBones)
        self.parse_materials(numMat)
        self.parse_unk1(count)
        self.parse_part_info(numParts)
        self.parse_face_info()        
        self.parse_vertex_info()
        
        #parse data
        self.parse_faces()
        self.parse_vertices()
       
        self.build_meshes()