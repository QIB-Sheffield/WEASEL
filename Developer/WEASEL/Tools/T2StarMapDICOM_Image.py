import os
import numpy as np
import re
import struct
import CoreModules.readDICOM_Image as readDICOM_Image
import CoreModules.saveDICOM_Image as saveDICOM_Image
from CoreModules.weaselToolsXMLReader import WeaselToolsXMLReader
from Developer.WEASEL.Tools.imagingTools import resizePixelArray, formatArrayForAnalysis

FILE_SUFFIX = '_T2StarMap'


def T2starmap(pixelArray, echoList):
    """
    Generates a T2* map from a series of volumes collected with different echo times.

    Parameters
    ----------
    pixelArray : 4D/3D array
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
    pixelArray[pixelArray == 0] = 1E-10

    # If raw data is 2D (3D inc echo times) then add a dimension so it can be processed in the same way as 3D data
    if len(pixelArray.shape) == 3:
        pixelArray = np.expand_dims(pixelArray, 2)

    t2star = np.zeros(pixelArray.shape[0:3])
    r2star = np.zeros(pixelArray.shape[0:3])
    m0 = np.zeros(pixelArray.shape[0:3])
    with np.errstate(invalid='ignore', over='ignore'):
        for s in range(pixelArray.shape[2]):
            for x in range(np.shape(pixelArray)[0]):
                for y in range(np.shape(pixelArray)[1]):
                    noise = 0.0
                    sd = 0.0
                    s_w = 0.0
                    s_wx = 0.0
                    s_wx2 = 0.0
                    s_wy = 0.0
                    s_wxy = 0.0
                    for d in range(pixelArray.shape[3]):
                        noise = noise + pixelArray[x, y, s, d]
                        sd = sd + pixelArray[x, y, s, d] * pixelArray[x, y, s, d]
                    noise = noise / pixelArray.shape[3]
                    sd = sd / pixelArray.shape[3] - noise ** 2
                    sd = sd ** 2
                    sd = np.sqrt(sd)
                    for d in range(pixelArray.shape[3]):
                        te_tmp = echoList[d] * 0.001 # Conversion from ms to s
                        if pixelArray[x, y, s, d] > sd:
                            sigma = np.log(pixelArray[x, y, s, d] / (pixelArray[x, y, s, d] - sd))
                            sig = pixelArray[x, y, s, d]
                            weight = 1 / (sigma ** 2)
                        else:
                            sigma = np.log(pixelArray[x, y, s, d] / 0.0001)
                            sig = np.log(pixelArray[x, y, s, d])
                            weight = 1 / (sigma ** 2)
                        weight = 1 / (sigma ** 2)
                        s_w = s_w + weight
                        s_wx = s_wx + weight * te_tmp
                        s_wx2 = s_wx2 + weight * te_tmp ** 2
                        s_wy = s_wy + weight * sig
                        s_wxy = s_wxy + weight * te_tmp * sig
                    delta = (s_w * s_wx2) - (s_wx ** 2)
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


def returnPixelArray(imagePathList, sliceList, echoList):
    """Returns the T2* Map Array"""
    try:
        if os.path.exists(imagePathList[0]):
            dataset = readDICOM_Image.getDicomDataset(imagePathList[0])
            if hasattr(dataset, 'PerFrameFunctionalGroupsSequence'): # For Enhanced MRI, sliceList is a list of indices
                volumeArray, sliceList, numberSlices = readDICOM_Image.getMultiframeBySlices(dataset, sliceList=sliceList, sort=True)
            else: # For normal DICOM, slicelist is a list of slice locations in mm.
                volumeArray = readDICOM_Image.returnSeriesPixelArray(imagePathList)
                numberSlices = len(sliceList)
            # The assumption is that volumeArray is 3D always/usually
            pixelArray = formatArrayForAnalysis(volumeArray, numberSlices, dataset, dimension='4D', transpose=True, resize=3) # The transpose is applied here because the T2* algorithm is developed this way
            # Algorithm 
            derivedImage, _, _ = T2starmap(pixelArray, echoList)
            derivedImage = np.transpose(derivedImage)

            del volumeArray, pixelArray, dataset
            return derivedImage
        else:
            return None
    except Exception as e:
        print('Error in function T2StarMapDICOM_Image.returnPixelArray: ' + str(e))


def getParametersT2StarMap(imagePathList, seriesID):
    """This method checks if the series in imagePathList meets the criteria to be processed and calculate T2* Map"""
    try:
        if os.path.exists(imagePathList[0]):
            # Sort by slice last place
            magnitudePathList = []
            datasetList = readDICOM_Image.getDicomDataset(imagePathList[0]) # even though it can be 1 file only, I'm naming datasetList due to consistency
            if hasattr(datasetList, 'PerFrameFunctionalGroupsSequence'):
                echoList = []
                sliceList = []
                numberEchoes = datasetList[0x20011014].value
                _, originalSliceList, numberSlices = readDICOM_Image.getMultiframeBySlices(datasetList)
                for index, dataset in enumerate(datasetList.PerFrameFunctionalGroupsSequence):
                    flagMagnitude = False
                    echo = dataset.MREchoSequence[0].EffectiveEchoTime
                    if hasattr(dataset.MRImageFrameTypeSequence[0], 'FrameType') and hasattr(dataset.MRImageFrameTypeSequence[0], 'ComplexImageComponent'):
                        if set(['M', 'MAGNITUDE']).intersection(set(dataset.MRImageFrameTypeSequence[0].FrameType)) or set(['M', 'MAGNITUDE']).intersection(set(dataset.MRImageFrameTypeSequence[0].ComplexImageComponent)):
                            flagMagnitude = True
                    if (numberEchoes == 12) and (echo != 0) and flagMagnitude and (re.match(".*t2.*", seriesID.lower()) or re.match(".*r2.*", seriesID.lower())):
                        sliceList.append(originalSliceList[index])
                        echoList.append(echo)
                if sliceList and echoList:
                    echoList = np.unique(echoList)
                    magnitudePathList = imagePathList
            else:
                sortedSequenceEcho, echoList, numberEchoes = readDICOM_Image.sortSequenceByTag(imagePathList, "EchoTime")
                sortedSequenceSlice, sliceList, numberSlices = readDICOM_Image.sortSequenceByTag(sortedSequenceEcho, "SliceLocation")
                datasetList = readDICOM_Image.getSeriesDicomDataset(sortedSequenceSlice)
                echoList = np.delete(echoList, np.where(echoList == 0.0))
                numberEchoes = len(echoList)
                for index, dataset in enumerate(datasetList):
                    flagMagnitude = False
                    echo = dataset.EchoTime
                    try: #MAG = 0; PHASE = 1; REAL = 2; IMAG = 3; # RawDataType_ImageType in GE - '0x0043102f'
                        if struct.unpack('h', dataset[0x0043102f].value)[0] == 0:
                            flagMagnitude = True
                    except: pass
                    if hasattr(dataset, 'ImageType'):
                        if set(['M', 'MAGNITUDE']).intersection(set(dataset.ImageType)):
                            flagMagnitude = True
                    if (numberEchoes == 12) and (echo != 0) and flagMagnitude and (re.match(".*t2.*", seriesID.lower()) or re.match(".*r2.*", seriesID.lower())):
                        magnitudePathList.append(imagePathList[index])
            del datasetList, numberSlices, numberEchoes, flagMagnitude
            return magnitudePathList, sliceList, echoList
        else:
            return None, None, None
    except Exception as e:
        print('Error in function T2StarMapDICOM_Image.getParametersT2StarMap: Not possible to calculate T2* Map' + str(e))


def saveT2StarMapSeries(objWeasel):
    """Main method called from WEASEL to calculate the T2* Map"""
    try:
        studyID = objWeasel.selectedStudy
        seriesID = objWeasel.selectedSeries
        imagePathList = \
            objWeasel.getImagePathList(studyID, seriesID)

        magnitudePathList, sliceList, echoList = getParametersT2StarMap(imagePathList, seriesID)
        if magnitudePathList:
            T2StarImage = returnPixelArray(magnitudePathList, sliceList, echoList)
        else:
            objWeasel.displayMessageSubWindow("NOT POSSIBLE TO CALCULATE T2* MAP IN THIS SERIES.")
            raise ValueError("NOT POSSIBLE TO CALCULATE T2* MAP IN THIS SERIES.")

        if hasattr(readDICOM_Image.getDicomDataset(magnitudePathList[0]), 'PerFrameFunctionalGroupsSequence'):
            # If it's Enhanced MRI
            objWeasel.displayMessageSubWindow(
                "<H4Saving 1 Enhanced DICOM file for T2* Map calculated</H4>",
                "Saving T2* Map into DICOM")
            objWeasel.setMsgWindowProgBarMaxValue(0)
            T2StarImageList = [T2StarImage]
            T2StarImageFilePath = saveDICOM_Image.returnFilePath(magnitudePathList[0], FILE_SUFFIX)
            T2StarImagePathList = [T2StarImageFilePath]
            objWeasel.setMsgWindowProgBarMaxValue(1)
        else:
            # Iterate through list of images and save T2* for each image
            T2StarImagePathList = []
            T2StarImageList = []
            numImages = len(magnitudePathList)
            objWeasel.displayMessageSubWindow(
                "<H4Saving {} DICOM files for T2* Map calculated</H4>".format(numImages),
                "Saving T2* Map into DICOM Images")
            objWeasel.setMsgWindowProgBarMaxValue(numImages)
            imageCounter = 0
            for index in range(np.shape(T2StarImage)[0]):
                T2StarImageFilePath = saveDICOM_Image.returnFilePath(magnitudePathList[index], FILE_SUFFIX)
                T2StarImagePathList.append(T2StarImageFilePath)
                T2StarImageList.append(T2StarImage[index, ...])
                imageCounter += 1
                objWeasel.setMsgWindowProgBarValue(imageCounter)

        objWeasel.closeMessageSubWindow()
        
        # Save new DICOM series locally
        saveDICOM_Image.saveDicomNewSeries(
            T2StarImagePathList, imagePathList, T2StarImageList, FILE_SUFFIX, parametric_map="T2Star")
        newSeriesID = objWeasel.insertNewSeriesInXMLFile(magnitudePathList[:len(T2StarImagePathList)],
                                                        T2StarImagePathList, FILE_SUFFIX)
        objWeasel.displayMultiImageSubWindow(T2StarImagePathList,
                                             studyID, newSeriesID)
        objWeasel.refreshDICOMStudiesTreeView(newSeriesID)
    except Exception as e:
        print('Error in T2StarMapDICOM_Image.saveT2StarMapSeries: ' + str(e))
