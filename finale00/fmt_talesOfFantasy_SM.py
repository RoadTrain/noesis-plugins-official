from inc_noesis import *
import noesis
import rapi
from Sanae3D.Sanae import SanaeObject

def registerNoesisTypes():
    '''Register the plugin'''
    
    handle = noesis.register("Tales of Fantasy", ".sm")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    #noesis.logPopup()
    return 1

def noepyCheckType(data):
    '''Verify the file format matches this plugin. Return 1 if yes,
    0 otherwise'''
    
    return 1

def noepyLoadModel(data, mdlList):
    '''Load the model'''
    
    ctx = rapi.rpgCreateContext()
    parser = TalesOfFantasy_SM(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdlList.append(mdl)
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    return 1

class TalesOfFantasy_SM(SanaeObject):
    
    def __init__(self, data):    
        super(TalesOfFantasy_SM, self).__init__(data)
        self.meshes = []
        self.materials = []
    
    def parse_coords(self, numVerts):
        
        coords = self.inFile.readBytes(numVerts * 12)
        rapi.rpgBindPositionBuffer(coords, noesis.RPGEODATA_FLOAT, 12)
        
        trans = NoeMat43((NoeVec3((-1.0, 0.0, 0.0)),
                          NoeVec3((0.0, 0.0, 1.0)),
                          NoeVec3((0.0, 1.0, 0.0)),
                          NoeVec3((0.0, 0.0, 0.0))))
        rapi.rpgSetTransform(trans)
        
    def parse_normals(self, numNorms):
        
        normals = self.inFile.readBytes(numNorms * 12)
        rapi.rpgBindNormalBuffer(normals, noesis.RPGEODATA_FLOAT, 12)
    
    def parse_uv(self, numUV):
        
        uvs = self.inFile.readBytes(numUV * 8)
        rapi.rpgBindUV1Buffer(uvs, noesis.RPGEODATA_FLOAT, 8)
        
    def parse_unk1(self, numUnk1):
        
        self.inFile.readBytes(numUnk1 * 12)
    
    def parse_faces(self, numIdx):
        
        print(numIdx)
        idxList = self.inFile.readBytes(numIdx*2)
        rapi.rpgCommitTriangles(idxList, noesis.RPGEODATA_USHORT, numIdx, noesis.RPGEO_TRIANGLE, 1)
    
    def parse_file(self):
        '''Main parser method.'''
        
        meshName = "temp"
        rapi.rpgSetName(meshName)
        numCoords = self.inFile.readInt()
        self.parse_coords(numCoords)
        numNorms = self.inFile.readInt()
        self.parse_normals(numNorms)
        numUV = self.inFile.readUInt()
        self.parse_uv(numUV)
        numUnk1 = self.inFile.readUInt()
        self.parse_unk1(numUnk1)
        numIdx = self.inFile.readUInt()
        self.parse_faces(numIdx)