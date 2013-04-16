from inc_noesis import *
import os

def registerNoesisTypes():
	handle = noesis.registerTool("&Get material info", gmToolMethod, "Prints out material info for selected model")
	return 1

def printMaterialInfo(mat):
	print("Material name:", noeSafeGet(mat, "name"))
	print("Diffuse:", noeSafeGet(mat, "texName"))
	print("Normal:", noeSafeGet(mat, "nrmTexName"))
	print("Bump:", noeSafeGet(mat, "bumpTexName"))
	print("Specular:", noeSafeGet(mat, "specTexName"))
	print("Opacity:", noeSafeGet(mat, "opacTexName"))
	print("Flags:", noeSafeGet(mat, "flags"))
	print("Blend mode:", noeSafeGet(mat, "blendSrc"), noeSafeGet(mat, "blendDst"))
	nextPass = noeSafeGet(mat, "nextPass")
	if nextPass is not None:
		print("== Additional pass ==")
		printMaterialInfo(nextPass)
	print("")

def gmToolMethod(toolIndex):
	selFileName = noesis.getSelectedFile()
	if selFileName == "":
		noesis.messagePrompt("No file selected.")
		return 0

	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)
	if rapi.toolLoadGData(selFileName) is not True:
		noesis.freeModule(noeMod)
		noesis.messagePrompt("Could not load selected model.")
		return 0

	noesis.logPopup()
	for i in range(0, rapi.toolGetLoadedModelCount()):
		mdl = rapi.toolGetLoadedModel(i)
		if mdl.modelMats is not None and mdl.modelMats.matList is not None:
			print("Materials for model", i)
			print("=====================")
			for mat in mdl.modelMats.matList:
				printMaterialInfo(mat)

	rapi.toolFreeGData()
	noesis.freeModule(noeMod)
	
	return 0
