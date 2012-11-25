#Noesis Python model import+export test module, imports/exports some data from/to a made-up format

from inc_noesis import *

import noesis

#rapi methods should only be used during handler callbacks
import rapi

#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
	handle = noesis.register("Noesis Python Bonemap Example", ".noepyb")
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadModel(handle, noepyLoadModel)
	noesis.setHandlerWriteModel(handle, noepyWriteModel)
	noesis.setHandlerWriteAnim(handle, noepyWriteAnim)
	return 1

NOEPY_HEADER = 0x1337F00
NOEPY_VERSION = 0x7178173

#check if it's this type based on the data
def noepyCheckType(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)

	if bs.readInt() != NOEPY_HEADER:
		return 0
	if bs.readInt() != NOEPY_VERSION:
		return 0

	return 1

#load the model
def noepyLoadModel(data, mdlList):
	bs = NoeBitStream(data)
	if bs.readInt() != NOEPY_HEADER:
		return 0
	if bs.readInt() != NOEPY_VERSION:
		return 0

	#no need to explicitly free the context (created contexts are auto-freed after the handler), but DO NOT hold any references to it outside of this method
	ctx = rapi.rpgCreateContext()

	numMeshes = bs.readInt()
	for i in range(0, numMeshes):
		meshName = bs.readString()
		meshMat = bs.readString()
		numIdx = bs.readInt()
		numPos = bs.readInt()
		numNrm = bs.readInt()
		numUVs = bs.readInt()
		numTan = bs.readInt()
		numClr = bs.readInt()
		numWeights = bs.readInt()
		numBoneRefs = bs.readInt()
		if numBoneRefs > 0:
			boneMap = bs.read("i"*numBoneRefs)
			rapi.rpgSetBoneMap(boneMap) #set the bone map

		rapi.rpgSetName(meshName)
		rapi.rpgSetMaterial(meshMat)

		triangles = bs.readBytes(numIdx * 4)
		positions = bs.readBytes(numPos * 12)
		normals = bs.readBytes(numPos * 12) if numNrm == numPos else None
		uvs = bs.readBytes(numPos * 12) if numUVs == numPos else None
		tans = bs.readBytes(numPos * 48) if numTan == numPos else None
		colors = bs.readBytes(numPos * 16) if numClr == numPos else None

		rapi.rpgBindPositionBuffer(positions, noesis.RPGEODATA_FLOAT, 12)
		rapi.rpgBindNormalBuffer(normals, noesis.RPGEODATA_FLOAT, 12)
		rapi.rpgBindUV1Buffer(uvs, noesis.RPGEODATA_FLOAT, 12)
		rapi.rpgBindColorBuffer(colors, noesis.RPGEODATA_FLOAT, 16, 4)
		if numWeights > 0:
			vwList = []
			for j in range(0, numWeights):
				vwNum = bs.readInt()
				bidx = []
				bwgt = []
				for k in range(0, vwNum):
					bidx.append(bs.readInt())
				for k in range(0, vwNum):
					bwgt.append(bs.readFloat())
				vwList.append(NoeVertWeight(bidx, bwgt))
			fw = NoeFlatWeights(vwList)
			rapi.rpgBindBoneIndexBuffer(fw.flatW[:fw.weightValOfs], noesis.RPGEODATA_INT, 4*fw.weightsPerVert, fw.weightsPerVert)
			rapi.rpgBindBoneWeightBuffer(fw.flatW[fw.weightValOfs:], noesis.RPGEODATA_FLOAT, 4*fw.weightsPerVert, fw.weightsPerVert)
		numMorphFrames = bs.readInt()
		for j in range(0, numMorphFrames):
			numMFPos = bs.readInt()
			numMFNrm = bs.readInt()
			morphPosAr = bs.readBytes(numMFPos * 12)
			rapi.rpgFeedMorphTargetPositions(morphPosAr, noesis.RPGEODATA_FLOAT, 12)
			if numMFNrm > 0:
				morphNrmAr = bs.readBytes(numMFNrm * 12)
				rapi.rpgFeedMorphTargetNormals(morphNrmAr, noesis.RPGEODATA_FLOAT, 12)
			rapi.rpgCommitMorphFrame(numMFPos)
		rapi.rpgCommitMorphFrameSet()

		rapi.rpgCommitTriangles(triangles, noesis.RPGEODATA_INT, numIdx, noesis.RPGEO_TRIANGLE, 1)
		rapi.rpgClearBufferBinds() #reset in case a subsequent mesh doesn't have the same components

	mdl = rapi.rpgConstructModel()

	bones = []
	numBones = bs.readInt()
	for i in range(0, numBones):
		bone = noepyReadBone(bs)
		bones.append(bone)

	anims = []
	numAnims = bs.readInt()
	for i in range(0, numAnims):
		animName = bs.readString()
		numAnimBones = bs.readInt()
		animBones = []
		for j in range(0, numAnimBones):
			animBone = noepyReadBone(bs)
			animBones.append(animBone)
		animNumFrames = bs.readInt()
		animFrameRate = bs.readFloat()
		numFrameMats = bs.readInt()
		animFrameMats = []
		for j in range(0, numFrameMats):
			frameMat = NoeMat43.fromBytes(bs.readBytes(48))
			animFrameMats.append(frameMat)
		anim = NoeAnim(animName, animBones, animNumFrames, animFrameMats, animFrameRate)
		anims.append(anim)

	mdl.setBones(bones)
	mdl.setAnims(anims)
	mdlList.append(mdl)			#important, don't forget to put your loaded model in the mdlList
	return 1

#write it
def noepyWriteModel(mdl, bs):
	anims = rapi.getDeferredAnims()

	bs.writeInt(NOEPY_HEADER)
	bs.writeInt(NOEPY_VERSION)

	bs.writeInt(len(mdl.meshes))
	for mesh in mdl.meshes:
		boneMap = None
		if len(mesh.weights) > 0:
			boneMap = rapi.createBoneMap(mesh.weights)
		bs.writeString(mesh.name)
		bs.writeString(mesh.matName)
		bs.writeInt(len(mesh.indices))
		bs.writeInt(len(mesh.positions))
		bs.writeInt(len(mesh.normals))
		bs.writeInt(len(mesh.uvs))
		bs.writeInt(len(mesh.tangents))
		bs.writeInt(len(mesh.colors))
		bs.writeInt(len(mesh.weights))
		#generate and write the bone map
		if boneMap is None:
			bs.writeInt(0)
		else:
			bs.writeInt(len(boneMap))
			for bval in boneMap:
				bs.writeInt(bval)
		
		for idx in mesh.indices:
			bs.writeInt(idx)
		for vcmp in mesh.positions:
			bs.writeBytes(vcmp.toBytes())
		for vcmp in mesh.normals:
			bs.writeBytes(vcmp.toBytes())
		for vcmp in mesh.uvs:
			bs.writeBytes(vcmp.toBytes())
		for vcmp in mesh.tangents:
			bs.writeBytes(vcmp.toBytes())
		for vcmp in mesh.colors:
			bs.writeBytes(vcmp.toBytes())
		for vcmp in mesh.weights:
			bs.writeInt(vcmp.numWeights())
			for wval in vcmp.indices:
				bs.writeInt(wval)
			for wval in vcmp.weights:
				bs.writeFloat(wval)
		bs.writeInt(len(mesh.morphList))
		for mf in mesh.morphList:
			bs.writeInt(len(mf.positions))
			bs.writeInt(len(mf.normals))
			for vec in mf.positions:
				bs.writeBytes(vec.toBytes())
			for vec in mf.normals:
				bs.writeBytes(vec.toBytes())

	bs.writeInt(len(mdl.bones))
	for bone in mdl.bones:
		noepyWriteBone(bs, bone)

	bs.writeInt(len(anims))
	for anim in anims:
		bs.writeString(anim.name)
		bs.writeInt(len(anim.bones))
		for bone in anim.bones:
			noepyWriteBone(bs, bone)
		bs.writeInt(anim.numFrames)
		bs.writeFloat(anim.frameRate)
		bs.writeInt(len(anim.frameMats))
		for mat in anim.frameMats:
			bs.writeBytes(mat.toBytes())

	return 1

#when you want animation data to be written out with a model format, you should make a handler like this that catches it and defers it
def noepyWriteAnim(anims, bs):
	#it's good practice for an animation-deferring handler to inform the user that the format only supports joint model-anim export
	if rapi.isGeometryTarget() == 0:
		print("WARNING: Stand-alone animations cannot be written to the .noepy format.")
		return 0

	rapi.setDeferredAnims(anims)
	return 0

#write bone
def noepyWriteBone(bs, bone):
	bs.writeInt(bone.index)
	bs.writeString(bone.name)
	bs.writeString(bone.parentName)
	bs.writeInt(bone.parentIndex)
	bs.writeBytes(bone.getMatrix().toBytes())

#read bone
def noepyReadBone(bs):
	boneIndex = bs.readInt()
	boneName = bs.readString()
	bonePName = bs.readString()
	bonePIndex = bs.readInt()
	boneMat = NoeMat43.fromBytes(bs.readBytes(48))
	return NoeBone(boneIndex, boneName, boneMat, bonePName, bonePIndex)
