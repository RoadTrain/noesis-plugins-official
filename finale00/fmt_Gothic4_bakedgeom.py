from inc_noesis import *
import noesis
import rapi
import os

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''
    
    handle = noesis.register("Arcania", ".bakedgeom")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''
    
    if len(data) < 39:
        return 0
    bs = NoeBitStream(data)
    null = bs.readUByte()
    one = bs.readInt()
    idstring = noeStrFromBytes(bs.readBytes(bs.readUInt()))
    if idstring != "IkiResourceBakedStaticGeometry":
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

class SanaeParser(object):
    
    def __init__(self, data):    
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''
        
        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.materials = []
        
    def read_name(self):
        
        string = self.inFile.readBytes(self.inFile.readUInt())
        return noeStrFromBytes(string)
    
    def build_mesh(self, idxBuff):
        
        for matInfo in self.materials:
            one, start, count, matNum = matInfo
            end = start*2 + count*2
            idxList = idxBuff[start*2:end]
            matName = self.matList[matNum].name
            rapi.rpgSetMaterial(matName)
            rapi.rpgCommitTriangles(idxList, noesis.RPGEODATA_USHORT, count, noesis.RPGEO_TRIANGLE, 1)
    
    def parse_vertices(self, numVerts, vertType):
        
        if vertType == 1:
            vertBuff = self.inFile.readBytes(numVerts*36)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 36, 28)
        elif vertType == 9:
            vertBuff = self.inFile.readBytes(numVerts*32)
            rapi.rpgBindPositionBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
            rapi.rpgBindNormalBufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
            rapi.rpgBindUV1BufferOfs(vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
        else:
            print("unknown vert type: %d" %vertType)
            
        #flip y-z axis?
        trans = NoeMat43((NoeVec3((1, 0, 0)),
                          NoeVec3((0, 0, 1)),
                          NoeVec3((0, -1, 0)),
                          NoeVec3((0, 0, 0))))
        rapi.rpgSetTransform(trans)            
 
    def parse_faces(self, numIdx):
        
        return self.inFile.readBytes(numIdx * 2)
    
    def parse_unk(self, count):
        
        for i in range(count):
            self.inFile.read('2L')
            self.inFile.readInt()
            
    def parse_materials(self):
        
        self.inFile.readUInt()
        
        #face material assignment.
        count = self.inFile.readUInt()        
        for i in range(count):
            #unk, idxStart, idxCount, matNum
            self.materials.append(self.inFile.read('4L'))
            
        numMat = self.inFile.readUInt()
        for i in range(numMat):
            self.inFile.readUInt()
            self.read_name()
            self.read_name()            
            diffuseTex = self.read_name()
            normalTex = self.read_name()
            specularTex = self.read_name()
            self.inFile.readFloat()
            
            material = NoeMaterial("material%d" %i, "")
            material.setTexture(os.path.basename(diffuseTex))
            material.setNormalTexture(os.path.basename(normalTex))
            material.setSpecularTexture(os.path.basename(specularTex))
            self.matList.append(material)
                    
    def parse_mesh(self):
        
        #self.inFile.read('10L')
        #count = self.inFile.readUInt()
        #self.inFile.read('3L')
        #self.parse_unk(count)
        self.inFile.seek(260, 1)
        
        vertType = self.inFile.readUInt()
        numVerts = self.inFile.readUInt()
        numIdx = self.inFile.readUInt()
        print("%d verts, %d idx" %(numVerts, numIdx))
        self.inFile.read('5L')
        
        print(self.inFile.tell())
        self.parse_vertices(numVerts, vertType)
        print(self.inFile.tell())
        idxBuff = self.parse_faces(numIdx)
        self.build_mesh(idxBuff)
        
    def parse_file(self):
        '''Main parser method'''
        
        self.inFile.readByte()
        self.inFile.readInt()
        idstring = self.read_name() #IkiResourceBakedStaticGeometry
        self.parse_materials()          
        print(self.inFile.tell())
                
        self.inFile.readUShort()
        self.inFile.readInt()
        self.read_name() #IkiResourceBakedMesh
        self.parse_mesh()
        