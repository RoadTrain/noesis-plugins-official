from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Dragon Nest", ".msh")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 30:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(29))
        if idstring != "Eternity Engine Mesh File 0.1":
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

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.hasBones = True
        
    def read_name(self):
        
        return noeStrFromBytes(self.inFile.readBytes(256))
    
    def parse_bones(self, numBones):
        
        for i in range(numBones):
            boneName = self.read_name()
            matrix = self.inFile.readBytes(64)
            
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_vertices(self, numVerts):

        positions = self.inFile.readBytes(numVerts * 12)
        normals = self.inFile.readBytes(numVerts * 12)
        uv = self.inFile.readBytes(numVerts * 8)
        
        rapi.rpgBindPositionBuffer(positions, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgBindNormalBuffer(normals, noesis.RPGEODATA_FLOAT, 12)
        rapi.rpgBindUV1Buffer(uv, noesis.RPGEODATA_FLOAT, 8)        
        
        if self.hasBones:
            bones = self.inFile.readBytes(numVerts * 8) #4 shorts
            weights = self.inFile.readBytes(numVerts * 16) #4 floats
        
    def parse_unk(self, count):
        
        for i in range(count):
            self.read_name()
            
    def parse_mesh_bones(self, numBones):
        
        for i in range(numBones):
            boneName = self.read_name()
            
    def parse_mesh(self, numMesh):
        
        for i in range(numMesh):
            self.read_name() #scene root
            meshName = self.read_name()
            rapi.rpgSetName(meshName)
            numVerts, numIdx, unk = self.inFile.read('3L')
            triStrip, flag1, unk, unk = self.inFile.read('4B')
            self.inFile.seek(496, 1)
            idxBuff = self.parse_faces(numIdx)
            self.parse_vertices(numVerts)
            print(self.inFile.tell())
            if self.hasBones:
                numBones = self.inFile.readUInt()
                self.parse_mesh_bones(numBones)
    
            texName = meshName + ".dds"
            matName = "material"
            material = NoeMaterial(matName, texName)
            self.matList.append(material)
            print(self.inFile.tell())
            
            rapi.rpgSetMaterial(matName)
            if triStrip:
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE_STRIP, 1)
            else:
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
                
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.read_name()
        version, numMesh, unk1, unk2 = self.inFile.read('4L')
        self.inFile.read('6f')
        numBones = self.inFile.readUInt()
        if not numBones:
            self.hasBones = False
        self.inFile.read('2L')
        
        self.inFile.seek(716, 1)
        self.parse_bones(numBones)
        self.parse_mesh(numMesh)