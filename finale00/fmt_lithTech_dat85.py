'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("LithTech v85 map", ".dat")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    bs = NoeBitStream(data)
    idstring = bs.readUInt()
    if idstring != 85:
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
        
        self.triCount = 0
        self.quadCount = 0
        self.numVerts = 0
        self.vertBuff = bytes()
        self.triBuff = bytes()
        self.quadBuff = bytes()

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
        
    def read_info(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)        
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUShort())
        return noeStrFromBytes(string)
    
    def build_mesh(self):
        
        for mesh in self.meshList:
        
            rapi.rpgBindPositionBuffer(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 12)
            self.plot_points(mesh.numVerts)
            rapi.rpgSetName(mesh.name)
            
            if mesh.triCount:
                rapi.rpgCommitTriangles(mesh.triBuff, noesis.RPGEODATA_UINT, mesh.triCount, noesis.RPGEO_TRIANGLE, 1)
            if mesh.quadCount:
                rapi.rpgCommitTriangles(mesh.quadBuff, noesis.RPGEODATA_UINT, mesh.quadCount, noesis.RPGEO_QUAD_ABC_ACD, 1)
        
    def parse_materials(self, numMat):
            
        for i in range(numMat):
            name = self.inFile.readString()
            #print(name)
        
    def parse_textures(self, numTex):
            
        pass    
        
    def parse_vertices(self, numVerts):
        
        return self.inFile.readBytes(numVerts*12)
    
    def parse_faces(self, faceList, mesh):
        
        triCount = 0
        quadCount = 0
        triBuff = bytes()
        quadBuff = bytes()
        for count in faceList:
            if count == 3:
                triCount += count
                matNum = self.inFile.readUInt()
                unk = self.inFile.readUInt()
                triBuff += struct.pack('3L', *self.inFile.read('3L'))
            elif count == 4:
                quadCount += count
                matNum = self.inFile.readUInt()
                unk = self.inFile.readUInt()
                quadBuff += struct.pack('4L', *self.inFile.read('4L'))
            else:
                matNum = self.inFile.readUInt()
                unk = self.inFile.readUInt()
                self.inFile.read('%dL' %count)
        
        mesh.triCount = triCount
        mesh.quadCount = quadCount
        mesh.triBuff = triBuff
        mesh.quadBuff = quadBuff
    
    def parse_meshes(self, numMesh):
        
        for i in range(numMesh):
            mesh = Mesh()
            self.inFile.read('2L')
            meshName = self.read_name()
            numVerts, unk2, unk3, unk4, numFaces, unk6, numIdx, unk8, unk9, \
                unk10 = self.inFile.read("10L")
            self.inFile.read("9f")
            
            strLen, numTex = self.inFile.read('2L')
            
            #get texture paths
            #self.inFile.seek(strLen, 1)
            self.parse_materials(numTex)

            # struct 1
            faceList = self.inFile.read('%dB' %numFaces)
            
            # unk struct2
            unkbuff = self.inFile.readBytes(unk2*16)
            
            #unk struct3
            self.inFile.readBytes(unk3*8)
            
            #faces
            self.parse_faces(faceList, mesh)

            #unk struct5
            self.inFile.readBytes(unk10*14)
            
            #vert coords struct
            vertBuff = self.parse_vertices(numVerts)

            #don't know
            self.inFile.read('2L')

            mesh.name = meshName
            mesh.numVerts = numVerts
            mesh.vertBuff = vertBuff
            self.meshList.append(mesh)
        
    def parse_file(self):
        '''Main parser method'''
        
        #header
        version = self.inFile.readUInt()
        offsets = self.inFile.read('6L')
        self.inFile.seek(32, 1)
        info = self.read_info()

        self.inFile.read('15f')
        
        self.inFile.readByte()
        count = self.inFile.readUInt()
        self.inFile.seek(3, 1)
        for i in range(count):
            self.inFile.seek(32, 1)
        self.inFile.seek(11, 1)

        #mesh section
        numMesh = self.inFile.readUInt()
        self.parse_meshes(numMesh)
        
        self.build_mesh()