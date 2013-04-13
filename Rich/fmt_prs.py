from inc_noesis import *

def registerNoesisTypes():
   handle = noesis.register("PRS Data", ".prs")
   noesis.setHandlerExtractArc(handle, prsExtractArc)
   return 1

#assumes the prs is just a raw stream of PRS-compressed data, and decompresses to a single file.
def prsExtractArc(fileName, fileLen, justChecking):
   with open(fileName, "rb") as f:
      if justChecking:
         return 1
      compData = f.read(fileLen)
      decomp = rapi.decompPRS(compData, rapi.getPRSSize(compData))
      fname = rapi.getExtensionlessName(rapi.getLocalFileName(rapi.getLastCheckedName())) + "_decomp.nj"
      print("Writing", fname)
      rapi.exportArchiveFile(fname, decomp)
   return 1
