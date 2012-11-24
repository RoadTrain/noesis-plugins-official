from inc_noesis import *
import noesis
import rapi
import glob,struct



def registerNoesisTypes():
    handle = noesis.register("SUN",".wzm")
    noesis.setHandlerTypeCheck(handle,noepyCheckType)
    noesis.setHandlerLoadModel(handle,noepyLoadModel)
    return 1

def noepyCheckType(data):
    bs = NoeBitStream(data)
    if not noeStrFromBytes(bs.readBytes(4)) == "WZMD":
        print("not a wzm?")
        return 0
    return 1

def noepyLoadModel(data,mdlList):
    ctx = rapi.rpgCreateContext()
    wzm = WZM(data)
    mdl = rapi.rpgConstructModel()
    texList = []
    Bones = []
    Anims = []
    matList = wzm.matList
    Bones = rapi.multiplyBones(wzm.skeleton.Bones)
    Anims = wzm.ParseAnims()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdl.setBones(Bones)
    mdl.setAnims(Anims)
    mdlList.append(mdl)
    return 1
class WZMSkeleton:
    def __init__(self,data,version):
        self.numBones = data.readUByte()
        self.Bones    = []
        if version <= 112:
            self.mOne = data.readUByte()
        elif version <= 118:
            self.mOne = data.readUShort()
        else:
            self.mOne = []
            for i in range(self.numBones):self.mOne.append(data.readUShort())
        self.mOne1  = data.readFloat()
        parents     = []
        names       = []
        transforms  = []
        class transform:
            def __init__(self,data,version):
                if version == 119:
                    self.mUnknown  = data.readUShort()
                self.mTrans = data.read('3f')
                if version == 112:
                    x,y,z = data.read('3f')
                    RtD = noesis.g_flRadToDeg
                    self.mRot = NoeAngles((x*RtD,y*RtD,z*RtD))
                    self.mRot = self.mRot.toMat43_XYZ()
                    x,y,z,w   = self.mRot.toQuat()
                    self.mRot = NoeQuat((x,-y,z,-w))
                    
                    
                    
                else:
                    self.mRot = NoeQuat(data.read('4f'))
        for i in range(self.numBones):
            parents.append(data.readUByte())
            length = data.readUByte()
            names.append(noeStrFromBytes(data.readBytes(length)))
        if version <= 113:
            for i in range(self.numBones):
                transforms.append(transform(data,version))
        else:
            mUnknownOne = data.readUInt()
            if mUnknownOne == 1:
                if version == 118 or version == 114:
                    data.seek(4,1)
                for i in range(self.numBones):transforms.append(transform(data,version))
            elif mUnknownOne == 0:
                if version == 119 or version == 117:
                    for i in range(self.numBones):transforms.append(transform(data,118))
                else:
                    for i in range(self.numBones):transforms.append(transform(data,version))
            print(mUnknownOne)
        for i in range(self.numBones):
            if version == 112:
                rot = transforms[i].mRot.toMat43()
                #rot=rot.inverse()
                if i ==0: print(transforms[i].mRot)
            else:rot = transforms[i].mRot.toMat43()
            if version != 112:rot = rot.inverse()
            rot.__setitem__(3,transforms[i].mTrans)
            self.Bones.append(NoeBone(i,names[i],rot,None,parents[i]))
class WZMvertex112:
    def __init__(self,data):
        self.boneID  = data.readShort()
        self.vertID   = data.readUInt()
        self.normal  = data.readBytes(12)
        self.mSkin   = data.read('4b')
        self.tangent = data.readBytes(12)
        data.seek(1,1)
        self.uv      = data.readBytes(8)
class WZMvertex118:
    def __init__(self,data):
        self.boneID  = data.readShort()
        self.vertID   = data.readUInt()
        self.normal  = data.readBytes(12)
        self.mSkin   = data.read('4b'),data.read('4b')
        self.tangent = data.readBytes(12)
        data.seek(1,1)
        self.uv      = data.readBytes(8)
class WZMBoneWeight:
    def __init__(self,data):
        self.count = data.readUByte()
        self.boneID = []
        self.weight = []
        for i in range(self.count):
            self.boneID.append(data.readUByte())
            self.weight.append(data.readFloat())
class WZMsubmesh112:
    def __init__(self,data):
        self.diffuse    = noeStrFromBytes(data.readBytes(data.readUByte()))
        self.specular   = noeStrFromBytes(data.readBytes(data.readUByte()))
        self.mZero      = data.readUInt()
        self.mZeroDummy = data.readUByte()
        self.numVert    = data.readUInt()
        self.numIdx     = data.readUInt()
        self.vertBuff   = []
        for i in range(self.numVert):
            vert = WZMvertex112(data)
            self.vertBuff.append(vert)
        self.idxBuffer  = data.readBytes(self.numIdx *12)
class WZMsubmesh117:
    def __init__(self,data):
        data.seek(4,1)
        self.diffuse    = noeStrFromBytes(data.readBytes(data.readUByte()))
        self.specular   = noeStrFromBytes(data.readBytes(data.readUByte()))
        self.mZero      = data.readUInt()
        self.mZeroDummy = data.readUByte()
        self.numVert    = data.readUInt()
        self.numIdx     = data.readUInt()
        self.vertBuff   = []
        for i in range(self.numVert):
            vert = WZMvertex118(data)
            self.vertBuff.append(vert)
        self.idxBuffer  = data.readBytes(self.numIdx *12)
class WZMsubmesh118:
    def __init__(self,data):
        data.seek(4,1)
        self.diffuse    = noeStrFromBytes(data.readBytes(data.readUByte()))
        self.specular   = noeStrFromBytes(data.readBytes(data.readUByte()))
        self.mZero      = data.readUInt()
        self.mZeroDummy = data.readUByte()
        self.numVert    = data.readUInt()
        self.numIdx     = data.readUInt()
        self.vertBuff   = []
        for i in range(self.numVert):
            vert = WZMvertex118(data)
            self.vertBuff.append(vert)
        self.idxBuffer  = data.readBytes(self.numIdx *12)
        data.seek(4,1)
class WZMsubmesh120:
    def __init__(self,data):
        data.seek(4,1)
        self.diffuse    = noeStrFromBytes(data.readBytes(data.readUByte()))
        self.specular   = noeStrFromBytes(data.readBytes(data.readUByte()))
        self.mZero      = data.readUInt()
        self.mZeroDummy = data.readUByte()
        self.numVert    = data.readUInt()
        self.numIdx     = data.readUInt()
        self.vertBuff   = []
        for i in range(self.numVert):
            vert = WZMvertex118(data)
            self.vertBuff.append(vert)
        self.idxBuffer  = data.readBytes(self.numIdx *12)
        data.seek(4,1)
        
class WZMmesh112:
    def __init__(self,data,mesh):
        mesh.matList = []
        self.numPos    = data.readUInt()
        self.boneID    = b''
        self.posBuffer = []
        for i in range(self.numPos):
            self.boneID    += data.readBytes(2)
            self.posBuffer.append(data.readBytes(12))
        self.numSubMesh = data.readUByte()
        self.numVert = data.readUInt()
        self.subMesh = []
        for i in range(self.numSubMesh):
            self.subMesh.append(WZMsubmesh112(data))
class WZMmesh117:
    def __init__(self,data,mesh):
        mesh.matList = []
        self.numPos    = data.readUInt()
        self.boneID    = b''
        self.posBuffer = []
        for i in range(self.numPos):
            self.boneID    += data.readBytes(2)
            self.posBuffer.append(data.readBytes(12))
        data.seek(1,1)
        self.numSubMesh = data.readUByte()
        self.numVert = data.readUInt()
        self.subMesh = []
        for i in range(self.numSubMesh):
            self.subMesh.append(WZMsubmesh117(data))            
class WZMmesh118:
    def __init__(self,data,mesh):
        mesh.matList = []
        self.numPos    = data.readUInt()
        self.boneID    = b''
        self.posBuffer = []
        for i in range(self.numPos):
            self.boneID    += data.readBytes(2)
            self.posBuffer.append(data.readBytes(12))
        data.seek(1,1)
        self.numSubMesh = data.readUByte()
        self.numVert = data.readUInt()
        self.subMesh = []
        for i in range(self.numSubMesh):
            self.subMesh.append(WZMsubmesh118(data))
            
class WZMmesh120:
    def __init__(self,data,mesh):
        mesh.matList = []
        self.numPos    = data.readUInt()
        self.boneID    = b''
        self.posBuffer = []
        for i in range(self.numPos):
            self.boneID    += data.readBytes(2)
            self.posBuffer.append(data.readBytes(12))
        self.numSubMesh = data.readUByte()
        self.numVert = data.readUInt()
        self.subMesh = []
        for i in range(self.numSubMesh):
            self.subMesh.append(WZMsubmesh120(data))
            

class WZM:
    def __init__(self,data):
        fName=rapi.getInputName().split('\\')[-1][:-4]
        self.data       = NoeBitStream(data)
        self.magix      = noeStrFromBytes(self.data.readBytes(4))
        self.version    = self.data.readUShort()
        print("Version:",self.version)
        self.matList    = []
        if self.version != 120:
            self.padding    = self.data.readUShort()
            if self.padding >0: self.data.seek(self.padding,1)
        while  not self.data.checkEOF():
            current = self.data.tell()
            chunkID = self.data.readUShort()
            cSize   = self.data.readUInt()
            if chunkID   == 47066:
                self.skeleton = WZMSkeleton(self.data,self.version)
                if self.data.tell() != current + cSize:self.data.seek(current + cSize - self.data.tell(),1)
            elif chunkID == 47057:
                if self.version <=112:
                    print("Skeleton won't show up correctly")
                    mesh = WZMmesh112(self.data,self)
                elif self.version == 113 or self.version == 114:
                    mesh = WZMmesh112(self.data,self)
                elif self.version == 117:
                    mesh = WZMmesh117(self.data,self)
                elif self.version in [118,119]:
                    mesh = WZMmesh118(self.data,self)
                elif self.version == 120:
                    mesh = WZMmesh120(self.data,self)
                else:print("###\nUnknown mesh format\n###\nVersion: %d\n###"%self.version);self.data.seek(cSize - 6,1)
            elif chunkID == 47058:
                if cSize == 8:self.data.seek(2,1);maxWeight = 1
                else:
                    count = self.data.readUShort()
                    maxWeight = 0
                    extraWeight = []
                    for i in range(count):
                        extraWeight.append(WZMBoneWeight(self.data))
                        if extraWeight[-1].count > maxWeight:maxWeight = extraWeight[-1].count
            else:
                try:self.data.seek(cSize - 6,1)
                except:
                    print(self.data.tell(),cSize)
                    break
        for subMesh in mesh.subMesh:
            vertBuffer = b''
            for i in range(subMesh.numVert):
                vert = subMesh.vertBuff[i]
                vertBuffer += mesh.posBuffer[vert.vertID]
                vertBuffer += vert.normal
                vertBuffer += vert.tangent
                vertBuffer += vert.uv
            rapi.rpgBindPositionBufferOfs(vertBuffer, noesis.RPGEODATA_FLOAT, 44, 0)
            if self.version == 112:
                rapi.rpgSetPosScaleBias((1,-1,1),(0,0,-5))
            rapi.rpgBindNormalBufferOfs(vertBuffer, noesis.RPGEODATA_FLOAT, 44, 12)
            rapi.rpgBindTangentBufferOfs(vertBuffer, noesis.RPGEODATA_FLOAT, 44, 24)
            rapi.rpgBindUV1BufferOfs(vertBuffer, noesis.RPGEODATA_FLOAT, 44, 36)

            wB = NoeBitStream()
            weightLength = maxWeight * 6
            for i in range(subMesh.numVert):
                vert = subMesh.vertBuff[i]
                if vert.boneID >= 0:
                    wB.writeUShort(vert.boneID)
                    for n in range(maxWeight - 1):
                        wB.writeUShort(0)
                    wB.writeFloat(1)
                    for n in range(maxWeight - 1):
                        wB.writeFloat(0)
                else:
                    ID  = abs(vert.boneID)-1
                    
                    weight = extraWeight[ID]
                    for bID in weight.boneID:
                        wB.writeUShort(bID)
                    for n in range(maxWeight - len(weight.boneID)):
                        wB.writeUShort(0)
                    for bW in weight.weight:
                        wB.writeFloat(bW)
                    for n in range(maxWeight - len(weight.weight)):
                        wB.writeFloat(0)
            weightBuffer = wB.getBuffer()
            rapi.rpgBindBoneIndexBufferOfs(weightBuffer, noesis.RPGEODATA_USHORT, weightLength, 0, maxWeight)
            rapi.rpgBindBoneWeightBufferOfs(weightBuffer, noesis.RPGEODATA_FLOAT, weightLength, maxWeight*2, maxWeight)
            material = NoeMaterial(subMesh.diffuse,subMesh.diffuse)
            material.setSpecularTexture(subMesh.specular)
            self.matList.append(material)
            rapi.rpgSetMaterial(subMesh.diffuse)
            rapi.rpgSetName(fName)
            rapi.rpgCommitTriangles(subMesh.idxBuffer,noesis.RPGEODATA_UINT, subMesh.numIdx*3, noesis.RPGEO_TRIANGLE, 1)
        
    def ParseAnims(self):
        import os
        anims = []
        dirPath = rapi.getDirForFilePath(rapi.getInputName())+"/anims"
        if not os.path.isdir(dirPath):
            dirPath = rapi.getDirForFilePath(rapi.getInputName())
        os.chdir(dirPath)
        for file in os.listdir("."):
            if file.endswith(".wza"):
                animFile = NoeBitStream(open(dirPath + "/" +file,'rb').read())
                animFile.seek(4,1)
                version = animFile.readUShort()
                #print("Version:",version)
                animFile.seek(10,1)
                numBones  = animFile.readUByte()
                if version <= 112:
                    numFrames = animFile.readUByte()
                    numFramesMax = numFrames
                elif version <= 118:
                    numFrames = animFile.readUShort()
                    numFramesMax = numFrames
                else:
                    numFrames = list(animFile.read('%dh'%numBones))
                    numFramesMax = numFrames[:]
                    numFramesMax.sort()
                    if len(numFramesMax) == 0:numFramesMax = 0
                    elif len(numFramesMax)>1:numFramesMax=numFramesMax[-1]
                    
                animFile.seek(4,1)
                anim = []
                for i in range(numBones):
                    parent = animFile.readUByte()
                    length = animFile.readUByte()
                    animFile.seek(length,1)
                
                if version <=113:mUnknownOne = 0
                else:
                    mUnknownOne = animFile.readUInt()
                try:
                    if version != 119:
                        for f in range(numFrames):
                            if mUnknownOne == 1 and version > 112:
                                animFile.readUInt()
                            for i in range(numBones):
                                
                                #if version == 119: mUnknown = animFile.readUShort()
                                pos = animFile.read('3f')
                                rot = NoeQuat(animFile.read('4f'))
                                mat = rot.toMat43()
                                mat = mat.inverse()
                                mat.__setitem__(3,pos)
                                anim.append(mat)
                    else:
                        for i in range(numBones):
                            for f in range(numFrames[i]):
                                if mUnknownOne == 1:
                                    animFile.readUShort()
                                pos = animFile.read('3f')
                                rot = NoeQuat(animFile.read('4f'))
                                mat = rot.toMat43()
                                mat = mat.inverse()
                                mat.__setitem__(3,pos)
                                anim.append(mat)
                            for f in range(numFramesMax - numFrames[i]):
                                anim.append(NoeMat43())
                except:print(file);continue
                if version == 119:
                    temp = anim[:]
                    anim=[]
                    for f in range(numFramesMax):
                        
                        for b in range(numBones):
                            anim.append(temp[f + b*numFramesMax])
                animName = file.split(']',1)[-1][:-3]
                if version ==119:anims.append(NoeAnim(animName,self.skeleton.Bones,numFramesMax,anim))
                else:anims.append(NoeAnim(animName,self.skeleton.Bones,numFrames,anim))
                
        return anims
        
















