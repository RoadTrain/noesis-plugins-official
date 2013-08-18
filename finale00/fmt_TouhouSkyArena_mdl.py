from inc_noesis import *
import noesis
import rapi

from Sanae3D.Sanae import SanaeObject
import os

def registerNoesisTypes():
    handle = noesis.register("Touhou Sky Arena", ".mdl")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    noesis.logPopup()
    return 1

#check if it's this type based on the data
def noepyCheckType(data):
    
    if len(data) < 23:
        return 0
    bs = NoeBitStream(data)
    try:
        header = noeStrFromBytes(bs.readBytes(23))
        if header != "MBS MODEL VER 0.01 FILE":
            return 0
        return 1
    except:
        return 0

#load the model
def noepyLoadModel(data, mdlList):
    ctx = rapi.rpgCreateContext()
    parser = TouhouSkyArena_MDL(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdlList.append(mdl)
    return 1

class TouhouSkyArena_MDL(SanaeObject):
    
    def __init__(self, data):    
        super(TouhouSkyArena_MDL, self).__init__(data)
        self.faceMats = []
      
    def read_name(self):

        return self.inFile.readString()
    
    def parse_material(self):
        
        matName = self.read_name()
        self.inFile.read('16f')
        self.inFile.read('5L')
        charLen = self.inFile.readUInt()
        texName = os.path.basename(self.read_string(charLen))
        print(texName)
        self.inFile.read('2L') #chunk, chunkSize
        
        material = NoeMaterial(matName, "")
        material.setTexture(texName)
        self.matList.append(material)
    
    def parse_vertices(self, numVerts):
        
        verts = self.inFile.readBytes(numVerts * 48)
        rapi.rpgBindPositionBufferOfs(verts, noesis.RPGEODATA_FLOAT, 48, 0)
        rapi.rpgBindNormalBufferOfs(verts, noesis.RPGEODATA_FLOAT, 48, 12)
        rapi.rpgBindUV1BufferOfs(verts, noesis.RPGEODATA_FLOAT, 48, 24)
            
    def parse_faces(self, numIdx):
        
        self.idxList = self.inFile.readBytes(numIdx * 4)
        
    def parse_face_material(self):
        
        numMat = self.inFile.readUInt()
        for i in range(numMat):
            start, count = self.inFile.read('2L')
            print(start, count)
            self.faceMats.append([start, count])
            
    def assign_face_material(self, numMat, numIdx):
        '''Have to split the idxList into separate parts, where each index
        is an integer'''
        
        for i in range(numMat):
            start = self.faceMats[i][0]
            count = self.faceMats[i][1]
            end = start*4 + count*4
            idxList = self.idxList[start*4:end]
            matName = self.matList[i].name
            rapi.rpgSetMaterial(matName)
            if count:
                rapi.rpgCommitTriangles(idxList, noesis.RPGEODATA_UINT, count, noesis.RPGEO_TRIANGLE, 1)
            
    def parse_bone(self):
        
        self.inFile.readUInt()
        self.inFile.readUInt()
        size = self.inFile.readUInt()
        self.inFile.seek(size, 1)
        #size = self.inFile.readUInt()
        #boneName = self.read_name()
        #matrix = self.inFile.read('16f')
        #matrix2 = self.inFile.read('16f')
        #self.inFile.read('6L')

    def parse_file(self):
        '''Main parser method. Can be replaced'''
        
        numBones = 0
        idstring = self.read_string(23)
        while 1:
            chunk = self.inFile.readInt()
            if chunk != -1:
                chunkSize = self.inFile.readUInt()
                if chunk == 0:
                    meshName = self.read_name()
                elif chunk == 1:
                    numVerts, unk = self.inFile.read('2L')
                    self.parse_vertices(numVerts)
                elif chunk == 2:
                    
                    numIdx = self.inFile.readUInt()
                    self.parse_faces(numIdx)
                    self.parse_face_material()
                elif chunk == 3:
                    numMat = self.inFile.readUInt()
                elif chunk == 4:
                    
                    self.parse_material()
                elif chunk == 7:
                    self.inFile.seek(chunkSize, 1)
                    numBones += 1
                    break
                elif chunk == 8:
                    
                    self.inFile.seek(chunkSize, 1)
                elif chunk == 9:
                    self.read_name()
                    self.inFile.readUInt()
                    break
                elif chunk == 0x0A:
                    break
                    #self.inFile.seek(chunkSize - 8, 1)
                else:
                    break
        
        self.assign_face_material(numMat, numIdx)
        print("%d bones" %numBones)