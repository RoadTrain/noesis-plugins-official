#Noesis Python model import+export test module, imports/exports some data from/to a made-up format

from inc_noesis import *
from array import array
from bitreader import *

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
	noesis.logPopup()
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
		# read EDGE indices header
		numIndices = bs.readUShort()
		#print('Num Indices: ' + str(numIndices))
		indexBase = bs.readUShort()
		#print('Base Index: ' + str(indexBase))
		sequenceSize = bs.readUShort()
		#print('Sequence Size: ' + str(sequenceSize))
		indexBitSize = bs.readUByte()
		#print('Index Bit Size: ' + str(indexBitSize))
		bs.readUByte() # padding
		# setup sequence bit stream
		sequenceCount = sequenceSize * 8
		#print('Sequence Count: ' + str(sequenceCount))
		sequenceBytes = bs.readBytes(sequenceSize)
		spec = ['data', {"count" : sequenceCount, "spec" : ["value", 1]}]
		reader = BitReader(spec, BitReader.BIG_ENDIAN)
		sequenceStream = reader.read(sequenceBytes)
		# setup triangle bit stream
		triangleCount = indexCount // 3
		#print('Triangle Count: ' + str(triangleCount))
		triangleSize = ((triangleCount * 2) + 7) // 8
		#print('Trangle Size: ' + str(triangleSize))
		triangleBytes = bs.readBytes(triangleSize)
		spec = ['data', {"count" : triangleCount, "spec" : ["value", 2]}]
		reader = BitReader(spec, BitReader.BIG_ENDIAN)
		triangleStream = reader.read(triangleBytes)
		# setup indices bit stream
		indicesSize = ((numIndices * indexBitSize) + 7) // 8
		#print('Indices Size: ' + str(indicesSize))
		#print('Indices Offset: ' + str(bs.getOffset()))
		indicesBytes = bs.readBytes(indicesSize)
		spec = ['data', {"count" : numIndices, "spec" : ["value", indexBitSize]}]
		reader = BitReader(spec, BitReader.BIG_ENDIAN)
		indicesStream = reader.read(indicesBytes)
		# indicesStream = NoeBitStream(indicesBytes)
		# indicesStream.setEndian(NOE_BIGENDIAN)
		# read delta compressed indices
		deltaIndices = array('H')
		for i in range(0, numIndices):
			value = indicesStream.data[i].value
			if i == 1:
				pass
				#print('Index Bit Value: ' + str(value) + ' Index: ' + str(i))
			value -= indexBase
			if i > 7:
				value += deltaIndices[i - 8]
			deltaIndices.append(value)
		# create sequence indices
		inputIndices = array('H')
		sequencedIndex = 0
		unorderedIndex = 0
		for i in range(0, sequenceCount):
			value = sequenceStream.data[i].value
			if value == 0:
				inputIndices.append(sequencedIndex)
				sequencedIndex += 1
			else:
				inputIndices.append(deltaIndices[unorderedIndex])
				unorderedIndex += 1
		# create triangle indices
		outputIndices = array('H')
		currentIndex = 0
		triangleIndices = [0, 0, 0]
		# triangleIndices = {0:0, 1:0, 2:0}
		for i in range(0, triangleCount):
			value = triangleStream.data[i].value
			if value == 0:
				triangleIndices[1] = triangleIndices[2]
				triangleIndices[2] = inputIndices[currentIndex]
				currentIndex += 1
			elif value == 1:
				triangleIndices[0] = triangleIndices[2]
				triangleIndices[2] = inputIndices[currentIndex]
				currentIndex += 1
			elif value == 2:
				tempIndex = triangleIndices[0]
				triangleIndices[0] = triangleIndices[1]
				triangleIndices[1] = tempIndex
				triangleIndices[2] = inputIndices[currentIndex]
				currentIndex += 1
			else: # value == 3:
				triangleIndices[0] = inputIndices[currentIndex]
				currentIndex += 1
				triangleIndices[1] = inputIndices[currentIndex]
				currentIndex += 1
				triangleIndices[2] = inputIndices[currentIndex]
				currentIndex += 1
			outputIndices.append(triangleIndices[0])
			outputIndices.append(triangleIndices[1])
			outputIndices.append(triangleIndices[2])
		bs.seek(vertexOffset, NOESEEK_ABS)
		vertexSize = 16 * vertexCount
		vertbuff = bs.readBytes(vertexSize)
		rapi.rpgBindPositionBufferOfs(vertbuff, noesis.RPGEODATA_FLOAT, 16, 0)
		faceBuff = struct.pack(">" + 'h'*len(outputIndices), *outputIndices)
		#print(outputIndices[len(outputIndices) - 1])
		#print(outputIndices)
		rapi.rpgSetName(str(i))
		#rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, (vertexSize // 16), noesis.RPGEO_POINTS, 1)
		rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, len(outputIndices), noesis.RPGEO_TRIANGLE, 1)
	mdl = rapi.rpgConstructModel()
	mdlList.append(mdl)
	rapi.rpgClearBufferBinds()	
	return 1