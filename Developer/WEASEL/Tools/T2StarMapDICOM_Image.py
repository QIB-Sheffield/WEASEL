import os
import numpy as np
import re
import CoreModules.readDICOM_Image as readDICOM_Image
import CoreModules.saveDICOM_Image as saveDICOM_Image
from CoreModules.weaselToolsXMLReader import WeaselToolsXMLReader
from CoreModules.imagingTools import formatArrayForAnalysis
from ukrinAlgorithms import ukrinMaps

FILE_SUFFIX = '_T2StarMap'

def returnPixelArray(imagePathList, sliceList, echoList):
    """Returns the T2* Map Array"""
    try:
        if os.path.exists(imagePathList[0]):
            dataset = readDICOM_Image.getDicomDataset(imagePathList[0])
            if hasattr(dataset, 'PerFrameFunctionalGroupsSequence'): # For Enhanced MRI, sliceList is a list of indices
                volumeArray, sliceList, numberSlices = readDICOM_Image.getMultiframeBySlices(dataset, sliceList=sliceList, sort=True)
            else: # For normal DICOM, slicelist is a list of slice locations in mm.
                volumeArray = readDICOM_Image.returnSeriesPixelArray(imagePathList)
                numberSlices = len(np.unique(sliceList))
            # The echo values repeat, so this is to remove all values=0 and repetitions
            echoList = np.delete(np.unique(echoList), np.where(np.unique(echoList) == 0.0))
            pixelArray = formatArrayForAnalysis(volumeArray, numberSlices, dataset, dimension='4D', resize=3)
            # Algorithm 
            derivedImage = ukrinMaps(pixelArray).T2Star(echoList)
            del volumeArray, pixelArray, numberSlices, dataset, echoList
            return derivedImage
        else:
            return None
    except Exception as e:
        print('Error in function T2StarMapDICOM_Image.returnPixelArray: ' + str(e))


def getParametersT2StarMap(imagePathList, seriesID):
    """This method checks if the series in imagePathList meets the criteria to be processed and calculate T2* Map"""
    try:
        if os.path.exists(imagePathList[0]):
            magnitudePathList = []
            datasetList = readDICOM_Image.getDicomDataset(imagePathList[0]) # even though it can be 1 file only, I'm naming datasetList due to consistency
            if hasattr(datasetList, 'PerFrameFunctionalGroupsSequence'):
                echoList = []
                sliceList = []
                numberEchoes = datasetList[0x20011014].value
                _, originalSliceList, numberSlices = readDICOM_Image.getMultiframeBySlices(datasetList)
                for index, dataset in enumerate(datasetList.PerFrameFunctionalGroupsSequence):
                    flagMagnitude, _, _, _, _ = readDICOM_Image.checkImageType(dataset)
                    echo = dataset.MREchoSequence[0].EffectiveEchoTime
                    if (numberEchoes == 12) and (echo != 0) and flagMagnitude and (re.match(".*t2.*", seriesID.lower()) or re.match(".*r2.*", seriesID.lower())):
                        sliceList.append(originalSliceList[index])
                        echoList.append(echo)
                if sliceList and echoList:
                    #echoList = np.unique(echoList)
                    magnitudePathList = imagePathList
            else:
                imagePathList, firstSliceList, numberSlices, _ = readDICOM_Image.sortSequenceByTag(imagePathList, "SliceLocation")
                imagePathList, echoList, numberEchoes, indicesSorted = readDICOM_Image.sortSequenceByTag(imagePathList, "EchoTime")
                # After sorting, it needs to update the sliceList
                sliceList = [firstSliceList[index] for index in indicesSorted]
                for index in range(len(imagePathList)):
                    dataset = readDICOM_Image.getDicomDataset(imagePathList[index])
                    flagMagnitude, _, _, _, _ = readDICOM_Image.checkImageType(dataset)
                    echo = echoList[index]
                    # Can use numberEchoes > 8 or similar
                    if (numberEchoes == 12) and (echo != 0) and flagMagnitude and (re.match(".*t2.*", seriesID.lower()) or re.match(".*r2.*", seriesID.lower())):
                        magnitudePathList.append(imagePathList[index])
            del datasetList, numberSlices, numberEchoes, flagMagnitude
            return magnitudePathList, sliceList, echoList
        else:
            return None, None, None
    except Exception as e:
        print('Error in function T2StarMapDICOM_Image.getParametersT2StarMap: ' + str(e))


def saveT2StarMapSeries(objWeasel):
    """Main method called from WEASEL to calculate the T2* Map"""
    try:
        studyID = objWeasel.selectedStudy
        seriesID = objWeasel.selectedSeries
        imagePathList = \
            objWeasel.getImagePathList(studyID, seriesID)

        objWeasel.displayMessageSubWindow(
            "<H4>Extracting parameters to calculate T2* Map</H4>",
            "Saving T2* Map")
        objWeasel.setMsgWindowProgBarMaxValue(4)
        objWeasel.setMsgWindowProgBarValue(1)

        magnitudePathList, sliceList, echoList = getParametersT2StarMap(imagePathList, seriesID)

        objWeasel.displayMessageSubWindow(
            "<H4>Calculating the T2* Map</H4>",
            "Saving T2* Map")
        objWeasel.setMsgWindowProgBarMaxValue(4)   
        objWeasel.setMsgWindowProgBarValue(2)

        if magnitudePathList:
            T2StarImage = returnPixelArray(magnitudePathList, sliceList, echoList)
        else:
            objWeasel.displayMessageSubWindow("NOT POSSIBLE TO CALCULATE T2* MAP IN THIS SERIES.")
            raise Exception("Not possible to calculate T2* Map in the selected series.")

        if hasattr(readDICOM_Image.getDicomDataset(magnitudePathList[0]), 'PerFrameFunctionalGroupsSequence'):
            # If it's Enhanced MRI
            numImages = 1
            T2StarImageList = [T2StarImage]
            T2StarImageFilePath = saveDICOM_Image.returnFilePath(magnitudePathList[0], FILE_SUFFIX)
            T2StarImagePathList = [T2StarImageFilePath]
        else:
            # Iterate through list of images and save T2* for each image
            T2StarImagePathList = []
            T2StarImageList = []
            numImages = (1 if len(np.shape(T2StarImage)) < 3 else np.shape(T2StarImage)[0])
            for index in range(numImages):
                T2StarImageFilePath = saveDICOM_Image.returnFilePath(magnitudePathList[index], FILE_SUFFIX)
                T2StarImagePathList.append(T2StarImageFilePath)
                if numImages==1:
                    T2StarImageList.append(T2StarImage)
                else:
                    T2StarImageList.append(T2StarImage[index, ...])

        objWeasel.displayMessageSubWindow(
            "<H4>Saving {} DICOM files for the T2* Map calculated</H4>".format(numImages),
            "Saving T2* Map")
        objWeasel.setMsgWindowProgBarMaxValue(4)
        objWeasel.setMsgWindowProgBarValue(3)

        # Save new DICOM series locally
        saveDICOM_Image.saveDicomNewSeries(
            T2StarImagePathList, imagePathList, T2StarImageList, FILE_SUFFIX, parametric_map="T2Star")
        newSeriesID = objWeasel.insertNewSeriesInXMLFile(magnitudePathList[:len(T2StarImagePathList)],
                                                        T2StarImagePathList, FILE_SUFFIX)
        objWeasel.setMsgWindowProgBarValue(4)                                                    
        objWeasel.closeMessageSubWindow()
        objWeasel.displayMultiImageSubWindow(T2StarImagePathList,
                                             studyID, newSeriesID)
        objWeasel.refreshDICOMStudiesTreeView(newSeriesID)
    except Exception as e:
        print('Error in T2StarMapDICOM_Image.saveT2StarMapSeries: ' + str(e))
