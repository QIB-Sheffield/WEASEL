import Developer.MenuItems.developerToolsModule as tool
#**************************************************************************
#Added by third party developer to the template module. 
#The function containing the image processing algorithm must be given the 
#generic name, funcAlgorithm
#uncomment and edit the following line of code to import the function 
#containing your image processing algorith. 
from Developer.SciPackages.imagingTools import gaussianFilter
FILE_SUFFIX = '_Gaussian'
#***************************************************************************

def isSeriesOnly(self):
    #This functionality only applies to a series of DICOM images
    return True


def main(objWeasel):
    if tool.treeView.isAnImageSelected(objWeasel):
        imagePath = tool.getImagePath(objWeasel)
        derivedImageFileName = tool.setNewFilePath(imagePath, FILE_SUFFIX)
        pixelArray = tool.getPixelArrayFromDICOM(imagePath)
        # Standard deviation value is hard coded here. I'm passing sigma=10 for the gaussian filter
        derivedImage = tool.applyProcessInOneImage(gaussianFilter, pixelArray, 10)
        tool.saveNewDICOMAndDisplayResult(objWeasel, imagePath, derivedImageFileName, derivedImage, FILE_SUFFIX)
    elif tool.treeView.isASeriesSelected(objWeasel):
        imagePathList = tool.getImagePathList(objWeasel)
        # Standard deviation value is hard coded here. I'm passing sigma=10 for the gaussian filter
        # No progress bar, as flagged below
        derivedImagePathList, derivedImageList = tool.applyProcessIterativelyInSeries(objWeasel, imagePathList, FILE_SUFFIX, gaussianFilter, 10, progress_bar=False)        
        tool.saveNewDICOMAndDisplayResult(objWeasel, imagePathList, derivedImagePathList, derivedImageList, FILE_SUFFIX)


def GroupWise(objWeasel):
    # In this case, the user introduces the sigma value intended for the gaussian filter
    inputDict = {"Standard Deviation":"float"}
    paramList = tool.inputWindow(inputDict, title="Input Parameters for the Gaussian Filter")
    standard_deviation_filter = paramList[0]
    imagePathList = tool.getImagePathList(objWeasel)
    tool.showProcessingMessageBox(objWeasel)
    pixelArray = tool.getPixelArrayFromDICOM(imagePathList)
    derivedImage = tool.applyProcessInOneImage(gaussianFilter, pixelArray, standard_deviation_filter)
    derivedImagePathList, derivedImageList = tool.prepareBulkSeriesSave(objWeasel, imagePathList, derivedImage, FILE_SUFFIX)
    tool.saveNewDICOMAndDisplayResult(objWeasel, imagePathList, derivedImagePathList, derivedImageList, FILE_SUFFIX)
