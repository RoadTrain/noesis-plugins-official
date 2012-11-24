'''
Created on 16-nov.-2012

@author: Andrew
Thanks MrAdults for the alpha fix an decoding normal maps. 
'''
from inc_noesis import *
import noesis
import rapi
import os

DEBUGANIM = False ### DO NOT CHANGE ###

def registerNoesisTypes():
    handle = noesis.register("Heroes of Might & Magic 6", ".gobj")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1
    
def noepyCheckType(data):
    data = NoeBitStream(data)
    magic=data.read("3I")
    noesis.logPopup()
    if magic[0] != 3992875215 or magic[2] != 1245859655:
        return 0
    return 1

def noepyLoadModel(data, mdlList):
    
    ctx = rapi.rpgCreateContext()
    global dirPath
    global fileName
    dirPath     = rapi.getDirForFilePath(rapi.getInputName())
    fileName    = rapi.getLocalFileName(rapi.getInputName()) 
    file = GOBJ(data)
    mdlList.append(file.mdl)
    rapi.rpgClearBufferBinds()
    return 1

#MrAdults - routine to copy an alpha channel from an arbitrarily-sized source texture
def copyTextureAlpha(srcTex, dstTex):
    srcRGBA = rapi.imageGetTexRGBA(srcTex)
    dstRGBA = rapi.imageGetTexRGBA(dstTex)
    for y in range(0, dstTex.height):
        for x in range(0, dstTex.width):
            fracX = x / dstTex.width
            fracY = y / dstTex.height
            sample = rapi.imageInterpolatedSample(srcRGBA, srcTex.width, srcTex.height, fracX, fracY)
            #overwrite the destination alpha
            dstRGBA[y*dstTex.width*4 + x*4 + 3] = int(sample[3]*255.0);
    #convert destination texture to the modified rgba32
    dstTex.pixelData = dstRGBA
    dstTex.pixelType = noesis.NOESISTEX_RGBA32

#MrAdults - decode normal map
def decodeHOMM6NormalMap(normTex):
    rgba = rapi.imageGetTexRGBA(normTex)
    rgba = rapi.imageNormalSwizzle(rgba, normTex.width, normTex.height, 1, 1, 0)
    normTex.pixelData = rgba
    normTex.pixelType = noesis.NOESISTEX_RGBA32

class GOBJ:
    def __init__(self,data):
        self.data=NoeBitStream(data)
        self.boneList       = []
        self.matList        = []
        self.texList        = []
        self.triList        = []
        self.animList       = []
        self.drawCallFace   = []
        self.numDrawCall    = []
        self.matID          = []
        self.vertBuff       = []
        self.idxBuff        = []
        self.numVert        = []
        self.numTri         = []
        self.boneId         = []
        
        self.parse()
        return
    
    def parse(self):
        
        self.data.seek(4,1)
        self.numModel   = self.data.readUInt()
        self.data.seek(43,0)
        self.SkipChunk()
        self.data.seek(10,1)
        self.numMesh    = self.data.readUInt()
        
        for i in range (self.numMesh):
            self.data.seek(9,1)
            self.data.readBytes(self.data.readUByte())
            self.data.seek(23,1)
            self.data.readBytes(self.data.readUByte())
            self.Vertices()
            self.Triangles()
            self.DrawCall()
            self.data.seek(5,1)
        self.BoneMap()
        self.ReadAnimations()
        self.ReadBones()
        
        self.ReadMaterials()
        
        self.CreateModel()
        
        mdl = rapi.rpgConstructModel()
        mdl.setBones(self.boneList)
        mdl.setModelMaterials(NoeModelMaterials(self.texList, self.matList))
        self.mdl = mdl
        return
    
    def Vertices(self):
        self.data.seek(30,1)
        vertBuffSize = self.data.readUInt()
        tag = self.data.read('4b')
        if tag[0] == 32:
            self.data.seek(1,1)
        self.numVert.append(vertBuffSize//64)
        self.vertBuff.append(self.data.readBytes(vertBuffSize))
        self.data.seek(1,1)
        self.boneId.append([])
        for i in range(self.numVert[-1]):
            for y in range(4):
                Id = struct.unpack_from('B',self.vertBuff[-1],64*i+44 + y)[0]
                self.boneId[-1].append(Id)
        return
    
    def Triangles(self):
        self.data.seek(10,1)
        idxBuffSize     = self.data.readUInt()
        tag             = self.data.read('4b')
        if tag[0] == 32:
            self.data.seek(1,1)
        self.numTri.append(idxBuffSize // 6)
        self.idxBuff.append(self.data.readBytes(idxBuffSize))
        self.data.seek(1,1)
        return
    
    def DrawCall(self):
        self.data.seek(10,1)
        self.numDrawCall.append(self.data.readUInt())
        self.matID.append([])
        self.drawCallFace.append([])
        for i in range(self.numDrawCall[-1]):
            self.data.seek(10,1)
            self.matID[-1].append(self.data.readUByte())
            self.data.seek(19,1)
            self.drawCallFace[-1].append(self.data.readUInt())
            self.data.seek(1,1)
        self.data.seek(1,1)
        return
    
    def BoneMap(self):
        global SKIPTOID
        SKIPTOID = True
        self.data.seek(1 + 7 + 10, 1)
        numBones = self.data.readUInt()
        self.boneID  = []
        self.boneID2 = []
        self.boneBuff= []
        for i in range(numBones):
            self.data.seek(54,1)
            self.boneID2.append(self.data.readUShort())
            self.data.seek(19,1)
        self.data.seek(1,1)
        self.SkipChunk()
        self.SkipChunk()
        self.data.seek(2,1)
        
        for n in range(self.numMesh):
            self.boneID.append([])
            for Id in self.boneId[n]:
                if Id == 255:
                    self.boneID[-1].append(255)
                else:
                    self.boneID[-1].append(self.boneID2[Id])
            self.boneBuff.append( b'')
            for Id in self.boneID[-1]:
                self.boneBuff[-1] += struct.pack('B',Id) ## change to bonemap
        return
    
    
    
    def ReadAnimations(self):
        if DEBUGANIM and not os.path.isdir(dirPath + '/anm/'):
            os.mkdir(dirPath + '/anm/')
        self.data.seek(12 + 5,1)
        anims       = []
        numAnim     = self.data.readUInt()
        for i in range(numAnim):
            self.data.seek(2,1)
            anims.append(NoeBitStream(self.data.readBytes(self.data.readUInt())))
        self.data.seek(1, 1)
        for anim in anims:
            anim.seek(3,1)
            name        = noeStrFromBytes(anim.readBytes(anim.readUByte()))
            anim.seek(3,1)
            length      = anim.readUByte() 
            if length == 1: 
                numFrames     = anim.readUByte()
            elif length == 2 : 
                numFrames     = anim.readUShort()
            else: raise
            anim.seek(3,1)
            anim.seek(anim.readUByte(),1)
            anim.seek(3,1)
            
            anim.seek(anim.readUInt(),1)
            anim.seek(10,1)
            numBones = anim.readUInt()
            anims = []
            for i in range(numBones):
                anims.append([])
                if name.lower() == 'move' and i == 9:print('%-2d: %d'%(i,anim.tell() + 978304+6))
                anim.seek(13,1)
                for t in range(8):
                    anims[-1].append([])
                    anim.seek(15,1)
                    count = anim.readUInt()
                    tempOff = anim.tell() + 978310
                    if count>0:
                        temp = anim.read('2B')
                        
                        if temp[0] == 16:
                            chunkSize = anim.readUShort()
                        else:
                            chunkSize = anim.readUByte()
                        if (chunkSize / count / 4 == 4):
                            for n in range(count):
                                try: temp = int(anim.readFloat()), anim.readFloat(),anim.readFloat(),anim.readFloat()
                                except: print((i,t,n,anim.tell()+6));raise
                                anims[-1][-1].append(temp)
                            anim.seek(2,1)
                            
                        elif (chunkSize / count /4 == 2):
                            for n in range(count):
                                
                                try: #temp = anim.readUShort(), anim.readHalfFloat(),anim.readHalfFloat(),anim.readHalfFloat()
                                    temp =  anim.readShort(),anim.readShort(),anim.readShort(),anim.readShort()
                                except: print((i,t,n,anim.tell()+6));raise
                                anims[-1][-1].append(temp)
                            
                            anim.seek(3,1)
                            anim.readBytes(anim.readUByte()+1)
                        else:pass
                    
                            
                    else:
                        temp = anim.read('2B')
                        if temp[1] != 2:
                            anim.seek(1 + anim.read('2B')[1],1)
                    if i == 9 and name.lower() == 'move':
                        try:print((chunkSize, count,chunkSize / count /4, tempOff))
                        except:print((chunkSize, count, tempOff))
                anim.seek(6,1) ## +1?
            if DEBUGANIM :
                file = open('%s_%s.anm'%(dirPath +"/anm/"+ fileName[:-5],name),'w')
                temp = ''
                i=0
                for a in anims:
                    temp+= "###############\n### Bone %d ###\n###############\n"%i
                    i+=1
                    y=0
                    for block in a:
                        temp += "\tblock: %d\n"%(y)
                        y+=1
                        for vector in block:
                            if vector !=[]:
                                try:temp+= "\t\tFrame: %-5d, vector: %f, %f, %f\n"%(vector[0],vector[1]/32767,vector[2]/32767,vector[3]/32767)
                                except:
                                    print((a.index(block),block.index(vector),vector))
                                    file.write(temp)
                                    file.close()
                                    raise
                file.write(temp)
                file.close()
            
    def ReadBones(self):
        self.SearchChunk("353020")
        self.data.seek(7,1)
        self.numBones = self.data.readUInt()
        tempBone = []
        for i in range(self.numBones):
            self.data.seek(10,1)
            x,y,z = self.data.read('3f')
            self.data.seek(12,1)
            r = self.data.read('4f')
            rotate = NoeQuat((r[0],r[1],r[2],-r[3]))
            bone = rotate.toMat43()
            bone.__setitem__(3,(x,y,z))
            tempBone.append(bone)
            self.data.seek(1,1)
        self.data.seek(15,1)
        tag = self.data.read('3b')
        if tag[0] == 16:self.data.seek(1,1)
        parent = []
        for i in range(self.numBones):
            parent.append( self.data.readShort())
        
        self.data.seek(11,1)
        nameCount = self.data.readUInt()
        if  nameCount> 0:
            boneName = 1
            boneNames = []
            for i in range(nameCount):
                self.data.seek(9,1)
                boneNames.append(noeStrFromBytes(self.data.readBytes( self.data.readUByte()))[2:])
                self.data.seek(1, 1)
        else:
            boneName = 0
        self.data.seek(2,1)
        for i in range(self.numBones):
            if boneName == 1:
                self.boneList.append(NoeBone(i,boneNames[i],tempBone[i],None,parent[i]))
            else:
                self.boneList.append(NoeBone(i,str(i),tempBone[i],None,parent[i]))
            
        self.boneList = rapi.multiplyBones(self.boneList)

    def ReadMaterials(self):
        self.SearchChunk("353010")
        self.data.seek(7,1)
        self.matEmis={}
        self.matID_F={}
        for i in range(self.data.readUInt()):
            self.data.seek(17,1)
            size        = self.data.readUInt()
            self.data.seek(2,1)
            length      = self.data.readUByte()
            nameMat     = noeStrFromBytes(self.data.readBytes(length))
            nameMat     = nameMat.split('\\')[-1]
            self.data.seek(-length-2,1)
            matbuffer   = self.data.readBytes(size)
            matbuffer   = matbuffer.split(b"\x31\x03")
            buffer      =   matbuffer[1:]
            material    = NoeMaterial(nameMat,"")
            for t in range (0,len(buffer),2):
                length  = int(buffer[t][6])
                name    = buffer[t][7:6+length]
                name    = name.split(b'/')[-1]
                name    = name[:-3]+b'dds'
                name    = name.decode("utf-8")
                if "_diff.dds" in name:
                    material.setTexture(name)
                elif "_norm.dds" in name:
                    material.setNormalTexture(name)
                elif "_spec.dds" in name:
                    material.setSpecularTexture(name)
                elif "_emis.dds" in name:
                    self.matEmis[i] = NoeMaterial(nameMat+"_Emiss", name)
                    self.matEmis[i].setBlendMode("GL_ONE","GL_ONE")
                    self.matEmis[i].setAlphaTest(0.5)
            self.matList.append(material)
        for t in self.matEmis.keys():
            self.matList.append(self.matEmis[t])
        texList = []
        for t in self.matList:
            try:
                name=rapi.getDirForFilePath(rapi.getInputName())+t.texName
                if not t.texName in texList:
                    tex = open(name,'rb').read()
                    tex = rapi.loadTexByHandler(tex,'.dds')
                    tex.name = t.texName
                    if "_diff.dds" in tex.name:
                        try:
                            norm = rapi.getDirForFilePath(rapi.getInputName())+t.nrmTexName
                            spec = rapi.getDirForFilePath(rapi.getInputName())+t.specTexName
                            norm = open(norm,'rb').read()
                            spec = open(spec,'rb').read()
                            norm = rapi.loadTexByHandler(norm,'.dds')
                            spec = rapi.loadTexByHandler(spec,'.dds')
                            norm.name = t.nrmTexName
                            spec.name = t.specTexName
                            decodeHOMM6NormalMap(norm)
                            self.texList.append(norm)
                            self.texList.append(spec)
                        except:pass
                    self.texList.append(tex)
            except:
                print("Couldn't find",t.texName)
        #MrAdults - make a list of emissive textures, find the corresponding diffuse texture, and copy its alpha over
        emissiveTexs = [t for t in self.texList if "_emis.dds" in t.name]
        for t in emissiveTexs:
            diffName = t.name.replace("_emis.dds", "_diff.dds")
            for d in self.texList:
                if d.name == diffName:
                    copyTextureAlpha(d, t)
                    break

    def CreateModel(self):
            
        
        for n in range(self.numMesh):
            rapi.rpgBindPositionBufferOfs   (self.vertBuff[n], noesis.RPGEODATA_HALFFLOAT, 64, 0)
            rapi.rpgBindUV1BufferOfs        (self.vertBuff[n], noesis.RPGEODATA_SHORT,     64, 16)
            rapi.rpgBindUV2BufferOfs        (self.vertBuff[n], noesis.RPGEODATA_SHORT,     64, 16)
            
            idxBuffer = self.idxBuff[n][:]
            for i in range(self.numDrawCall[n]):
                numDrawFace = self.drawCallFace[n][i]
                idxBuff = idxBuffer[:numDrawFace*6]
                idxBuffer=idxBuffer[numDrawFace*6:]
                rapi.rpgSetMaterial(self.matList[self.matID[n][i]].name)
                if self.matID[n][i] in self.matEmis:
                    #rapi.rpgSetLightmap(self.matEmis[self.matID[n][i]].name)
                    self.matList[self.matID[n][i]].setNextPass(self.matEmis[self.matID[n][i]])
                rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
                if SKIPTOID:
                    rapi.rpgBindBoneIndexBufferOfs(self.boneBuff[n], noesis.RPGEODATA_UBYTE, 4, 0, 4)
                else:
                    rapi.rpgBindBoneIndexBufferOfs(self.vertBuff[n], noesis.RPGEODATA_UBYTE, 64, 44, 4)
                rapi.rpgBindBoneWeightBufferOfs(self.vertBuff[n], noesis.RPGEODATA_FLOAT, 64, 28, 4)
                rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numDrawFace*3, noesis.RPGEO_TRIANGLE, 1)
    
    def SearchChunk(self,byteArray,readFlag=1):
        found = 0
        byte1 = int(byteArray[:2],16)
        type2 = len(byteArray[2:])//2
        if type2 == 2:
            byte2 = int(byteArray[4:]+byteArray[2:4],16)
        else:byte2 = int(byteArray[2:],16)
        while found!=1:
            byte = self.data.readByte()
            if byte == byte1:
                if type2 == 2:flag = self.data.readShort()
                else:flag = self.data.readByte()
                if flag ==byte2:found=1
        if readFlag == 0: self.data.seek(-3,1)
        return
    
    def SkipChunk(self):
        magix = self.data.readUByte()
        if magix == 53:
            self.data.seek(2,1)
            self.data.seek(self.data.readUInt(),1)
        elif magix == 49:
            self.data.seek(1,1)
            self.data.seek(self.data.readUInt(),1)   
