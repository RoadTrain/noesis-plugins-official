### GUILD WARS 2 FP Parser ###
"""
Version: 0.0.7
Author: forum.XeNTaX.com
"""



from inc_noesis import *
import noesis
import rapi
import glob,struct



def registerNoesisTypes():
    handle = noesis.register("GW2",".pf")
    noesis.setHandlerTypeCheck(handle,noepyCheckType)
    noesis.setHandlerLoadModel(handle,noepyLoadModel)
    return 1

def noepyCheckType(data):
    return 1

def noepyLoadModel(data,mdlList):
    ctx = rapi.rpgCreateContext()
    pfFile = PFfile(data)
    rapi.setPreviewOption('setAngOfs',"0 90 180")
    try:
        pfFile.Bones = rapi.multiplyBones(pfFile.Bones)
        mdl = rapi.rpgConstructModel()
        mdl.setModelMaterials(NoeModelMaterials(pfFile.texList, pfFile.matList))
        mdl.setBones(pfFile.Bones)
        mdlList.append(mdl)
    except:pass
    rapi.rpgClearBufferBinds()
    return 1
class DXT3Block():
    def __init__(self,data):
        self.alpha      = struct.unpack('q',data.readBytes(8))[0]
        self.color1     = [data.readBits(5),data.readBits(6),data.readBits(5)]
        self.color2     = [data.readBits(5),data.readBits(6),data.readBits(5)]
        data.seek(-4,1)
        self.color1_a   = data.readUShort()
        self.color2_a   = data.readUShort()
        self.indices    = data.readUInt()
class ANetPfChunkHeader():
    def __init__(self,data):
        self.chunkTypeInteger  = data.readUInt()
        self.chunkDataSize     = data.readUInt()
        self.chunkVersion      = data.readUShort()
        self.chunkHeaderSize   = data.readUShort()
        self.offsetTableOffset = data.readUInt()
class ANetModelMeshInfo():
    def __init__(self,data):
        self.unknown1           = data.read('5i')
        self.unknownData1Count  = data.readUInt()
        self.unknownData1Offset = data.readUInt()
        self.unknownFloats      = data.read('8f')
        self.unknownData2Count  = data.readUInt()
        self.unknownData2Offset = data.readUInt()
        self.materialIndex      = data.readInt()
        self.matpos             = data.tell()
        self.materialNameOffset = data.readUInt()
        self.unknownData3Count  = data.readUInt()
        self.unknownData3Offset = data.readUInt()
        self.pos                = data.tell()
        self.bufferInfoOffset   = data.readUInt()
class ANetModelBufferInfo():
    def __init__(self,data):
        self.vertexCount        = data.readUInt()
        self.vertexFormat       = data.readUInt()
        self.vertexBufferSize   = data.readUInt()
        self.vertexPos          = data.tell()
        self.vertexBufferOffset = data.readUInt()
        self.indexCount         = data.readUInt()
        self.indexPos           = data.tell()
        self.indexBufferOffset  = data.readUInt()
        self.lodLevelCount      = data.readUInt()
        self.lodPos             = data.tell()
        self.lodLevelOffset     = data.readUInt()
        self.boneMapCount       = data.readUInt()
        self.boneMapPos         = data.tell()
        self.boneMapOffset      = data.readUInt()
class ANetModelMaterialArray():
    def __init__(self,data):
        self.unknown1       = data.readUInt()
        self.unknown2       = data.readUInt()
        self.materialCount  = data.readUInt()
        self.matpos         = data.tell()
        self.materialOffset = data.readInt()
class ANetModelMaterialInfo():
    def __init__(self,data):
        self.unknown1           = data.read('3f')
        self.materialFilePos    = data.tell()
        self.materialFileOffset = data.readInt()
        self.flags              = data.readUInt()
        self.unknown2           = data.readUInt()
        self.textureCount       = data.readUInt()
        self.texturepos         = data.tell()
        self.textureOffset      = data.readInt()
        self.vectorCount        = data.readUInt()
        self.vectorpos          = data.tell()
        self.vectorOffset       = data.readInt()
        self.hashCount          = data.readUInt()
        self.hashpos            = data.tell()
        self.hashOffset         = data.readInt()
        self.unknown3Count      = data.readUInt()
        self.unknown3Offset     = data.readInt()
        self.unknown4Count      = data.readUInt()
        self.unknown4Offset     =data.readInt()
        self.unknwn5            = data.readUInt()
class ANetModelTextureReference():
    def __init__(self,data):
        self.referencepos           = data.tell()
        self.offsetToFileReference  = data.readInt()
        self.unknown1               = data.readUInt()
        self.hash                   = data.readUInt()
        self.unknown2               = data.readUInt()
        self.unknown3               = data.read('13b')
ANFVF_Position              = 0x00000001
ANFVF_Weights               = 0x00000002
ANFVF_Group                 = 0x00000004
ANFVF_Normal                = 0x00000008
ANFVF_Color                 = 0x00000010
ANFVF_Tangent               = 0x00000020
ANFVF_Bitangent             = 0x00000040
ANFVF_TangentFrame          = 0x00000080
ANFVF_UV32Mask              = 0x0000ff00
ANFVF_UV16Mask              = 0x00ff0000
ANFVF_Unknown1              = 0x01000000
ANFVF_Unknown2              = 0x02000000
ANFVF_Unknown3              = 0x04000000
ANFVF_Unknown4              = 0x08000000
ANFVF_PositionCompressed    = 0x10000000
ANFVF_Unknown5              = 0x20000000
class FlexibleVertex:
    def __init__(self):
        self.vertexSize         =  0
        self.position           = -1
        self.weights            = -1
        self.group              = -1
        self.normal             = -1
        self.color              = -1
        self.tangent            = -1
        self.biTangent          = -1
        self.tangentFrame       = -1
        self.uv32Mask           = -1
        self.uv32Count          =  0
        self.uv16Mask           = -1
        self.uv16Count          =  0
        self.unknown1           = -1
        self.unknown2           = -1
        self.unknown3           = -1
        self.inknown4           = -1
        self.positionCompressed = -1
        self.unknown5           = -1
class Bone:
    def __init__(self,data,index):
        current = data.tell()
        try:data.seek(current + data.readUInt())
        except:
            print(index,data.tell())
            raise
        self.name = data.readString()
        data.seek(current+4)
        self.index=index
        self.parent = data.readUInt()
        self.flag   = data.readUInt()
        self.xyz = data.read('3f')
        self.rot = data.read('4f')
        self.scaleShear = []
        for i in range(3):
            self.scaleShear.append(data.read('3f'))
        self.scaleShear.append([0,0,0])
        self.inverseWorld = []
        for i in range(4):
            self.inverseWorld.append(data.read('4f'))
        self.lodError = data.readFloat()
        data.seek(8,1)
class PFfile:
    def __init__(self,data):
        
        self.meshInfo     = []
        self.bufferInfo   = []
        self.vertexBuffer = []
        self.indexBuffer  = []
        self.matList      = []
        self.texList      = []
        self.lightMapList = {}
        
        self.data = NoeBitStream(data)
        self.findMODL()
        self.parseMaterials()
        
        self.findGEOM()
        self.header               = ANetPfChunkHeader(self.data)
        self.numMesh              = self.data.readUInt()
        if self.numMesh == 0:print("numMesh = 0, animation file")
        meshInfoOffsetTableOffset = self.data.readUInt()
        self.data.seek(meshInfoOffsetTableOffset-4,1)
        meshInfoOffsetTable       = self.data.read('%di'%self.numMesh)
        
        for i in range(self.numMesh): self.meshInfo.append(ANetModelMeshInfo(self.data))
        for mesh in self.meshInfo:
            self.data.seek(mesh.pos+mesh.bufferInfoOffset)
            self.bufferInfo.append(ANetModelBufferInfo(self.data))

            self.data.seek(mesh.matpos+mesh.materialNameOffset)
            self.bufferInfo[-1].materialName = self.data.readString()
            self.bufferInfo[-1].materialIndex= mesh.materialIndex
        for buffer in self.bufferInfo:
            
            Format = self.vertexSize(buffer)
            LOGGING = 0
            if LOGGING == 1:
                print("[*] Mesh")
                for var in vars(Format):
                    val = getattr(Format,var)
                    if val != -1:print("  %s: %d"%(var,val))

            self.data.seek(buffer.vertexPos + buffer.vertexBufferOffset)
            vertexBuffer = self.data.readBytes(buffer.vertexBufferSize)
            
            self.data.seek(buffer.indexPos + buffer.indexBufferOffset)
            indexBuffer = self.data.readBytes(buffer.indexCount*2)

            self.data.seek(buffer.boneMapPos + buffer.boneMapOffset)
            boneMap = self.data.read('%di'%buffer.boneMapCount)
            try:material = self.matList[buffer.materialIndex]
            except:
                print(buffer.materialIndex)
                raise
            material.name = buffer.materialName
            rapi.rpgSetMaterial(buffer.materialName)
            self.matList[buffer.materialIndex] = material
            if buffer.materialIndex in self.lightMapList:
                material = self.lightMapList[buffer.materialIndex]
                material.name = buffer.materialName + "_LM"
                rapi.rpgSetLightmap(material.name)
                self.matList.append(material)
            if Format.position != -1: rapi.rpgBindPositionBufferOfs(vertexBuffer, noesis.RPGEODATA_FLOAT, Format.vertexSize, Format.position)
            if Format.uv32Mask != -1: rapi.rpgBindUV1BufferOfs(vertexBuffer, noesis.RPGEODATA_FLOAT, Format.vertexSize, Format.uv32Mask)
            if Format.uv16Mask != -1:
                rapi.rpgBindUV1BufferOfs(vertexBuffer, noesis.RPGEODATA_HALFFLOAT, Format.vertexSize, Format.uv16Mask)
                if Format.uv16Count >=3: rapi.rpgBindUV2BufferOfs(vertexBuffer, noesis.RPGEODATA_HALFFLOAT, Format.vertexSize, Format.uv16Mask+8)
            rapi.rpgBindBoneIndexBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, Format.vertexSize ,Format.group, 4)
            rapi.rpgBindBoneWeightBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, Format.vertexSize, Format.weights, 4)
            rapi.rpgSetBoneMap(boneMap)
            rapi.rpgCommitTriangles(indexBuffer, noesis.RPGEODATA_USHORT, buffer.indexCount, noesis.RPGEO_TRIANGLE, 1)
        self.Bones = []
        self.ParseBones()
    def ParseBones(self):
        self.data.seek(16)
        self.data.seek(self.data.readUInt(),1)
        skel=noeStrFromBytes(self.data.readBytes(4))
        if not  skel== "SKEL": print("wrong Skeleton offset",self.data.tell());return
        self.data.seek(12,1)
        self.data.seek(self.data.readUInt()-4,1)
        if self.data.readUInt() == 0: return
        else:self.data.seek(-4,1)
        self.data.seek(self.data.readUInt()-4,1)
        self.data.seek(self.data.readUInt()-4,1)
        self.data.readString() #(merged)
        self.data.seek(7,1)
        self.numBones = self.data.readUInt()
        self.data.seek(self.data.readUInt()-4,1)
        bones = []
        for i in range(self.numBones):
            bones.append(Bone(self.data,i))
        for bone in bones:
            if "bone:" in bone.name or bone!=None:
                x,y,z,w = bone.rot
                rot     = NoeQuat((x,y,z,-w))
                mat     = rot.toMat43()
                shear   = NoeMat43(bone.scaleShear)
                mat     = mat.__mul__(shear)
                mat.__setitem__(3,bone.xyz)
                inverse = NoeMat44(bone.inverseWorld)
                #mat     = mat.toMat44()
                #mat     = mat.__mul__(inverse)
                #mat     = mat.toMat43()
                self.Bones.append(NoeBone(bone.index,bone.name,mat,None,bone.parent))
            
        
    def vertexSize(self,buffer):
        f       = buffer.vertexFormat
        vertex  = FlexibleVertex()
        current = 0
        uvIndex = 0
        if f & ANFVF_Position:
            vertex.position = current
            current += 12
        if f & ANFVF_Weights:
            vertex.weights = current
            current += 4
        if f & ANFVF_Group:
            vertex.group = current
            current +=4
        if f & ANFVF_Normal:
            vertex.normal = current
            current += 12
        if f & ANFVF_Color:
            vertex.color = current
            current += 4
        if f & ANFVF_Tangent:
            vertex.tangent = current
            current += 12
        if f & ANFVF_Bitangent:
            vertex.biTangent = current
            current += 12
        if f & ANFVF_TangentFrame:
            vertex.tangentFrame = current
            current += 12
        if ((f& ANFVF_UV32Mask)>>8) != 0:
            uvFlag = (f& ANFVF_UV16Mask)>>8
            vertex.uv32Mask = current
            for i in range(7):
                if (((uvFlag >> i) & 1) == 0): pass
                else: current+= 8;vertex.uv32Count+=1
        if ((f& ANFVF_UV16Mask)>>16) != 0:
            uvFlag = (f& ANFVF_UV16Mask)>>16
            vertex.uv16Mask = current
            for i in range(7):
                if (((uvFlag >> i) & 1) == 0): pass
                else: current+= 4;vertex.uv16Count+=1
            #current += 4
        if f & ANFVF_Unknown1:
            current += 48
        if f & ANFVF_Unknown2:
            current += 4
        if f & ANFVF_Unknown3:
            current += 4
        if f & ANFVF_Unknown4:
            current += 16
        if f & ANFVF_PositionCompressed:
            print("fix this")
            current += 6
        if f & ANFVF_Unknown5:
            current += 12
        vertex.vertexSize = current
        return vertex
    def parseMaterials(self):
        dirPath = rapi.getDirForFilePath(rapi.getInputName())
        self.data.seek(28)
        self.numMat = self.data.readUInt()
        matOffset =self.data.readUInt()
        self.data.seek(matOffset-4,1)
        materialArray = ANetModelMaterialArray(self.data)
        self.data.seek(materialArray.materialOffset-4,1)
        current = self.data.tell()
        offsetTable = self.data.read("%di"%materialArray.materialCount)
        diffuse  = [0x67531924]
        normal   = [2332802439,2774157488]
        lightmap = [1745599879,]
        for i in range(materialArray.materialCount):
            self.data.seek(current + offsetTable[i] + i*4)
            matInfo = ANetModelMaterialInfo(self.data)
            self.data.seek(matInfo.texturepos + matInfo.textureOffset)
            material = NoeMaterial(str(i),'')
            #material.setBlendMode("GL_SRC_COLOR","GL_ONE")
            
            texInfos = []
            for t in range(matInfo.textureCount):texInfos.append(ANetModelTextureReference(self.data))
            
            for texInfo in texInfos:
                self.data.seek(texInfo.referencepos + texInfo.offsetToFileReference)
                texInDAT = self.data.read('3H')
                if texInfo.hash in diffuse or texInfo.hash in normal or texInfo.hash in lightmap:
                    texture = 0xFF00 * (texInDAT[1] - 0x100) + (texInDAT[0] - 0x100) + 1
                    if texInfo.hash in diffuse:  material.setTexture(str(texture))
                    elif texInfo.hash in normal: material.setNormalTexture(str(texture))
                    elif texInfo.hash in lightmap:
                        self.lightMapList[i]=NoeMaterial(str(i),"")
                        self.lightMapList[i].setTexture(str(texture))
                        self.lightMapList[i].setBlendMode("GL_ONE","GL_ONE")
                    try:
                        path = glob.glob(dirPath+str(texture)+'*.atex')[0]
                        tex=open(path,'rb').read()
                        tex=rapi.loadTexByHandler(tex,'.atex')
                        tex.name=str(texture)+'.atex'
                        self.texList.append(tex)
                    except:print("Can't load", texture)
                else:
                    texture = 0xFF00 * (texInDAT[1] - 0x100) + (texInDAT[0] - 0x100) + 1
                    #print(texture, texInfo.hash)
            self.matList.append(material)
            
    def findGEOM(self):
        fName=rapi.getInputName().split('\\')[-1]
        dirPath = rapi.getDirForFilePath(rapi.getInputName())
        f = open(dirPath + "/" + fName,'rb')
        file = f.read()
        f.close()
        offset = file.find(b"GEOM")
        self.data.seek(offset)
    def findMODL(self):
        fName=rapi.getInputName().split('\\')[-1]
        dirPath = rapi.getDirForFilePath(rapi.getInputName())
        f = open(dirPath + "/" + fName,'rb')
        file = f.read()
        f.close()
        offset = file.find(b"MODL")
        self.data.seek(offset)
        
    
    
