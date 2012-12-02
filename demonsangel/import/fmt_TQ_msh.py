
from inc_noesis import *
import noesis
import rapi
import os
########################################################################################################################
########################################################################################################################
'''

IMPORTANT: MODPATH:
    None = Textures in same folder as model!
    MODPATH = r'C:\games\TQ\mod' -> link to 'creatures' folder
    for example you load C:\games\TQ\mod\Creatures\PC\Male\MalePC01 set MODPATH to r'C:\games\TQ\mod'

'''
#MODPATH = None
MODPATH = r'E:\games\THQ\Titan Quest Immortal Throne\extracted'
########################################################################################################################
########################################################################################################################



def registerNoesisTypes():
    handle = noesis.register("TitanQuest Model", ".msh")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    
    handle = noesis.register("TitanQuest Texture", ".tex")
    noesis.setHandlerTypeCheck(handle, noepyCheckTex)
    noesis.setHandlerLoadRGBA(handle, noepyLoadRGBA)
    
    handle = noesis.registerTool("&TitanQuest merger", mergeToolMethod)
    return 1
    
def noepyCheckType(data):
    data = NoeBitStream(data)
    mesh=data.readUInt()
    if mesh != 172512077 and mesh != 189289293:
        print ("Not TQ .msh")
        return 0
    return 1
def noepyCheckTex(data):
    return 1
def noepyLoadModel(data, mdlList):
    ctx = rapi.rpgCreateContext()
    #noesis.logPopup()
    file = MSH(data)
    mdlList.append(file.mdl)
    rapi.rpgClearBufferBinds()
    return 1

def LoadTexture(texName, file):
    
    if MODPATH != None:
        name = MODPATH +'\\'+ texName
    else:
        name = rapi.getDirForFilePath(rapi.getInputName()) + texName.split('\\')[-1]
        print(rapi.getDirForFilePath(rapi.getInputName()))
    if not rapi.checkFileExists(name):
        print("Texture not found: %s" %name)
        
    else:
        
        tex = open(name,'rb').read()
        noepyLoadRGBA(tex,file.texList)
        file.texList[-1].name = name
        
        return file.texList[-1]

class MSH:
    def __init__(self,data):
        self.data = NoeBitStream(data)
        self.boneList   = []
        self.animList   = []
        self.matList    = []
        self.texList    = []
        
        self.SECTION    = {0 : self.Material,
                           4 : self.Vertex,
                           5 : self.Triangle,
                           6 : self.Bones,
                           7 : self.Textures,
                           10: self.Extends,
                           99: self.SkipChunk}
        self.vertOrder  = {0 : 12,
                           1 : 12,
                           2 : 12,
                           3 : 12,
                           4 : 8,
                           5 : 16,
                           6 : 4,
                           14: 4}   
        
        self.__parse__()
        return
    
    def __parse__(self):
        self.magic = self.data.read('4B')
        while not self.data.checkEOF():
            section = self.data.readUInt()
            if not section in self.SECTION:
                self.SECTION[99]()
            else:
                self.SECTION[section]()
            
        self.mdl = rapi.rpgConstructModel()
        self.mdl.setModelMaterials(NoeModelMaterials(self.texList, self.matList))
        self.mdl.setBones(self.boneList)
        #self.Animations()
        #self.mdl.setAnims(self.Animations())
        return
    
    def Material(self):
        self.data.seek(4,1)
        self.mif = noeStrFromBytes(self.data.readBytes(self.data.readUInt())) 
        return
    
    def Vertex(self):
        self.data.seek(4,1)
        numOrder    = self.data.readUInt()
        self.vertLength = vertLength  = self.data.readUInt()
        self.numVert = numVert     = self.data.readUInt()
        Order       = self.data.read('%sI'%numOrder)
        self.vertBuff = vertBuff    = self.data.readBytes(vertLength * numVert)
        offset      = 0
        for o in Order:
            if o == 0:
                vertOffset = offset
                offset += self.vertOrder[o]
            elif o == 4:
                uvOffset = offset
                offset += self.vertOrder[o]
            elif o == 1:
                normalOffset = offset
                offset += self.vertOrder[o]
            elif o == 5:
                self.boneWeightOffset = offset
                offset += self.vertOrder[o]
            elif o == 6:
                self.boneIndexOffset = offset
                offset += self.vertOrder[o]
            else:
                offset += self.vertOrder[o]
                
        rapi.rpgBindPositionBufferOfs   (vertBuff, noesis.RPGEODATA_FLOAT, vertLength, vertOffset)
        rapi.rpgBindUV1BufferOfs        (vertBuff, noesis.RPGEODATA_FLOAT, vertLength, uvOffset)
        rapi.rpgBindNormalBufferOfs     (vertBuff, noesis.RPGEODATA_FLOAT, vertLength, normalOffset)
        
        return
    
    def Triangle(self):
        self.data.seek(4,1)
        self.numTri         = self.data.readUInt()
        self.numDrawCall    = self.data.readUInt()
        self.idxBuffer      = self.data.readBytes(self.numTri * 6)
        self.drawCallInfo   = []
        drawCallIndex       = []
        
        for i in range( self.numDrawCall):
            drawCallIndex = []
            shader, startFace, faceCount, word = self.data.read('4I')
            if self.magic[3] == 10:
                for n in range(word):
                    drawCallIndex.append( self.data.readUInt())
            elif self.magic[3] == 11:
                self.data.read('6f')
                for n in range( self.data.readUInt()):
                    drawCallIndex.append( self.data.readUInt())
            self.drawCallInfo.append({'matID' : shader, 'faceStart' : startFace, 'faceCount' : faceCount, 'boneMap':drawCallIndex})
        return
    
    def Bonees(self):
        self.data.seek(4,1)
        numBones    = self.data.readUInt()
        self.bones  = []
        for i in range( numBones):
            bone = {'name' : noeStrFromBytes(self.data.readBytes(32))}
            bone['index']       = i
            bone['child']       = self.data.readUInt()
            bone['numChild']    = self.data.readUInt()
            bone['matrix']      = NoeMat43.fromBytes(self.data.readBytes(48))
            self.bones.append(bone)
        
        for bone in self.bones:
            for i in range( bone['numChild']):
                child = bone['child'] + i
                self.bones[child]['parent'] = bone['index']
        
        for bone in self.bones:
            if not 'parent' in bone:
                bone['parent'] = -1
            else:
                matrix = bone['matrix']
                parent = self.bones[ bone['parent']]['matrix']
                bone['matrix'] = matrix.__mul__(parent)
                #bone['matrix'] = bone['matrix'].inverse()
                m = bone['matrix'].mat43
            self.boneList.append(NoeBone(bone['index'],
                                         bone['name'],
                                         bone['matrix'],
                                         None,
                                         bone['parent']))
        
        #self.boneList = rapi.multiplyBones(self.boneList)
        return
    def Bones(self):
        self.data.seek(4,1)
        numBones    = self.data.readUInt()
        self.bones  = []
        
        for i in range( numBones):
            bone = {'name' : noeStrFromBytes(self.data.readBytes(32))}
            bone['index']       = i
            bone['child']       = self.data.readUInt()
            bone['numChild']    = self.data.readUInt()
            boneBuff=self.data.readBytes(48)
            
            (a1,a2,a3),(a4,a5,a6),(a7,a8,a9),(x,y,z) = NoeMat43.fromBytes(boneBuff)
            
            tupl=(a1,a2,a3,0),(a4,a5,a6,0),(a7,a8,a9,0),(x,y,z,1)
            
            bone['matrix'] = NoeMat44(tupl)
            self.bones.append(bone)
        for bone in self.bones:
            for i in range( bone['numChild']):
                child = bone['child'] + i
                self.bones[child]['parent'] = bone['index']
                
        for bone in self.bones:
            if not 'parent' in bone:
                bone['parent'] = -1
            else:
                matrix = bone['matrix']
                parent = self.bones[ bone['parent']]['matrix']
                bone['matrix'] = matrix.__mul__(parent)
                m = bone['matrix'].mat44
        for bone in self.bones:
            m = bone['matrix'].mat44
            k=[0,0,0,0]
            for t in range(len(m)):
                k[t] = NoeVec3(m[t][:-1])
            bone['matrix'] = NoeMat43(list(k))
            self.boneList.append(NoeBone(bone['index'],
                                         bone['name'],
                                         bone['matrix'],
                                         None,
                                         bone['parent']))
        
        return
    def Textures(self):
        self.data.seek(4,1)
        numShader = self.data.readUInt()
        for i in range( numShader):
            name    = noeStrFromBytes(self.data.readBytes(self.data.readUInt()))
            numTex  = self.data.readUInt()
            material = NoeMaterial(name, "")
            for n in range( numTex):
                typeName    = noeStrFromBytes(self.data.readBytes(self.data.readUInt()))
                typeID      = self.data.readUInt()
                if typeID ==7: #BaseTexture, Bump
                    if MODPATH == None:texName = noeStrFromBytes(self.data.readBytes(self.data.readUInt())).split('\\')[-1]
                    else: texName = noeStrFromBytes(self.data.readBytes(self.data.readUInt()))
                    if typeName == 'baseTexture':
                        tex = LoadTexture(texName, self)
                        if tex != None: material.setTexture(tex.name)
                    elif typeName == 'bumpTexture':
                        tex = LoadTexture(texName, self)
                        if tex != None: material.setNormalTexture(tex.name)
                        
                elif typeID ==8:
                    self.data.read('2f')
                elif typeID ==9: #Color (specular, ..)
                    temp = self.data.read('3f')
                    if typeName == 'specularColor':
                        material.setSpecularColor((temp[0], temp[1], temp[2], 8.0))
                        
                elif typeID ==10: #Power, Effects, ...
                    self.data.read('f')
            self.matList.append(material)
            
        for draw in self.drawCallInfo:
            idxBuff = self.idxBuffer[ draw['faceStart'] * 6 : ]
            numIdx  = draw['faceCount']
            rapi.rpgSetMaterial(self.matList[draw['matID']].name)
            if len(self.boneList) >0:
                    rapi.rpgSetBoneMap( draw['boneMap'])
                    rapi.rpgBindBoneIndexBufferOfs  (self.vertBuff, noesis.RPGEODATA_UBYTE, self.vertLength, self.boneIndexOffset, 4)
                    rapi.rpgBindBoneWeightBufferOfs (self.vertBuff, noesis.RPGEODATA_FLOAT, self.vertLength, self.boneWeightOffset, 4)
            rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
            rapi.rpgCommitTriangles(idxBuff, noesis.RPGEODATA_USHORT, numIdx*3, noesis.RPGEO_TRIANGLE, 1)
            
        return
    def Extends(self):
        self.data.seek(28,1)
        
    def SkipChunk(self):
        self.data.seek( self.data.readUInt(), 1)
        
    def Animations(self):
        dirPath     = rapi.getDirForFilePath(rapi.getInputName())
        animFile    = open(dirPath+"/anm/jackalman_walk.anm","rb").read()
        animFile    = NoeBitStream(animFile)
        animFile.seek(4)
        numBones    = animFile.readUInt()
        numFrames   = animFile.readUInt()
        FPS         = animFile.readUInt()
        
        animation = []
        for i in range(numBones):
            name    = noeStrFromBytes( animFile.readBytes( animFile.readUInt()))
            anim = []
            
            for t in range(numFrames):
                pos =x,y,z = animFile.read("3f")
                rot = animFile.read("4f")
                #rot = (rot[0],rot[1],rot[2],-rot[3])
                scale = animFile.read("3f")
                rot2 = animFile.read("4f")
                
                matrix = NoeQuat(rot).toMat43()
                matrix.__setitem__(3,(pos))
                if i == 1 and t == 0: 
                    for m in matrix:print("%6f, %6f, %6f"%(m[0],m[1],m[2]))
                anim.append(matrix)
            animation.append(anim)
        for i in range(numBones):
            for t in range(numFrames):
                if t==0 or t>0 :
                    bone = self.boneList[i]._matrix
                    #animation[i][t] = bone.__mul__(animation[i][t])
                    #animation[i][t] = animation[i][t].__mul__(bone)
                    
                    
                else:
                    pass
        frameMat=[]
        for t in range(numFrames):
            for i in range(numBones):
                frameMat.append(animation[i][t])
        return (NoeAnim("walk", self.boneList, 1, frameMat, 1),)
        return (NoeAnim("walk", self.boneList, numFrames, frameMat, 1),)
        return

#######################################################################################################################
#######################################################################################################################
#######################################################################################################################
"""TEXTURE"""
#######################################################################################################################
#######################################################################################################################
#######################################################################################################################
"""FLAGS"""
###CAPS2###
Cubemap = 0x200 
CubemapPositiveX = 0x400  
CubemapNegativeX = 0x800   
CubemapPositiveY = 0x1000  
CubemapNegativeY = 0x2000  
CubemapPositiveZ = 0x4000  
CubemapNegativeZ = 0x8000  
Volume = 0x200000 
###CAPS###
Complex = 0x8
Mipmap = 0x400000 
Texture = 0x1000
###HEADER###
Caps = 0x1            
Height = 0x2          
Width = 0x4           
Pitch = 0x8           
PixelFormat = 0x1000  
MipmapCount = 0x20000 
LinearSize =  0x80000 
Depth =       0x800000
###PIXEL###
AlphaPixels = 0x1
Alpha = 0x2
fourCC = 0x4
PaletteIndexed8 = 0x20
RGB = 0x40
YUV = 0x200
Luminance = 0x20000
###VARIANT###
Reversed = 0x52
Default = 0x20


def noepyLoadRGBA(data,texList):
    noesis.logPopup()
    file = TEX(data)
    if file.header['version'] == Reversed:
        q=file.WriteFixedDDS()
        q=q.getBuffer()
    else:
        Data = NoeBitStream(data)
        Data.readBytes(12)
        q=Data.getBuffer()
        q=q[12:]
    tex = rapi.loadTexByHandler(q, '.dds')
    if tex: texList.append(tex)
    return 1


class TEX:
    def __init__(self, data):
        self.data = NoeBitStream(data)
        self.data.seek(12,1)
        self.header = self.HEADER()
        self.Images,self.Layers = self.ParseMipMaps()
        self.FixHeader()
        
        return
    
    def HEADER(self):
        header = {}
        header['magic']         = noeStrFromBytes(self.data.readBytes(3))
        header['version']       = self.data.readUByte()
        header['defaultSize']   = self.data.readUInt()
        if header['defaultSize'] != 124:
            raise ValueError("HeaderDS != 124")
        header['flags']         = self.data.readUInt()
        header['height']        = self.data.readUInt()
        header['width']         = self.data.readUInt()
        header['linearSize']    = self.data.readUInt()
        header['depth']         = self.data.readUInt()
        header['mipmapCount']   = self.data.readUInt()
        header['reserved1']     = self.data.read('11I')
        header['pixelFormat']   = self.PixelFormat()
        header['caps1']         = self.data.readUInt()
        header['caps2']         = self.data.readUInt()
        header['caps3']         = self.data.readUInt()
        header['caps4']         = self.data.readUInt()
        header['reserved2']     = self.data.readUInt()
        return header

    def PixelFormat(self):
        pf = {}
        pf['defaultSize'] = self.data.readUInt()
        if pf['defaultSize'] != 32:
            raise ValueError("DS != 32")
        pf['flags'] = self.data.readUInt()
        pf['fourCC'] = noeStrFromBytes(self.data.readBytes(4))
        pf['RGBBitCount'] = self.data.readUInt()
        pf['RBitMask'] = self.data.readUInt()
        pf['GBitMask'] = self.data.readUInt()
        pf['BBitMask'] = self.data.readUInt()
        pf['ABitMask'] = self.data.readUInt()
        return pf
    
    def ParseMipMaps(self):
        layers = 1
        if self.header['caps1'] & Cubemap:
            layers = 0
            if self.header['caps2'] & CubemapPositiveX: layers +=1
            if self.header['caps2'] & CubemapNegativeX: layers +=1
            if self.header['caps2'] & CubemapPositiveY: layers +=1
            if self.header['caps2'] & CubemapNegativeY: layers +=1
            if self.header['caps2'] & CubemapPositiveZ: layers +=1
            if self.header['caps2'] & CubemapNegativeZ: layers +=1
            
        mipCount = self.header['mipmapCount']
        if mipCount ==0 and (self.header['flags'] & MipmapCount):
            mipCount = 1
        
        lengths = []
        mips    = []
        for i in range(mipCount):
            height = self.header['height']
            width  = self.header['width']
            
            for t in range(i):
                width   = width//2
                height  = height //2
                
            if height <1: height = 1
            if width  <1: width  = 1
            
            if "DXT" in self.header['pixelFormat']['fourCC']:
                if width %4 != 0:
                    width +=4 - (width%4)
                    
                if height %4 != 0:
                    height +=4 -(height%4)
                    
                if self.header['pixelFormat']['fourCC'] == "DXT1":
                    lengths.append(width*height//2)
                else:
                    lengths.append(width*height)
            
            elif self.header['pixelFormat']['RGBBitCount'] != 0:
                lengths.append(width * height * self.header['pixelFormat']['RGBBitCount'])
                if lengths[i] //8 != 0:
                    lengths[i] += 8 - (lengths[i] // 8)
                lengths[i] = lengths[i] // 8
                
        if self.header['version'] == Reversed:
            lengths.reverse()
        # print(lengths)
        for i in range(layers):
            mips.append([])
            # mips[i] = []
            for t in range(mipCount):
                
                mips[i].append(self.data.readBytes(lengths[t]))
        #print(len(mips[0][10]))
        return mips,layers
    
    def Reverse(self,array):
        if self.header['version'] == Reversed:
            self.header['version'] = Default
            return
        elif self.header['version'] == Default:
            self.header['version'] = Reversed
            return

    def FixHeader(self):
        self.header['flags']  |= Caps | Height | Width | PixelFormat
        self.header['caps1']  |= Texture
        self.header['mipmapCount'] = len(self.Images[0])
        
        if self.header['mipmapCount'] >1:
            self.header['flags'] |= MipmapCount
            self.header['caps1'] |= Complex | Mipmap
            
        if self.header['caps2'] & Cubemap:
            self.header['caps1'] |= Complex
            
        if self.header['depth'] >1:
            self.header['caps1'] |= Complex
            self.header['flags'] |= Depth
            
        if (self.header['pixelFormat']['flags'] & fourCC) and self.header['linearSize'] != 0:
            self.header['flags'] |= LinearSize
            
        if (self.header['pixelFormat']['flags'] & RGB or self.header['pixelFormat']['flags'] & YUV or self.header['pixelFormat']['flags'] & Luminance or self.header['pixelFormat']['flags'] & Alpha) and self.header['linearSize'] !=0:
            self.header.Flags |= Pitch
            
        if self.header['pixelFormat']['flags'] & RGB and (self.header['pixelFormat']['RBitMask'] +self.header['pixelFormat']['GBitMask'] +self.header['pixelFormat']['GBitMask'] ==0):
            self.header['pixelFormat']['RBitMask'] = 0xff0000
            self.header['pixelFormat']['GBitMask'] = 0x00ff00
            self.header['pixelFormat']['BBitMask'] = 0x0000ff

    def WriteFixedDDS(self):
        file=NoeBitStream()
        file.writeBytes(b"\x44\x44\x53\x20")
        file.writeBytes(noePack("<1i",self.header['defaultSize']))
        file.writeBytes(noePack("<1i",self.header['flags']))
        file.writeBytes(noePack("<1i",self.header['height']))
        file.writeBytes(noePack("<1i",self.header['width']))
        file.writeBytes(noePack("<1i",self.header['linearSize']))
        file.writeBytes(noePack("<1i",self.header['depth']))
        file.writeBytes(noePack("<1i",self.header['mipmapCount']))
        file.writeBytes(noePack("<11i",*self.header['reserved1']))
        file.writeBytes(noePack("<1i",self.header['pixelFormat']['defaultSize']))
        file.writeBytes(noePack("<1i",self.header['pixelFormat']['flags']))
        if "DXT" in self.header['pixelFormat']['fourCC']:
            file.writeBytes(b"\x44\x58\x54") #write "DXT"
            file.writeBytes(struct.pack('b',48+int(self.header['pixelFormat']['fourCC'][-1]))) #write 1-5
        else:
            file.writeBytes(b"\x00\x00\x00\x00")
        file.writeBytes(noePack("<1i",self.header['pixelFormat']['RGBBitCount']))
        file.writeBytes(noePack("<1i",self.header['pixelFormat']['RBitMask']))
        file.writeBytes(noePack("<1i",self.header['pixelFormat']['GBitMask']))
        file.writeBytes(noePack("<1i",self.header['pixelFormat']['BBitMask']))
        try:file.writeBytes(noePack("<1i",self.header['pixelFormat']['ABitMask']))
        except: file.writeBytes(b"\x00\x00\x00\xFF")
        file.writeBytes(noePack("<1i",self.header['caps1']))
        file.writeBytes(noePack("<1i",self.header['caps2']))
        file.writeBytes(noePack("<1i",self.header['caps3']))
        file.writeBytes(noePack("<1i",self.header['caps4']))
        file.writeBytes(noePack("<1i",self.header['reserved2']))
        self.Images[0].reverse()
        for l in range(self.Layers):
            for m in range(self.header['mipmapCount']):
                file.writeBytes(self.Images[l][m])
        return file
    
def mergeValidateInput(inVal):
    if os.path.exists(inVal) is not True:
        return "'" + inVal + "' is not a valid file path!"
    return None
BODYPART = {'Armor'         : 'Select Armor piece',
            'Right Hand'    : 'Select Right Weapon',
            'Left Hand'     : 'Select Left Weapon or Shield',
            'Helmet'        : 'Select Helmet',
            'Boots'         : 'Select Greaves',
            'Bracers'       : 'Select Bracers'}
def mergeToolMethod(toolIndex):
    r = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Select File", "Select a character model.", "", mergeValidateInput)
    if r is None:
        return 0
    dstFilePath = noesis.getScenesPath() + "merger.noesis"
    with open(dstFilePath, "w") as f:
        f.write("NOESIS_SCENE_FILE\r\nversion 1\r\nphysicslib           \"\"\r\ndefaultAxis             \"0\"\r\n\r\n")
        dirName = os.path.dirname(r)
        baseFileName, baseFileExt = os.path.splitext(r)
        if baseFileExt != '.msh' :
            noesis.messagePrompt("Not a TitanQuest model file!")
            return 0
        f.write("object\r\n{\r\n")
        f.write("       name            \"Character\"\r\n")
        f.write("       model           \"" + baseFileName + baseFileExt + "\"\r\n")
        f.write("}\r\n")
        for part in BODYPART:
            r = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Select File", BODYPART[part], "", mergeValidateInput)
            if r != None:
                dirName = os.path.dirname(r)
                baseFileName, baseFileExt = os.path.splitext(r)
                if baseFileExt == '.msh' :
                    f.write("object\r\n{\r\n")
                    f.write("       name            "+part+"\r\n")
                    f.write("       model           \"" + baseFileName + baseFileExt + "\"\r\n")
                    f.write("       mergeTo         \"Character\"\r\n")
                    f.write("       mergeBones      \"" + "%i"%1 + "\"\r\n")
                    f.write("}\r\n")
    return 0
