#Noesis Python model import+export test module, imports/exports some data from/to a made-up format
#version 0.01

from inc_noesis import *
import xml.dom.minidom as xd

import noesis

#rapi methods should only be used during handler callbacks
import rapi

#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
	handle = noesis.register("Noesis Python XML Test Model", ".noepyxml")
	noesis.setHandlerTypeCheck(handle, noepyXmlCheckType)
	noesis.setHandlerLoadModel(handle, noepyXmlLoadModel) #see also noepyLoadModelRPG
	noesis.setHandlerWriteModel(handle, noepyXmlWriteModel)
	noesis.setHandlerWriteAnim(handle, noepyXmlWriteAnim)

	#noesis.logPopup()
	#print("The log can be useful for catching debug prints from preview loads.\nBut don't leave it on when you release your script, or it will probably annoy people.")
	return 1

#check if it's this type based on the data
def noepyXmlCheckType(data):
	if len(data) < 8:
		return 0
	bs = NoeBitStream(data)

	return 1

#load the model
def noepyXmlLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	bs = NoeBitStream(data)
	rapi.rpgClearBufferBinds()	
	return 1


#write it
def noepyXmlWriteModel(mdl, bs):
	anims = rapi.getDeferredAnims()
	textures = rapi.loadMdlTextures(mdl)

	#Create the root XML node ans set attributes
	doc = xd.Document()
	root_node = doc.createElement("root")
	doc.appendChild(root_node)
	root_node.setAttribute("NOEPY_HEADER", str(0x1337455))
	root_node.setAttribute("NOEPY_VERSION", str(0x7178173))
	#Write the mesh node
	mesh_node = doc.createElement("meshes")
	root_node.appendChild(mesh_node)
	mesh_node.setAttribute("count", str(len(mdl.meshes)))
	for mesh in mdl.meshes:
		object_node = doc.createElement(mesh.name)
		mesh_node.appendChild(object_node)
		object_node.setAttribute("material_name", mesh.matName)
		#create sub object nodes
		#indices
		indices_node = doc.createElement("indices")
		object_node.appendChild(indices_node)
		indices_node.setAttribute("count", str(len(mesh.indices)))
		for idx in mesh.indices:
			sub_indices_node = doc.createTextNode(str(idx))
			indices_node.appendChild(sub_indices_node)
		#verts
		#positions
		positions_node = doc.createElement("positions")
		object_node.appendChild(positions_node)
		positions_node.setAttribute("count", str(len(mesh.positions)))
		for vcmp in mesh.positions:
			sub_positions_node = doc.createTextNode(str(vcmp))
			positions_node.appendChild(sub_positions_node)
		#normals
		normals_node = doc.createElement("normals")
		object_node.appendChild(normals_node)
		normals_node.setAttribute("count", str(len(mesh.normals)))
		for vcmp in mesh.normals:
			sub_normals_node = doc.createTextNode(str(vcmp))
			normals_node.appendChild(sub_normals_node)
		#uvs
		uvs_node = doc.createElement("uvs")
		object_node.appendChild(uvs_node)
		uvs_node.setAttribute("count", str(len(mesh.uvs)))
		for vcmp in mesh.uvs:
			sub_uvs_node = doc.createTextNode(str(vcmp))
			uvs_node.appendChild(sub_uvs_node)
		#tangents
		tangents_node = doc.createElement("tangents")
		object_node.appendChild(tangents_node)
		tangents_node.setAttribute("count", str(len(mesh.tangents)))
		for vcmp in mesh.tangents:
			sub_tangents_node = doc.createTextNode(str(vcmp))
			tangents_node.appendChild(sub_tangents_node)
		#colors
		colors_node = doc.createElement("colors")
		object_node.appendChild(colors_node)
		colors_node.setAttribute("count", str(len(mesh.colors)))
		for vcmp in mesh.colors:
			sub_colors_node = doc.createTextNode(str(vcmp))
			colors_node.appendChild(sub_colors_node)
		#weights
		weights_node = doc.createElement("weights")
		object_node.appendChild(weights_node)
		weights_node.setAttribute("count", str(len(mesh.weights)))
		for vcmp in mesh.weights:
			sub_weights_node = doc.createElement("bw")
			sub_weights_node.setAttribute("count", str(vcmp.numWeights()))
			weights_node.appendChild(sub_weights_node)
			bIndices_node = doc.createElement("bIndices")
			sub_weights_node.appendChild(bIndices_node)
			for wval in vcmp.indices:
				sub_bIndices_node = doc.createTextNode(str(wval))
				bIndices_node.appendChild(sub_bIndices_node)
			bWeights_node = doc.createElement("bWeights")
			sub_weights_node.appendChild(bWeights_node)
			for wval in vcmp.weights:
				sub_bWeights_node = doc.createTextNode(str(wval))
				bWeights_node.appendChild(sub_bWeights_node)
		#morphList
		morphList_node = doc.createElement("morphList")
		object_node.appendChild(morphList_node)
		morphList_node.setAttribute("count", str(len(mesh.morphList)))
		for mf in mesh.morphList:
			morph_node = doc.createElement("morph")
			morphList_node.appendChild(morph_node)
			morph_pos_node = doc.createElement("morph_pos")
			morph_node.appendChild(morph_pos_node)
			morph_pos_node.setAttribute("count", str(len(mf.positions)))
			for vec in mf.positions:
				sub_morph_pos_node = doc.createTextNode(str(vec))
				morph_pos_node.appendChild(sub_morph_pos_node)				
			morph_norm_node = doc.createElement("morph_norm")
			morph_node.appendChild(morph_norm_node)
			morph_norm_node.setAttribute("count", str(len(mf.normals)))
			for vec in mf.normals:
				sub_morph_norm_node = doc.createTextNode(str(vec))
				morph_norm_node.appendChild(sub_morph_norm_node)

	#Write the textures node
	texture_node = doc.createElement("textures")
	root_node.appendChild(texture_node)
	texture_node.setAttribute("count", str(len(textures)))
	for tex in textures:
		sub_tex_node = doc.createElement(tex.name)
		texture_node.appendChild(sub_tex_node)
		sub_tex_node.setAttribute("width", str(tex.width))
		sub_tex_node.setAttribute("height", str(tex.height))

	#Write the materials node
	material_node = doc.createElement("materials")
	root_node.appendChild(material_node)
	material_node.setAttribute("count", str(len(mdl.modelMats.matList)))
	for mat in mdl.modelMats.matList:
		sub_material_node = doc.createElement(str(mat.name))
		material_node.appendChild(sub_material_node)
		sub_material_node.setAttribute("texName", mat.texName)

	#Write the bone node
	bone_node = doc.createElement("bones")
	root_node.appendChild(bone_node)
	bone_node.setAttribute("count", str(len(mdl.bones)))
	for bone in mdl.bones:
		object_node = doc.createElement(bone.name)
		bone_node.appendChild(object_node)
		object_node.setAttribute("index", str(bone.index))
		object_node.setAttribute("parentName", bone.parentName)
		object_node.setAttribute("parentIndex", str(bone.parentIndex))
		object_node.setAttribute("matrix", str(bone.getMatrix()))

	#Write the anims node
	anims_node = doc.createElement("anims")
	root_node.appendChild(anims_node)
	anims_node.setAttribute("count", str(len(anims)))
	for anim in anims:
		anim_node = doc.createElement(anim.name)
		anims_node.appendChild(anim_node)
		anim_bone_node = doc.createElement("anim_bones")
		anim_node.appendChild(anim_bone_node)
		anim_bone_node.setAttribute("count", str(len(anim.bones)))
		for bone in anim.bones:
			bone_node = doc.createElement(bone.name)
			anim_bone_node.appendChild(bone_node)
			bone_node.setAttribute("index", str(bone.index))
			bone_node.setAttribute("parentName", bone.parentName)
			bone_node.setAttribute("parentIndex", str(bone.parentIndex))
			bone_node.setAttribute("matrix", str(bone.getMatrix()))
		anim_node.setAttribute("numFrames", str(anim.numFrames))
		anim_node.setAttribute("frameRate", str(anim.frameRate))
		anim_mats_node = doc.createElement("anim_mats")
		anim_node.appendChild(anim_mats_node)
		anim_mats_node.setAttribute("count", str(len(anim.frameMats)))
		for mat in anim.frameMats:
			sub_mat_node = doc.createTextNode(str(mat))
			anim_mats_node.appendChild(sub_mat_node)

	bs.writeBytes(doc.toprettyxml(encoding="ascii"))
	return 1
		

#when you want animation data to be written out with a model format, you should make a handler like this that catches it and defers it
def noepyXmlWriteAnim(anims, bs):
	#it's good practice for an animation-deferring handler to inform the user that the format only supports joint model-anim export
	if rapi.isGeometryTarget() == 0:
		print("WARNING: Stand-alone animations cannot be written to the .noepy format.")
		return 0

	rapi.setDeferredAnims(anims)
	return 0