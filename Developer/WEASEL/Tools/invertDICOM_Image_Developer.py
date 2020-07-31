import Developer.WEASEL.Tools.ToolsFunctions  as toolFunctions
#**************************************************************************
#Added by third party developer to the template module. 
#The function containing the image processing algorithm must be given the 
#generic name, funcAlgorithm
from Developer.WEASEL.ScientificLibrary.imagingTools import invertAlgorithm as funcAlgorithm
FILE_SUFFIX = '_Invert'
#***************************************************************************

def saveImage(objWeasel):
    toolFunctions.saveImage(objWeasel, FILE_SUFFIX, funcAlgorithm)