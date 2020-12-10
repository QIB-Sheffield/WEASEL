from Developer.DeveloperTools import UserInterfaceTools
#**************************************************************************
import numpy as np
FILE_SUFFIX = "_Square"
# Can be an external toolbox instead
# from Developer.External.imagingTools import squareAlgorithm
#***************************************************************************

def isSeriesOnly(self):
    #This functionality only applies to a series of DICOM images
    return False


def main(objWeasel):
    ui = UserInterfaceTools(objWeasel)
    seriesList = ui.getCheckedSeries()
    for series in seriesList:
        newSeries = series.new(suffix=FILE_SUFFIX)
        pixelArray = series.PixelArray
        pixelArray = np.square(pixelArray)
        newSeries.write(pixelArray)
    ui.refreshWeasel(new_series_name=newSeries.seriesID)
    newSeries.DisplaySeries()
        
