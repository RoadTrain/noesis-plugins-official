from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Loong", ".fscn")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(6), "utf-16")
    if idstring == "SCN":
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

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.idxBuffs = []
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []       
       
    def invert_faces(self):
        '''Negates the x-coord of all vertices in the mesh'''
        
        trans = NoeMat43((NoeVec3((-1, 0, 0)),
                         NoeVec3((0, 1, 0)),
                         NoeVec3((0, 0, 1)),
                         NoeVec3((0, 0, 0))))
        rapi.rpgSetTransform(trans)       
        
    def read_ustring(self, n):
            
        s = bytes()
        for i in range(n):
            s += self.inFile.readBytes(1)
            self.inFile.readBytes(1)
        return noeStrFromBytes(s)    
        
    def build_meshes(self):
        
        for i in range(len(self.idxBuffs)):
            idxBuff, numIdx = self.idxBuffs[i]
            matName = self.matList[i].name
            
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)                
        
    def parse_vertices(self, numVerts):
        
        vertBuff = self.inFile.readBytes(numVerts*40)
        rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 0)
        rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 12)
        rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 40, 32)    
    
        self.invert_faces()
        
    def parse_faces(self, numIdx):
        
        idxBuff = self.inFile.readBytes(numIdx * 2)
        self.idxBuffs.append([idxBuff, numIdx])
        
    def parse_materials(self, numMat):
            
        for i in range(numMat):
            matId = self.inFile.readUInt()
            self.inFile.read('17f')
            self.inFile.read('4b')
            texName = self.read_ustring(768)
            normName = self.read_ustring(528)
            
            matName = "material[%d]" %matId
            material = NoeMaterial(matName, texName)
            self.matList.append(material)        
    
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.read_ustring(4)
        self.inFile.readUInt()
        self.inFile.readUInt()
        numVerts, vertOfs, numFaceGroups, faceOfs, numMat, matOfs, unk1, unk2 = \
            self.inFile.read('8L')
        self.inFile.read('6f')
        self.inFile.seek(256, 1)
        self.inFile.readUInt()
        
        #vert section start
        self.parse_vertices(numVerts)
        
        #face section start
        for i in range(numFaceGroups):
            unk, matNum, unk2, unk3 = self.inFile.read('4H')
            self.inFile.read('6f')
            numIdx = self.inFile.readUInt() * 3
            self.parse_faces(numIdx)
            self.inFile.read('5L')
            
        #material section start
        self.parse_materials(numMat)
        self.build_meshes()