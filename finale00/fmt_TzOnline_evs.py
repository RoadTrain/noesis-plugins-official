'''Noesis import plugin. Written by Tsukihime

Note that this game is published under the names
-Talisman Online
-Weapons of War Online
-TZ Online'''

from inc_noesis import *
import noesis
import rapi


def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Tz Online", ".evs")
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
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []
        self.filename = rapi.getLocalFileName(rapi.getInputName())
        
    def build_mesh(self):
        
        for mesh in self.meshList:
            
            rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 28, 0)
            rapi.rpgCommitTriangles(None, noesis.RPGEODATA_UINT, mesh.numVerts, noesis.RPGEO_POINTS, 1)
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
    
    def parse_material(self, matNum):
        
        idstring = self.inFile.readBytes(21)
        self.inFile.readByte() # 1
        matName = self.read_name()
        print(matName)
        self.inFile.readByte() # 1
        self.read_name()
        self.inFile.readUInt()
        lightmap = self.read_name()
        self.inFile.readBytes(3)
        
        # light properties
        self.inFile.read('48f')
        self.inFile.readByte() # 1
        
        # unk
        self.inFile.readBytes(19)
        self.read_name()
        self.read_name()
        self.read_name()
        self.inFile.readByte() # 0
        self.inFile.read('2L')
        self.read_name()
        self.inFile.readByte() # 0
        self.inFile.read('3L')
        self.read_name()
        self.read_name()
        self.inFile.seek(18, 1)
        self.inFile.readByte() # 1

    def parse_material_library(self):
        
        matIDstring = self.inFile.readBytes(21)
        self.inFile.readByte()
        numMat = self.inFile.readUInt()
        for i in range(numMat):
            self.parse_material(i)
        
    def parse_vertices(self, numVerts, mesh):
        
        vertBuff = bytes()
        totalVerts = 0
        print("read %d verts" %numVerts)
        for i in range(numVerts):
            if totalVerts == numVerts - 100:
                break
            self.inFile.readBytes(12)
            count = self.inFile.readUInt()
            for j in range(count):
                self.inFile.readByte()
                verts = self.inFile.readBytes(28)
                self.inFile.readByte() # 1
                totalVerts += 1
            self.inFile.read('2f')
            self.inFile.readByte() # 1
            
            vertBuff = b''.join([vertBuff, verts])
            
        mesh.numVerts = totalVerts
        mesh.vertBuff = vertBuff
    
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx*2)
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.inFile.readBytes(18)
        self.inFile.readByte()
        modelName = self.read_name()
        self.inFile.readByte()
        
        mesh = Mesh()
        faceGroups = self.inFile.readUInt()
        for i in range(faceGroups):
            groupName = self.read_name()
            matName = self.read_name()
            print(groupName, matName)
        
            numIdx = self.inFile.readUInt()
            self.parse_faces(numIdx)
            self.inFile.readByte()
            
        self.parse_material_library()
        
        self.inFile.read('2L')
        self.inFile.readByte()
        numVerts = self.inFile.readUInt()
        self.inFile.readUInt() #?
        self.parse_vertices(numVerts, mesh)
        self.inFile.readByte()
        
        self.meshList.append(mesh)
        self.build_mesh()