from inc_noesis import *
import os

#MERGE_BONES
#0 = no collapsing
#1 = collapse by name
#2 = collapse by name and reapply relative transforms
#3 = collapse by name and reapply relative transforms, retransforming geometry as well
MERGE_BONES = 0

def registerNoesisTypes():
	handle = noesis.registerTool("&Model merger", mergeToolMethod, "Merge all models of a given type and load them into a single scene")
	return 1

def mergeValidateInput(inVal):
	if os.path.exists(inVal) is not True:
		return "'" + inVal + "' is not a valid file path!"
	return None

def mergeToolMethod(toolIndex):
	r = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Select File", "Select a model, and all models of that type in the same directory will be loaded as one.", "", mergeValidateInput)
	if r is None:
		return 0
	
	dstFilePath = noesis.getScenesPath() + "merger.noesis"
	with open(dstFilePath, "w") as f:
		f.write("NOESIS_SCENE_FILE\r\nversion 1\r\nphysicslib		\"\"\r\ndefaultAxis		\"0\"\r\n\r\n")
		dirName = os.path.dirname(r)
		baseFileName, baseFileExt = os.path.splitext(r)
		dirList = os.listdir(dirName)
		numObj = 0
		for fileName in dirList:
			n, ext = os.path.splitext(fileName)
			if ext == baseFileExt:
				f.write("object\r\n{\r\n")
				f.write("	name		\"node" + "%i"%numObj + "\"\r\n")
				f.write("	model		\"" + dirName + "\\" + fileName + "\"\r\n")
				if numObj > 0:
					f.write("	mergeTo		\"node0\"\r\n")
					if MERGE_BONES != 0:
						f.write("	mergeBones	\"" + "%i"%MERGE_BONES + "\"\r\n")
				f.write("}\r\n")
				numObj += 1
	if noesis.openFile(dstFilePath) is not True:
		noesis.messagePrompt("Could not open merged model file!")
	return 0
