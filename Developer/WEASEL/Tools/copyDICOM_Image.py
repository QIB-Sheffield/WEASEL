import os
import numpy as np
import readDICOM_Image
import saveDICOM_Image
from Weasel import Weasel as weasel
from weaselXMLReader import WeaselXMLReader

FILE_SUFFIX = '_copy'

def returnCopiedFile(imagePath):
    """Inverts an image. Bits that are 0 become 1, and those that are 1 become 0"""
    try:
        if os.path.exists(imagePath):
            dataset = readDICOM_Image.getDicomDataset(imagePath)
            pixelArray = readDICOM_Image.getPixelArray(dataset)
            newFileName = saveDICOM_Image.save_automatically_and_returnFilePath(
                 imagePath, pixelArray, FILE_SUFFIX)
            return  newFileName
        else:
            return None
    except Exception as e:
            print('Error in function copyDICOM_Image.returnPixelArray: ' + str(e))


def copySeries(objWeasel):
        try:
            #imageList, studyID, _ = weasel.getImagePathList_Copy()  
            studyID = objWeasel.selectedStudy 
            seriesID = objWeasel.selectedSeries
            imageList = \
                    objWeasel.getImagePathList(studyID, seriesID)
            #Iterate through list of images and make a copy of each image
            copiedImageList = []
            numImages = len(imageList)
            objWeasel.displayMessageSubWindow(
              "<H4>Copying {} DICOM files</H4>".format(numImages),
              "Copying DICOM images")
            objWeasel.setMsgWindowProgBarMaxValue(numImages)
            imageCounter = 0
            for imagePath in imageList:
                copiedImageFilePath = returnCopiedFile(imagePath)
                copiedImageList.append(copiedImageFilePath)
                imageCounter += 1
                objWeasel.setMsgWindowProgBarValue(imageCounter)

            objWeasel.closeMessageSubWindow()
            newSeriesID= objWeasel.insertNewSeriesInXMLFile(imageList, \
                copiedImageList, FILE_SUFFIX)
            objWeasel.displayMultiImageSubWindow(copiedImageList, 
                                              studyID, newSeriesID)
            objWeasel.refreshDICOMStudiesTreeView(newSeriesID)
        except Exception as e:
            print('Error in copyDICOM_Image.copySeries: ' + str(e))

