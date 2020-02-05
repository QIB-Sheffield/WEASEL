import os
import numpy as np
import math
import re
from skimage.transform import resize
import CoreModules.readDICOM_Image as readDICOM_Image
import CoreModules.saveDICOM_Image as saveDICOM_Image
#from Weasel import Weasel as weasel
from CoreModules.weaselToolsXMLReader import WeaselToolsXMLReader

FILE_SUFFIX = '_T2StarMap'


def returnPixelArray(imagePathList, sliceList, echoList):
    """Returns the T2* Map Array"""
    try:
        if os.path.exists(imagePathList[0]):
            # Could make a generic method - need to take the Multiframe into account
            dicomList = readDICOM_Image.getSeriesDicomDataset(imagePathList)
            imageList = []
            for individualDicom in dicomList:
                imageList.append(readDICOM_Image.getPixelArray(individualDicom))
            volumeArray = np.array(imageList)
            # Next step is to reshape to 3D or 4D - the squeeze makes it 3D if number of slices is =1
            # The transpose is applied here because the algorithm is developed this way
            imageArray = np.transpose(np.squeeze(np.reshape(volumeArray, (int(np.shape(volumeArray)[0]/len(sliceList)), len(sliceList), np.shape(volumeArray)[1], np.shape(volumeArray)[2]))))
            
            #Resample Data
            reconstPixel = 3
            fraction = reconstPixel / dicomList[0].PixelSpacing[0] 
            imageArray = resize(imageArray, (imageArray.shape[0] // fraction, imageArray.shape[1] // fraction, imageArray.shape[2], imageArray.shape[3]), anti_aliasing=True)

            # Algorithm / Don't forget to resample the 128x128 of GE
            pixelArray, _, _ = T2starmap(imageArray, echoList)
            pixelArray = np.transpose(pixelArray)

            del volumeArray, imageArray, imageList, dicomList
            return pixelArray
        else:
            return None
    except Exception as e:
        print('Error in function T2StarMapDICOM_Image.returnPixelArray: ' + str(e))


def T2starmap(imageArray, echoList):
    """
    Generates a T2* map from a series of volumes collected with different echo times.

    Parameters
    ----------
    imageArray : 4D/3D array
        A 4D/3D array containing the signal from each voxel at each echo time i.e. the dimensions of the array
        are [x, y, z, TE].
    echoList : Array
        An array of the echo times used for the last dimension of the raw data.

    Returns
    -------
    t2star : 3D array
        An array containing the T2* map generated by the function with T2* measured in milliseconds.
    m0 : 3D array
        An array containing the M0 map generated by the function.
    """
    import numpy as np
    imageArray[imageArray == 0] = 1E-10

    # If raw data is 2D (3D inc echo times) then add a dimension so it can be processed in the same way as 3D data
    if len(imageArray.shape) == 3:
        imageArray = np.expand_dims(imageArray, 2)

    t2star = np.zeros(imageArray.shape[0:3])
    r2star = np.zeros(imageArray.shape[0:3])
    m0 = np.zeros(imageArray.shape[0:3])
    with np.errstate(invalid='ignore', over='ignore'):
        for s in range(imageArray.shape[2]):
            for x in range(np.shape(imageArray)[0]):
                for y in range(np.shape(imageArray)[1]):
                    noise = 0.0
                    sd = 0.0
                    s_w = 0.0
                    s_wx = 0.0
                    s_wx2 = 0.0
                    s_wy = 0.0
                    s_wxy = 0.0
                    for d in range(imageArray.shape[3]):
                        noise = noise + imageArray[x, y, s, d]
                        sd = sd + imageArray[x, y, s, d] * imageArray[x, y, s, d]
                    noise = noise / imageArray.shape[3]
                    sd = sd / imageArray.shape[3] - noise ** 2
                    sd = sd ** 2
                    sd = np.sqrt(sd)
                    for d in range(imageArray.shape[3]):
                        te_tmp = echoList[d] * 0.001 # Conversion from ms to s
                        if imageArray[x, y, s, d] > sd:
                            sigma = np.log(imageArray[x, y, s, d] / (imageArray[x, y, s, d] - sd))
                            sig = imageArray[x, y, s, d]
                            weight = 1 / (sigma ** 2)
                        else:
                            sigma = np.log(imageArray[x, y, s, d] / 0.0001)
                            sig = np.log(imageArray[x, y, s, d])
                            weight = 1 / (sigma ** 2)
                        weight = 1 / (sigma ** 2)
                        s_w = s_w + weight
                        s_wx = s_wx + weight * te_tmp
                        s_wx2 = s_wx2 + weight * te_tmp ** 2
                        s_wy = s_wy + weight * sig
                        s_wxy = s_wxy + weight * te_tmp * sig
                    delta = (s_w * s_wx2) - (s_wx ** 2)
                    # Ask Charlotte about adding isinf and isnan
                    if (delta == 0.0) or (np.isinf(delta)) or (np.isnan(delta)):
                        t2star[x, y, s] = 0
                        r2star[x, y, s] = 0
                        m0[x, y, s] = 0
                    else:
                        a = (1 / delta) * (s_wx2 * s_wy - s_wx * s_wxy)
                        b = (1 / delta) * (s_w * s_wxy - s_wx * s_wy)
                        t2stars_temp = np.real(-1 / b)
                        r2stars_temp = np.real(-b)
                        m0_temp = np.real(np.exp(a))
                        if (t2stars_temp < 0) or (t2stars_temp > 500):
                            t2star[x, y, s] = 0
                            r2star[x, y, s] = 0
                            m0[x, y, s] = 0
                        else:
                            t2star[x, y, s] = t2stars_temp
                            r2star[x, y, s] = r2stars_temp
                            m0[x, y, s] = m0_temp
    return t2star, r2star, m0


def getParametersT2StarMap(imagePathList, seriesID):
    try:
        if os.path.exists(imagePathList[0]):
            # Sort by slice last place
            sortedSequenceEcho, echoList, numberEchoes = readDICOM_Image.sortSequenceByTag(imagePathList, "EchoTime")
            sortedSequenceSlice, sliceList, numSlices = readDICOM_Image.sortSequenceByTag(sortedSequenceEcho, "SliceLocation")
            phasePathList = []
            dicomList = readDICOM_Image.getSeriesDicomDataset(sortedSequenceSlice)
            for index, individualDicom in enumerate(dicomList):
                minValue = np.amin(readDICOM_Image.getPixelArray(individualDicom))
                maxValue = np.amax(readDICOM_Image.getPixelArray(individualDicom))
                if (numberEchoes == 12) and (minValue < 0) and (maxValue > 0) and (maxValue + minValue < 10) and (('P' in individualDicom.ImageType) or ('PHASE' in individualDicom.ImageType)) and (re.match(".*T2.*", seriesID) or re.match(".*t2.*", seriesID) or re.match(".*R2.*", seriesID) or re.match(".*r2.*", seriesID)):
                    phasePathList.append(imagePathList[index])

            del dicomList, numSlices, numberEchoes
            return phasePathList, echoList, sliceList
        else:
            return None, None, None
    except Exception as e:
        print('Error in function T2StarMapDICOM_Image.checkParametersT2StarMap: Not possible to calculate T2* Map' + str(e))


def saveT2StarMapSeries(objWeasel):
    try:
        #imagePathList, studyID, _ = weasel.getImagePathList_Copy()
        studyID = objWeasel.selectedStudy
        seriesID = objWeasel.selectedSeries
        imagePathList = \
            objWeasel.getImagePathList(studyID, seriesID)

        # Should insert Slice sorting before and echotime sorting after this
        phasePathList, echoList, sliceList = getParametersT2StarMap(imagePathList, seriesID)
        #print(phasePathList)
        if phasePathList:
            T2StarImage = returnPixelArray(phasePathList, sliceList, echoList)
        else:
            T2StarImage = []
            objWeasel.displayMessageSubWindow("NOT POSSIBLE TO CALCULATE T2* MAP IN THIS SERIES.")
            raise ValueError("NOT POSSIBLE TO CALCULATE T2* MAP IN THIS SERIES.")

        # Iterate through list of images and save T2* for each image
        T2StarImagePathList = []
        T2StarImageList = []
        numImages = len(phasePathList)
        objWeasel.displayMessageSubWindow(
            "<H4Saving {} DICOM files for T2* Map calculated</H4>".format(numImages),
            "Saving T2* Map into DICOM Images")
        objWeasel.setMsgWindowProgBarMaxValue(numImages)
        imageCounter = 0
        for index in range(np.shape(T2StarImage)[0]):
            T2StarImageFilePath = saveDICOM_Image.returnFilePath(phasePathList[index], FILE_SUFFIX)
            T2StarImagePathList.append(T2StarImageFilePath)
            T2StarImageList.append(T2StarImage[index, ...])
            imageCounter += 1
            objWeasel.setMsgWindowProgBarValue(imageCounter)

        objWeasel.closeMessageSubWindow()
        newSeriesID = objWeasel.insertNewSeriesInXMLFile(phasePathList[:len(T2StarImagePathList)],
                                                         T2StarImagePathList, FILE_SUFFIX)
        # Save new DICOM series locally
        saveDICOM_Image.save_dicom_newSeries(
            T2StarImagePathList, imagePathList, T2StarImageList, FILE_SUFFIX, parametric_map = "T2Star")
        objWeasel.displayMultiImageSubWindow(T2StarImagePathList,
                                             studyID, newSeriesID)
        objWeasel.refreshDICOMStudiesTreeView(newSeriesID)
    except Exception as e:
        print('Error in T2StarMapDICOM_Image.saveT2StarMapSeries: ' + str(e))
