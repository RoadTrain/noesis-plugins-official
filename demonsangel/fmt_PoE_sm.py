"""
Script: Path of exile full importer and exporter
import requires all art assets to be extracted from the archive

How to use:
    needs:  .sm  file (link to materials and model file)
            .smd file (mesh file)
            .ast file (armature) if rig.ast is not present a file dialog will open for you to select an .ast
            textures @ TEXPATH (see below)
            
"""


################################
###  Only change this line  ####
################################
TEXPATH = r"c:\users\Andrew\Desktop\XentaxScript\PoE\Art"

################################
### Do not change below here ###
################################
from inc_noesis import *
import noesis
import rapi
import struct

def registerNoesisTypes():
    handle = noesis.register("Path of Exile",".sm")
    noesis.setHandlerTypeCheck(handle,noepyCheckType)
    noesis.setHandlerLoadModel(handle,noepyLoadModel)
    handle = noesis.register("Path of Exile",".@smd")
    noesis.setHandlerWriteModel(handle, noepyWriteModel)
    return 1

def noepyCheckType(data):
    fName=rapi.getInputName().split('\\')[-1]
    dirPath = rapi.getDirForFilePath(rapi.getInputName())
    bs = open(dirPath + "/" + fName)
    idstring = line = bs.readline()
    idstring =''.join(idstring.split('\x00'))
    bs.close()
    if not "version" in idstring.lower() : return 0
    return 1


def noepyLoadModel(data,mdlList):
    ctx = rapi.rpgCreateContext()
    
    model       = POE()
    matList     = model.matList
    texList     = model.texList
    bones       = model.bones
    anims       = model.anims

    mdl = rapi.rpgConstructModelSlim()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdl.setBones(bones)
    mdl.setAnims(anims)
    mdlList.append(mdl)
    return 1
class POE:
    def __init__(self):
        self.filename       = rapi.getInputName().split('\\')[-1]
        self.dirPath        = rapi.getDirForFilePath(rapi.getInputName())
        self.matList        = []
        self.texList        = []
        self.bones          = []
        self.anims          = []
        self.GetMaterials()
        self.LoadModel()
        try:self.LoadArmature()
        except:print('Armature failed to init');pass
    def GetMaterials(self):
        sm          = open(self.dirPath + '/' + self.filename)
        materials   = []
        while 1:
            line    = sm.readline()
            line    = ''.join(line.split('\x00'))

            if 'skinnedmeshdata' in line.lower(): self.model = line[17:].split('/')[-1][:-2]
            if 'materials'       in line.lower():
                numMat  = int(line.lower().split('materials ')[1])
                for i in range(numMat):
                    sm.readline() # skip the damn \n\n
                    line        = sm.readline().lower()
                    line        = ''.join(line.split('\x00'))
                    material    = line.split('art/')[-1]
                    mat         = material.split('.mat')
                    material    = mat[0] + '.mat'
                    count       = int(mat[1].strip(' ').strip('\n').strip('"'))
                    for x in range(count):materials.append(material)
                break
        sm.close()
        self.materials = materials
    def CreateMaterial(self,index):
        try:mF                  = open( TEXPATH + '/' +self.materials[index] ,'r')
        except:
            for mat in self.materials:print(mat)
            raise
        diffuse     = None
        normal      = None
        specular    = None
        for i in range(10):
            line    = mF.readline()
            line    = ''.join(line.split('\x00')).lower()
            if 'colourtexture' in line:
                diffuse     = line[14:-2].split('art/')[-1]
            elif 'normalspeculartexture' in line:
                normal      = line[14:-2].split('art/')[-1]
                specular    = normal
            mF.readline()
        material            = NoeMaterial( self.meshNames[index] , '' )
        material.setTexture(diffuse.split('/')[-1])
        try:
            material.setNormalTexture(normal.split('/')[-1])
            material.setSpecularTexture(specular.split('/')[-1])
        except: pass
        for t in [diffuse,normal,specular]:
            try:
                tex         = open(TEXPATH + '/' +t,'rb').read()
                tex         = rapi.loadTexByHandler(tex,'.dds')
                tex.name    = t.split('/')[-1]
                self.texList.append(tex)
            except:pass
        self.matList.append(material)
        
    def LoadModel(self):
        self.data           = NoeBitStream( open(self.dirPath + self.model,'rb').read() )
        self.data.seek(1,1)
        self.numIdx         = self.data.readUInt()
        self.numVert        = self.data.readUInt()
        prop                = self.data.read('3B')
        totalStringLength   = self.data.readUInt()
        boundingBox         = self.data.read('6f')
        meshNames           = []
        stringLengths       = []
        idxGroups           = []

        for i in range(prop[1]):
            stringLengths.append(self.data.readUInt())
            idxGroups.append    (self.data.readUInt())
        
        for i in range(prop[1]):
            meshNames.append    (noeStrFromBytes(self.data.readBytes(stringLengths[i])))
        self.meshNames      = meshNames

        self.idxBuffer      = self.data.readBytes(self.numIdx * 6)
        self.vertBuffer     = self.data.readBytes(self.numVert * 64)

        for i in range(prop[1]):
            name            = ''.join(meshNames[i].split('\x00'))
            meshNames[i]    = name.split('Shape')[0]

        idxG    = []
        idxGroups.append(self.numIdx)
        for i in range(prop[1]):
            idxG.append(idxGroups[i+1] - idxGroups[i])

        for i in range(prop[1]):
            rapi.rpgBindPositionBufferOfs   (self.vertBuffer, noesis.RPGEODATA_FLOAT, 64, 0)
            rapi.rpgBindUV1BufferOfs        (self.vertBuffer, noesis.RPGEODATA_FLOAT, 64, 40)
            rapi.rpgBindNormalBufferOfs     (self.vertBuffer, noesis.RPGEODATA_FLOAT, 64, 12)
            #rapi.rpgBindColorBufferOfs      (self.vertBuffer, noesis.RPGEODATA_FLOAT, 64, 24, 4)
            rapi.rpgBindBoneIndexBufferOfs  (self.vertBuffer, noesis.RPGEODATA_UBYTE, 64, 48, 4)
            rapi.rpgBindBoneWeightBufferOfs (self.vertBuffer, noesis.RPGEODATA_FLOAT, 64, 52, 3)

            self.CreateMaterial(i)
            rapi.rpgSetMaterial(self.meshNames[i])

            min = idxGroups[i] * 6
            max = idxGroups[i+1] * 6
            rapi.rpgCommitTriangles(self.idxBuffer[min:max], noesis.RPGEODATA_USHORT,idxG[i]*3, noesis.RPGEO_TRIANGLE, 1)
    def LoadArmature(self):
        if not rapi.checkFileExists(self.dirPath+'/rig.ast'):
            data = rapi.loadPairedFileOptional('Path of Exile armature','ast')
            if data == None: return
            data = NoeBitStream(data)
        else:
            data = NoeBitStream(open(self.dirPath + '/rig.ast','rb').read())

        data.seek(1,1)
        numBones        = data.readUByte()
        data.seek(1,1)
        numAnim         = data.readUShort()
        data.seek(3,1)

        bones           = []
        parent          = []

        for i in range(numBones):
            parent.append( data.read('2B') )
            bone        = data.read('16f')
            length      = data.readUByte()
            name        = noeStrFromBytes( data.readBytes(length) )
            mat         = NoeMat44()
            mat.__setitem__(0, NoeVec4(bone[0 :4 ]))
            mat.__setitem__(1, NoeVec4(bone[4 :8 ]))
            mat.__setitem__(2, NoeVec4(bone[8 :12]))
            mat.__setitem__(3, NoeVec4(bone[12:  ]))
            mat         = mat.toMat43()
            bones.append(NoeBone(i,name,mat,None,-1))

        Parent = { 0:{'parent':-1} }
        for i in range(len(parent)):
            mod=parent[i]
            if mod[0] !=255:
                Parent[mod[0]] = {'parent':Parent[i]['parent']}
            if mod[1] !=255:
                Parent[mod[1]] = {'parent':i}
        for i in range(len(bones)):
            bone = bones[i]
            bone.parentIndex = Parent[i]['parent']
        animation={}
        animL=[]
        for i in range(numAnim):
            nBones = data.readUByte()
            data.seek(3,1)
            length = data.readUByte()
            name = noeStrFromBytes(data.readBytes(length))
            animation[i] = {'name':name,'data':[]}
            
            for t in range(nBones):
                data.seek(1,1)
                boneID = data.readUShort()
                dID=data.tell()
                data.seek(2,1)
                mod = data.readUShort()
                mods= data.read('12B')
                data.seek(12,1)
                numFrames = data.readUShort()
                data.seek(12,1)
                if mod == 3:
                    numFrames=data.readUShort()
                    data.seek(12,1)
                rot={}
                pos={}
                printing=[]
                for f in range(numFrames+1):
                    try:
                        ID=data.readUShort()
                        rot[ID]=data.read('4f')
                        if ID >=numFrames:break
                    except:
                        print("animation:",i,"\nbone:",t,"total:",nBones,"\nframe:",f,"ID:",ID)
                        raise
                for f in range(numFrames+1):
                    ID=data.readUShort()
                    pos[ID]=data.read('3f')
                    printing.append(ID)
                    if ID >=numFrames:break
                animation[i]['data'].append((boneID,(rot,pos),numFrames+1))
                data.seek(14*mods[8],1)
                if t == nBones: print(data.tell())
            animL.append(numFrames+1)
        anims=[]
        pLine=''
        for i in range(numAnim):
            anim = animation[i]
            name = anim['name']
            data = anim['data']
            frameMat=[]
            for b in range(len(data)):
                frameMat.append([])
                bone = data[b]
                rot  = bone[1][0]
                pos  = bone[1][1]
                for f in range(bone[2]):
                    
                    if f in rot:
                        mat = NoeQuat((rot[f][0],rot[f][1],rot[f][2],rot[f][3]))
                        mat = mat.toMat43()
                    else:
                        mat = frameMat[b][-1]
                        
                    
                    if f in pos:
                        mat.__setitem__(3,NoeVec3((pos[f])))
                    else:
                        mat.__setitem__(3,frameMat[b][-1][3])
                    if b == 0 and f==0:
                        rotate = NoeMat43(((-1,0,0),(0,0,-1),(0,-1,0),(0,0,0)))
                    frameMat[b].append(mat)
            matFrame=[]
            for f in range(animL[i]):
                mat = NoeMat43()
                for b in range(len(data)):
                    try:matFrame.append(frameMat[b][f])
                    except:print("%d %d"%(f,b))
            anims.append(NoeAnim(name,bones,animL[i],matFrame,1))
        
        bones = rapi.multiplyBones(bones)
        self.bones = bones
        self.anims = anims
def noepyWriteModel(mdl,bs):
    return 1













