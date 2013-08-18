from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Loong", ".fak")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 4:
        return 0
    try:
        bs = NoeBitStream(data)
        idstring = noeStrFromBytes(bs.readBytes(8), 'utf-16')
        if idstring == "AKK":
            return 1
        return 0
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
        self.vertBuffs = []
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
            idxBuff, numIdx, matNum = self.idxBuffs[i]
            vertBuff, vertType = self.vertBuffs[i]
            if matNum != -1:
                matName = self.matList[matNum].name
                rapi.rpgSetMaterial(matName)
            
            if vertType == 0.125:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 16, 0)
                rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 16, 6)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 16, 12)
                
            elif vertType in [0.0333, 0.0335]:
                rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 22, 0)
                rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 22, 6)
                rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_HALFFLOAT, 22, 18)
            
            rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
            
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)    
            
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
    
    def parse_faces(self, numIdx, matNum):
        
        idxBuff = self.inFile.readBytes(numIdx * 2)
        self.idxBuffs.append([idxBuff, numIdx, matNum])
    
    def parse_vertices(self, numVerts, vertType, vertGroups):
        
        print(vertType)
        for vertCount in vertGroups:
            if vertType == 0.125:
                vertBuff = self.inFile.readBytes(vertCount*16)
            elif vertType in [0.0333, 0.0335]:
                vertBuff = self.inFile.readBytes(vertCount*22)
            self.vertBuffs.append([vertBuff, vertType])
        
    def parse_file(self):
        '''Main parser method'''
        
        idstring = self.read_ustring(4)
        self.inFile.readUInt()
        vertType, numVerts, numFaceGroups, faceOfs, numMat, matOfs, numVertGroups, vertOfs = \
            self.inFile.read('8L')
        
        self.inFile.read('6f')
        self.inFile.seek(256, 1)
        
        #face section start
        vertGroups = []
        for i in range(numFaceGroups):
            vertStart = self.inFile.readUInt()
            matNum = self.inFile.readShort()
            vertCount = self.inFile.readUShort()
            self.inFile.read('6f')
        
            numIdx = self.inFile.readUInt() * 3
            self.parse_faces(numIdx, matNum)
            self.inFile.read('5L')
            
            vertGroups.append(vertCount)
        
        #vert section start
        idstring = self.inFile.readBytes(4)
        vertType = round(self.inFile.readFloat(), 4)
        count = self.inFile.readUInt()
        self.inFile.seek(count, 1)
        size = self.inFile.readUInt()
        self.parse_vertices(numVerts, vertType, vertGroups)
        
        #skip rest of data, go straight to materials
        
        self.inFile.seek(matOfs)
        self.parse_materials(numMat)
            
        self.build_meshes()