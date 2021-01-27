
import MenuItems.ToolsFunctions  as toolFunctions
#**************************************************************************
#Added by third party developer to the template module. 
#The function containing the image processing algorithm must be given the 
#generic name, funcAlgorithm
#uncomment and edit the following line of code to import the function 
#containing your image processing algorith. 
from CoreModules.imagingTools import squareAlgorithm as funcAlgorithm
FILE_SUFFIX = '_Square'
#***************************************************************************


def main(objWeasel):
    toolFunctions.main(objWeasel, FILE_SUFFIX, funcAlgorithm)

