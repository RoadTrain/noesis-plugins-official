#Noesis Python model import+export test module, imports/exports some data from/to a made-up format

from inc_noesis import *
from array import array

import noesis

#rapi methods should only be used during handler callbacks
import rapi

#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
	handle = noesis.register("Playstation All Stars", ".cskn")
	noesis.setHandlerTypeCheck(handle, psaCheckType)
	noesis.setHandlerLoadModel(handle, psaLoadModel) #see also noepyLoadModelRPG
	#noesis.setHandlerWriteModel(handle, noepyWriteModel)
	#noesis.setHandlerWriteAnim(handle, noepyWriteAnim)
	#noesis.logPopup()
	return 1

#check if it's this type based on the data

def psaCheckType(data):
	bs = NoeBitStream(data)
	IdMagic = bs.readBytes(4).decode("ASCII")
	if IdMagic != "MODL":
		return 0
	return 1       

#load the model
def psaLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	bs = NoeBitStream(data)
	bs.setEndian(NOE_BIGENDIAN)
	rapi.rpgSetOption(noesis.RPGOPT_BIGENDIAN, 1)
	rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
	IdMagic = bs.readBytes(4).decode("ASCII")
	version = bs.readUInt()
	modelCount = bs.readUInt()
	fvfTableOffset = bs.readUInt()
	bs.seek(fvfTableOffset, NOESEEK_ABS)
	for i in range(0, modelCount):
		bs.seek(fvfTableOffset + (0x80 * i), NOESEEK_ABS)
		bs.seek(0x08, NOESEEK_REL)
		vertexCount = bs.readUShort()
		indexCount = bs.readUShort()
		#print('Index Count: ' + str(indexCount))
		bs.seek(0x04, NOESEEK_REL)
		indexOffset = bs.readUInt()
		#print('Index Offset: ' + str(indexOffset))
		indexSize = bs.readUShort()
		unk01 = bs.readUShort()
		vertexOffset = bs.readUInt()
		unkown01Offset = bs.readUInt()
		vertexSize = bs.readUShort()
		bs.seek(0x5E, NOESEEK_REL)
		bs.seek(indexOffset, NOESEEK_ABS)
		edgeData = bs.readBytes(indexSize)
		edgeDecomp = rapi.decompressEdgeIndices(edgeData, indexCount)
		for i in range(0, indexCount): #decompressEdgeIndices returns indices in little-endian, so swap back to big because rpg is in bigendian mode
			t = edgeDecomp[i*2]
			edgeDecomp[i*2] = edgeDecomp[i*2 + 1]
			edgeDecomp[i*2 + 1] = t
			
		bs.seek(vertexOffset, NOESEEK_ABS)
		vertexSize = 16 * vertexCount
		vertbuff = bs.readBytes(vertexSize)
		rapi.rpgBindPositionBufferOfs(vertbuff, noesis.RPGEODATA_FLOAT, 16, 0)
		#print(outputIndices[len(outputIndices) - 1])
		#print(outputIndices)
		rapi.rpgSetName(str(i))
		#rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, (vertexSize // 16), noesis.RPGEO_POINTS, 1)
		rapi.rpgCommitTriangles(edgeDecomp, noesis.RPGEODATA_USHORT, indexCount, noesis.RPGEO_TRIANGLE, 1)
	mdl = rapi.rpgConstructModel()
	mdlList.append(mdl)
	rapi.rpgClearBufferBinds()	
	return 1