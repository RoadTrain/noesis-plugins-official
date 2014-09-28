from inc_noesis import *
import os

def registerNoesisTypes():
	handle = noesis.registerTool("Assemble Vertex Morph Anim", assembleToolMethod, "Assembles vertex morph anim using assumed naming convention.")
	noesis.setToolFlags(handle, noesis.NTOOLFLAG_CONTEXTITEM)
	noesis.setToolVisibleCallback(handle, assembleContextVisible)
	return 1

def assembleContextVisible(toolIndex, selectedFile):
	if selectedFile is None or (noesis.getFormatExtensionFlags(os.path.splitext(selectedFile)[1]) & noesis.NFORMATFLAG_MODELREAD) == 0:
		return 0
	return 1
	
def getFirstMeshNameFromFirstFile(fileName):
	firstMeshName = "Unknown"
	noeMod = noesis.instantiateModule()
	noesis.setModuleRAPI(noeMod)
			
	if rapi.toolLoadGData(fileName):
		if rapi.toolGetLoadedModelCount() > 0:
			mdl = rapi.toolGetLoadedModel(0)
			if len(mdl.meshes) > 0:
				mesh = mdl.meshes[0]
				firstMeshName = mesh.name
		rapi.toolFreeGData()
	
	noesis.freeModule(noeMod)
	
	return firstMeshName
	
def assembleToolMethod(toolIndex):
	maxFrameCount = 512
	basePath = noesis.getSelectedFile()
	baseFileName, baseFileExt = os.path.splitext(basePath)
	expectedZeroIndex = baseFileName.rfind("0")
	if expectedZeroIndex < 0:
		noesis.messagePrompt("Expected 0 in filename.")
	else:
		frameAnimFileNames = []
		for frameCount in range(0, maxFrameCount):
			expectedFrameName = (
									basePath[:expectedZeroIndex] +
									"%i"%frameCount +
									basePath[expectedZeroIndex+1:]
								)
			print(expectedFrameName)
			if os.path.exists(expectedFrameName):
				frameAnimFileNames.append(expectedFrameName)
			else:
				break

		if len(frameAnimFileNames) == 0:
			noesis.messagePrompt("No files were found for assembly.")
		else:
			dstDefault = baseFileName + "_vmorph_assembly.noesis"
			dstFilePath = noesis.userPrompt(noesis.NOEUSERVAL_SAVEFILEPATH, "Save File", "Select destination path for the Noesis scene file.", dstDefault, None)
			if dstFilePath is not None:
				firstMeshName = getFirstMeshNameFromFirstFile(frameAnimFileNames[0])
				with open(dstFilePath, "w") as f:
					frameCount = len(frameAnimFileNames)
					f.write("NOESIS_SCENE_FILE\r\nversion 1\r\nphysicslib		\"\"\r\ndefaultAxis		\"0\"\r\noptionString		\"-fbxpreservecp\"\r\n\r\n")
					for objCount in range(0, frameCount):
						frameAnimFileName = frameAnimFileNames[objCount]
						f.write("object\r\n{\r\n")
						f.write("	name		\"node" + "%i"%objCount + "\"\r\n")
						f.write("	model		\"" + frameAnimFileName + "\"\r\n")
						if objCount == 0:
							f.write("	noSkelAnim	\"1\"\r\n")
							for objFrameIndex in range(1, frameCount):
								f.write("	morphFrame	\"node" + "%i"%objFrameIndex + "\" \"" + firstMeshName + "\" \"" + firstMeshName + "\"\r\n")
						else:
							f.write("	discard		\"1\"\r\n")
						f.write("}\r\n")
				print("Wrote Noesis scene file to '" + dstFilePath +"'.")
				noesis.openFile(dstFilePath)

	return 0
