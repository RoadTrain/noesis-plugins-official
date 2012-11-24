from inc_noesis import *
import noesis
import rapi




def registerNoesisTypes():
    handle = noesis.register("DMC3",".mod")
    noesis.setHandlerTypeCheck(handle,noepyCheckType)
    noesis.setHandlerLoadModel(handle,noepyLoadModel)
    return 1

def noepyCheckType(data):
    bs = NoeBitStream(data)
    if not bs.readUInt() == 541347661:
        print("not a DMC3 .mod?",)
        return 0
    return 1

def noepyLoadModel(data,mdlList):
    ctx = rapi.rpgCreateContext()
    dmc3 = DMC3(data)
    mdlList.append(dmc3.mdl)
    return 1
class subMesh:
    def __init__(self,data,i):
        data.seek(2,1)
        self.numVert        = data.readUShort()
        self.ptr            = data.readUInt()
        data.seek(28,1)
        self.xyz            = data.read('3f')
        current             = data.tell()
        data.seek(self.ptr+2)
        self.headers        = data.readUShort()
        pLine = 'SubMesh: \n  numVert: %d\n  Headers: %d'%(self.numVert,self.headers)
        print(pLine)
        #if self.headers != 1:    print('Not Header 1',data.tell());data.seek(current);return
        data.seek(4,1)
        ptrs                = data.read('5I')
        
        data.seek(ptrs[0])
        rapi.rpgBindPositionBuffer(data.readBytes(self.numVert *12), noesis.RPGEODATA_FLOAT, 12)
        data.seek(ptrs[1])
        rapi.rpgBindUV1Buffer(data.readBytes(self.numVert *12), noesis.RPGEODATA_FLOAT, 12)
        data.seek(ptrs[2])
        data.seek(current)
        mat = NoeMaterial(str(i),str(i))
        rapi.rpgSetMaterial(str(i))
        rapi.rpgCommitTriangles(None,noesis.RPGEODATA_UINT, self.numVert, noesis.RPGEO_TRIANGLE_STRIP_FLIPPED, 1)
class DMC3:
    def __init__(self,data):
        self.data        = NoeBitStream(data)
        self.data.seek(16)
        self.numMesh     = self.data.readUByte()
        self.numBones    = self.data.readUByte()
        self.data.seek(10,1)
        self.bone_ptr    = self.data.readUInt()
        self.data.seek(16,1)
        print('numMesh: %d\nnumBones: %d'%(self.numMesh,self.numBones))
        for i in range(self.numMesh):sM = subMesh(self.data,i)
        self.mdl = rapi.rpgConstructModel()
