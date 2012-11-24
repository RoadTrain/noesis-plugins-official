#Noesis Python model import+export test module, imports/exports some data from/to a made-up format

from inc_noesis import *

import noesis

#rapi methods should only be used during handler callbacks
import rapi

#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
	handle = noesis.register("Binary Domain/Yakuza", ".gmd")
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadModel(handle, noepyLoadModel) #see also noepyLoadModelRPG
	#noesis.setHandlerWriteModel(handle, noepyWriteModel)
	#noesis.setHandlerWriteAnim(handle, noepyWriteAnim)
	noesis.logPopup()
	#print("The log can be useful for catching debug prints from preview loads.\nBut don't leave it on when you release your script, or it will probably annoy people.")
	return 1

#check if it's this type based on the data

def noepyCheckType(data):
	bs = NoeBitStream(data)
	header = bs.readBytes(4).decode("ASCII")
	if header != 'GSGM':
		return 0
	return 1       

#load the model
def noepyLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	bs = NoeBitStream(data)
	bs.setEndian(NOE_BIGENDIAN)
	rapi.rpgSetOption(noesis.RPGOPT_BIGENDIAN, 1)
	fvfInto = []
	texList = []
	matList = []

	header = bs.readBytes(4).decode("ASCII")
	version1 = bs.readInt()
	version2 = bs.readInt()
	modelSize = bs.readInt()
	unk01 = bs.readUShort()
	sceneName = bs.readBytes(30).decode("ASCII").rstrip("\0")
	offset00 = bs.readInt()#Bone Matrix / Parent / 0x80
	count00  = bs.readInt()
	offset01 = bs.readInt()#info related to section before last? / 0x40
	count01  = bs.readInt()
	faceInfoOff = bs.readInt()#Face Info /0x40
	faceInfoSize = bs.readInt()
	materialOff = bs.readInt()
	materialCount  = bs.readInt()
	offset04 = bs.readInt()#? / 0x10
	count04  = bs.readInt()
	offset05 = bs.readInt()#Some Matrix / 0x40
	count05  = bs.readInt()
	vertInfoOff = bs.readInt()#Vertex Info / 0x20
	vertInfoSize  = bs.readInt()
	vertOff = bs.readInt()#Vertex Start / 1
	vertOffSize  = bs.readInt()
	texOff = bs.readInt()#Some Names / 0x20
	texCount  = bs.readInt()
	offset09 = bs.readInt()#Some Names / 0x20
	count09  = bs.readInt()
	offset10 = bs.readInt()#Bone Names / 0x20
	count10  = bs.readInt()
	faceOff = bs.readInt()#Some Face Info / 2
	faceOffSize  = bs.readInt()
	offset12 = bs.readInt()#? / 1
	count12  = bs.readInt()
	offset13 = bs.readInt()#? / 1
	count13  = bs.readInt()

	texName = []
	bs.seek(texOff, NOESEEK_ABS)
	for i in range(0, texCount):
		id = bs.readUShort()
		tmp = bs.readBytes(30).decode("ASCII").rstrip("\0")
		texName.append(tmp)

	bs.seek(materialOff, NOESEEK_ABS)
	for i in range(0, materialCount):
		matInfo = bs.read(">" + "h"*32)
		matInfo2 = bs.read(">" + "f"*16)
		material = NoeMaterial((str(i)), "")
		if matInfo[17] != -1:
			material.setTexture(texName[matInfo[17]] + ".dds")
		matList.append(material)
		#print(matInfo)

	faceInfo = []
	bs.seek(faceInfoOff, NOESEEK_ABS)
	for i in range(0, faceInfoSize):
		faceInfoTmp = bs.read(">iiiiiiiiiiiiiiii")
		#print(faceInfoTmp)
		faceInfo.append(faceInfoTmp)
	#for i in range(0, faceInfoSize):
	#	print(faceInfo[i])
	from operator import itemgetter
	faceInfo = sorted(faceInfo, key=itemgetter(2,1))
	#for i in range(0, faceInfoSize):
		#print(faceInfo[i])
	faceInfo2 = []
	for i in range(0, vertInfoSize):
		tmp = []
		for a in range(0, faceInfoSize):
			if faceInfo[a][2] == i:
				tmp.append(faceInfo[a])
		faceInfo2.append(tmp)
	#print(faceInfo2)

	bs.seek(vertInfoOff, NOESEEK_ABS)
	for i in range(0, vertInfoSize):
		meshID = bs.readInt()
		vertCount = bs.readInt()
		fvf00 = bs.readUByte()	
		fvf01 = bs.readUByte()
		fvf02 = bs.readUByte()
		fvf03 = bs.readUByte()
		fvf04 = bs.readUByte()
		fvf05 = bs.readUByte()
		fvf06 = bs.readUByte()
		fvf07 = bs.readUByte()
		vertStart = bs.readInt()
		vertDataSize = bs.readInt()
		vertSize = bs.readInt()
		null = bs.readInt()
		fvfInto.append([meshID,vertCount,vertStart,vertDataSize,vertSize,fvf00,fvf01,fvf02,fvf03,fvf04,fvf05,fvf06,fvf07])
	print(fvfInto)
	for i in range(0, vertInfoSize):
		bs.seek((vertOff + fvfInto[i][2]), NOESEEK_ABS)
		VertBuff = bs.readBytes(fvfInto[i][3])
		rapi.rpgBindPositionBufferOfs(VertBuff, noesis.RPGEODATA_FLOAT, fvfInto[i][4], 0)
		if fvfInto[i][8] == 4:
			rapi.rpgBindUV1BufferOfs(VertBuff, noesis.RPGEODATA_HALFFLOAT, fvfInto[i][4], (fvfInto[i][4] - 4))
		if fvfInto[i][8] == 0x44:
			rapi.rpgBindUV1BufferOfs(VertBuff, noesis.RPGEODATA_HALFFLOAT, fvfInto[i][4], (fvfInto[i][4] - 8))
		for a in range(0, len(faceInfo2[i])):
			rapi.rpgSetName(str(faceInfo2[i][a][1]))
			rapi.rpgSetMaterial(str(faceInfo2[i][a][1]))
			bs.seek(faceOff + (2 * faceInfo2[i][a][5]), NOESEEK_ABS)
			FaceBuff = bs.readBytes(faceInfo2[i][a][4] * 2)
			rapi.rpgCommitTriangles(FaceBuff, noesis.RPGEODATA_USHORT, faceInfo2[i][a][4], noesis.RPGEO_TRIANGLE, 1)
			bs.seek(faceOff + (2 * faceInfo2[i][a][7]), NOESEEK_ABS)
			FaceBuff = bs.readBytes(faceInfo2[i][a][6] * 2)
			rapi.rpgCommitTriangles(FaceBuff, noesis.RPGEODATA_USHORT, faceInfo2[i][a][6], noesis.RPGEO_TRIANGLE_STRIP, 1)
			bs.seek(faceOff + (2 * faceInfo2[i][a][9]), NOESEEK_ABS)
			FaceBuff = bs.readBytes(faceInfo2[i][a][8] * 2)
			rapi.rpgCommitTriangles(FaceBuff, noesis.RPGEODATA_USHORT, faceInfo2[i][a][8], noesis.RPGEO_TRIANGLE_STRIP, 1)

	mdl = rapi.rpgConstructModel()	
	mdl.setModelMaterials(NoeModelMaterials(texList, matList))
	mdlList.append(mdl)
	rapi.rpgClearBufferBinds()	
	return 1