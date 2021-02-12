import os
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.sequence import Sequence
import datetime
import copy
import random
import readDICOM_Image as readDICOM_Image


def calculateContourArray(dicomdata, roi):
    imageCoordinates = []
    realWorldCoordinates = []
    if "RectROI" in type(roi).__name__:
        pos_x, pos_y = roi.pos()
        #angle = roi.angle()
        size_x, size_y = roi.size()
        imageCoordinates = [pos_x, pos_y, 1]
    elif "CircleROI" in type(roi).__name__:
        pos_x, pos_y = roi.pos()
        #angle = roi.angle()
        size_x, size_y = roi.size()
    else:
        imageCoordinates = 1#roi.getPoints()
    
    contourArray = realWorldCoordinates

    return contourArray


def createNewRstructSingleDicom(dicomData, newFilePath, series_id=None, series_uid=None, list_refs=None):

    newDicom = FileDataset(newFilePath, {})

    # Generate Unique ID
    newDicom.SOPInstanceUID = pydicom.uid.generate_uid()
    newDicom.is_little_endian = True
    newDicom.is_implicit_VR = True

    # Series ID and UID
    if series_id is None:
        newDicom.SeriesNumber = int(str(dicomData.SeriesNumber) + str(random.randint(0, 999)))
    else:
        newDicom.SeriesNumber = series_id
    if series_uid is None:
        newDicom.SeriesInstanceUID = pydicom.uid.generate_uid()
    else:
        newDicom.SeriesInstanceUID = series_uid

    if len(dicomData.dir("SeriesDescription"))>0:
        newDicom.SeriesDescription = dicomData.SeriesDescription + "_ROI_STRUCT"
    elif len(dicomData.dir("SequenceName"))>0 & len(dicomData.dir("PulseSequenceName"))==0:
        newDicom.SeriesDescription = dicomData.SequenceName + "_ROI_STRUCT"
    elif len(dicomData.dir("SeriesDescription"))>0:
        newDicom.SeriesDescription = dicomData.SeriesDescription + "_ROI_STRUCT"
    elif len(dicomData.dir("ProtocolName"))>0:
        newDicom.SeriesDescription = dicomData.ProtocolName + "_ROI_STRUCT"
    else:
        newDicom.SeriesDescription = "NewSeries" + newDicom.SeriesNumber + "_ROI_STRUCT"

    newDicom.SOPClassUID = "1.2.840.10008.5.1.4.1.1.481.3"
    newDicom.StudyInstanceUID = dicomData.StudyInstanceUID
    newDicom.FrameOfReferenceUID = dicomData.SOPInstanceUID
    newDicom.Modality = "RTSTRUCT"
    newDicom.Manufacturer = "WEASEL"
    newDicom.SoftwareVersions = "0.1"
    newDicom.StructureSetName = "WEASEL" 
    newDicom.StructureSetLabel = "WEASEL"

    dt = datetime.datetime.now()
    timeStr = dt.strftime('%H%M%S')  # long format with micro seconds
    newDicom.SpecificCharacterSet = dicomData.SpecificCharacterSet
    newDicom.InstanceCreationDate = dt.strftime('%Y%m%d')
    newDicom.InstanceCreationTime = timeStr
    newDicom.StructureSetDate = dt.strftime('%Y%m%d')
    newDicom.StructureSetTime = timeStr
    newDicom.StudyDate = dicomData.StudyDate
    newDicom.StudyDate = dt.strftime('%Y%m%d')
    newDicom.StudyTime = dicomData.StudyTime
    newDicom.SeriesTime = timeStr

    newDicom.StudyID = dicomData.StudyID
    newDicom.StudyDescription = dicomData.StudyDescription
    newDicom.InstitutionName = dicomData.InstitutionName
    #newDicom.ReferringPhysicianName = dicomData.ReferringPhysicianName
    #newDicom.OperatorsName = dicomData.OperatorsName
    newDicom.PatientName = dicomData.PatientName
    newDicom.PatientID = dicomData.PatientID
    #newDicom.PatientSex = dicomData.PatientSex
    #newDicom.PatientBirthDate = dicomData.PatientBirthDate
    newDicom.PatientPosition = dicomData.PatientPosition


    # For now I will assume that there is only 1 ROI.
    # If there are multiple at some point, then:
    # for individual_roi in roi.getHandles(): individual_roi.mapToItem(imgItem, pos, ...)

    # Structure Set ROI Sequence
    structureSetRoiSequence = Sequence()
    newDicom.StructureSetROISequence = structureSetRoiSequence

    # Structure Set ROI Sequence: Structure Set ROI 1
    structureSetRoi1 = Dataset()
    structureSetRoi1.ROINumber = "1"
    structureSetRoi1.ReferencedFrameOfReferenceUID = dicomData.SOPInstanceUID
    structureSetRoi1.ROIName = 'KIDNEY'
    #structureSetRoi1.ROIDescription = type(roi).__name__
    #structureSetRoi1.ROIArea = [x,y,w,h] 
    structureSetRoi1.ROIGenerationAlgorithm = 'WEASEL-PYQTGRAPH'
    structureSetRoiSequence.append(structureSetRoi1)

    # ROI Contour Sequence
    roiContourSequence = Sequence()
    newDicom.ROIContourSequence = roiContourSequence

    # ROI Contour Sequence: ROI Contour 1
    roiContour1 = Dataset()
    roiContour1.ROIDisplayColor = ['128', '211', '52'] #  Can obtain this from roi.pen

    # Contour Sequence
    contourSequence = Sequence()
    roiContour1.ContourSequence = contourSequence

    # Contour Sequence: Contour 1
    contour1 = Dataset()
    contour1.ContourGeometricType = 'CLOSED_PLANAR'
    contour1.NumberOfContourPoints = "290" # len(calculateContourArray)/3
    contour1.ContourNumber = "1"
    contour1.ContourData = ['-27.063079834', '33.942630767', '101.703201293', '-27.063079834', '34.173683166', '102.681518554', '-28.068313599', '34.173683166', '102.681518554', '-29.073547364', '34.404735565', '103.659851074', '-29.073547364', '34.635791778', '104.638183593', '-30.078781128', '35.09790039', '106.594833374', '-31.084014893', '35.328948974', '107.573150634', '-31.084014893', '35.560005187', '108.551467895', '-31.084014893', '36.022109985', '110.508132934', '-31.084014893', '36.253166198', '111.486450195', '-31.084014893', '36.484218597', '112.464782714', '-32.089248658', '36.484218597', '112.464782714', '-32.089248658', '36.946323394', '114.421432495', '-32.089248658', '37.177379608', '115.399749755', '-33.094482422', '37.177379608', '115.399749755', '-34.099731446', '37.177379608', '115.399749755', '-35.104949952', '37.177379608', '115.399749755', '-36.110198975', '37.177379608', '115.399749755', '-36.110198975', '36.946323394', '114.421432495', '-37.11543274', '36.946323394', '114.421432495', '-38.120666504', '36.946323394', '114.421432495', '-39.125900269', '36.946323394', '114.421432495', '-40.131134034', '36.715270996', '113.443099975', '-41.136367798', '36.715270996', '113.443099975', '-42.141601563', '36.715270996', '113.443099975', '-42.141601563', '36.484218597', '112.464782714', '-43.146850586', '36.484218597', '112.464782714', '-44.152084351', '36.484218597', '112.464782714', '-45.157318116', '36.253166198', '111.486450195', '-46.16255188', '36.022109985', '110.508132934', '-46.16255188', '35.791057586', '109.529800415', '-48.17301941', '35.560005187', '108.551467895', '-48.17301941', '35.328948974', '107.573150634', '-49.178253174', '35.09790039', '106.594833374', '-50.183502198', '34.635791778', '104.638183593', '-51.188735962', '34.635791778', '104.638183593', '-51.188735962', '34.173683166', '102.681518554', '-52.193954468', '33.942630767', '101.703201293', '-53.199188233', '33.711578369', '100.724884033', '-53.199188233', '33.48052597', '99.746551513', '-53.199188233', '33.249469757', '98.768218994', '-54.204437256', '33.018417358', '97.789901733', '-54.204437256', '32.787361145', '96.811569213', '-56.214904786', '32.556308746', '95.833236694', '-56.214904786', '32.325256347', '94.854919433', '-57.220153809', '32.094203948', '93.876602172', '-57.220153809', '31.86315155', '92.898269653', '-59.23060608', '31.632095336', '91.919937133', '-59.23060608', '31.401042938', '90.941619873', '-60.235839844', '31.169990539', '89.963302612', '-61.241088868', '30.93893814', '88.984970092', '-62.246322632', '30.707881927', '88.006637573', '-62.246322632', '30.476829528', '87.028320312', '-63.251556397', '30.476829528', '87.028320312', '-63.251556397', '30.24577713', '86.049987792', '-64.256790162', '30.014720916', '85.071655273', '-65.262023926', '29.783672332', '84.093353271', '-66.267257691', '29.783672332', '84.093353271', '-67.272499085', '29.32156372', '82.136688232', '-68.277740479', '29.090507507', '81.158370971', '-69.282974244', '28.859455108', '80.180038452', '-70.288200379', '28.628402709', '79.201705932', '-71.293441773', '28.397350311', '78.223388671', '-72.298675538', '28.166297912', '77.245071411', '-74.309150696', '27.935241699', '76.266738891', '-75.31439209', '27.473133087', '74.310089111', '-76.319610596', '27.473133087', '74.310089111', '-77.32485199', '27.473133087', '74.310089111', '-77.32485199', '27.242080688', '73.331756591', '-78.330093384', '27.242080688', '73.331756591', '-78.330093384', '27.011028289', '72.353439331', '-79.335327149', '26.779975891', '71.375106811', '-79.335327149', '26.548923492', '70.39678955', '-80.340560914', '26.317867279', '69.418457031', '-81.345794678', '26.08681488', '68.440124511', '-82.351028443', '25.855758666', '67.46180725', '-84.361503602', '25.393653869', '65.50515747', '-84.361503602', '25.16260147', '64.526824951', '-85.366744996', '25.16260147', '64.526824951', '-87.377204896', '24.700492858', '62.57017517', '-88.38244629', '24.469444274', '61.59185791', '-90.392913819', '24.007335662', '59.635208129', '-90.392913819', '23.776283264', '58.656890869', '-91.398155213', '23.54522705', '57.678558349', '-92.403396607', '23.314174652', '56.700241088', '-94.413856507', '23.083118438', '55.72189331', '-95.419097901', '22.852069854', '54.743576049', '-96.424331666', '22.621009826', '53.76524353', '-96.424331666', '22.158908843', '51.808609008', '-97.42956543', '22.158908843', '51.808609008', '-98.434799195', '21.92785263', '50.830276489', '-99.440040589', '21.465744018', '48.87361145', '-100.445266724', '21.465744018', '48.87361145', '-101.450508118', '21.003643035', '46.916976928', '-102.455749512', '21.003643035', '46.916976928', '-102.455749512', '20.541534423', '44.960327148', '-103.460975647', '20.541534423', '44.960327148', '-103.460975647', '20.31047821', '43.981994628', '-104.466217042', '20.079425811', '43.003677368', '-105.471450806', '19.848369598', '42.025329589', '-105.471450806', '19.386268615', '40.068710327', '-106.476684571', '19.386268615', '40.068710327', '-106.476684571', '18.924160003', '38.112045288', '-107.481918335', '18.69310379', '37.133712768', '-108.48715973', '18.462051391', '36.155395507', '-109.492393494', '17.999946594', '34.198745727', '-109.492393494', '17.537837982', '32.242080688', '-110.497627259', '17.306785583', '31.263763427', '-111.502868653', '17.075733184', '30.285446166', '-111.502868653', '16.844676971', '29.307113647', '-111.502868653', '16.613628387', '28.328796386', '-111.502868653', '16.382572174', '27.350463867', '-111.502868653', '16.151519775', '26.372146606', '-112.508102417', '15.920463562', '25.393798828', '-112.508102417', '15.689411163', '24.415481567', '-112.508102417', '15.227302551', '22.458831787', '-113.513336182', '15.227302551', '22.458831787', '-114.518569947', '14.765197753', '20.502182006', '-114.518569947', '14.534145355', '19.523864746', '-114.518569947', '14.303092956', '18.545547485', '-113.513336182', '14.303092956', '18.545547485', '-112.508102417', '14.303092956', '18.545547485', '-111.502868653', '14.303092956', '18.545547485', '-110.497627259', '14.303092956', '18.545547485', '-109.492393494', '14.303092956', '18.545547485', '-106.476684571', '14.303092956', '18.545547485', '-104.466217042', '14.303092956', '18.545547485', '-102.455749512', '14.303092956', '18.545547485', '-101.450508118', '14.303092956', '18.545547485', '-99.440040589', '14.303092956', '18.545547485', '-98.434799195', '14.303092956', '18.545547485', '-97.42956543', '14.303092956', '18.545547485', '-96.424331666', '14.303092956', '18.545547485', '-95.419097901', '14.303092956', '18.545547485', '-94.413856507', '14.303092956', '18.545547485', '-93.408622742', '14.303092956', '18.545547485', '-92.403396607', '14.303092956', '18.545547485', '-91.398155213', '14.303092956', '18.545547485', '-90.392913819', '14.303092956', '18.545547485', '-89.387680054', '14.303092956', '18.545547485', '-88.38244629', '14.303092956', '18.545547485', '-87.377204896', '14.303092956', '18.545547485', '-86.37197876', '14.303092956', '18.545547485', '-85.366744996', '14.303092956', '18.545547485', '-84.361503602', '14.303092956', '18.545547485', '-83.356262208', '14.303092956', '18.545547485', '-81.345794678', '14.303092956', '18.545547485', '-80.340560914', '14.303092956', '18.545547485', '-79.335327149', '14.534145355', '19.523864746', '-77.32485199', '14.534145355', '19.523864746', '-75.31439209', '14.534145355', '19.523864746', '-74.309150696', '14.534145355', '19.523864746', '-73.303909302', '14.534145355', '19.523864746', '-72.298675538', '14.534145355', '19.523864746', '-71.293441773', '14.534145355', '19.523864746', '-70.288200379', '14.534145355', '19.523864746', '-69.282974244', '14.534145355', '19.523864746', '-68.277740479', '14.534145355', '19.523864746', '-67.272499085', '14.534145355', '19.523864746', '-66.267257691', '14.534145355', '19.523864746', '-65.262023926', '14.534145355', '19.523864746', '-64.256790162', '14.534145355', '19.523864746', '-63.251556397', '14.534145355', '19.523864746', '-62.246322632', '14.534145355', '19.523864746', '-61.241088868', '14.534145355', '19.523864746', '-60.235839844', '14.534145355', '19.523864746', '-59.23060608', '14.534145355', '19.523864746', '-58.225372315', '14.534145355', '19.523864746', '-57.220153809', '14.534145355', '19.523864746', '-56.214904786', '14.534145355', '19.523864746', '-56.214904786', '14.765197753', '20.502182006', '-55.209671021', '14.765197753', '20.502182006', '-54.204437256', '14.765197753', '20.502182006', '-52.193954468', '15.227302551', '22.458831787', '-51.188735962', '15.227302551', '22.458831787', '-50.183502198', '15.458362579', '23.437179565', '-49.178253174', '15.689411163', '24.415481567', '-49.178253174', '15.920463562', '25.393798828', '-48.17301941', '15.920463562', '25.393798828', '-48.17301941', '16.151519775', '26.372146606', '-47.167785645', '16.382572174', '27.350463867', '-47.167785645', '16.613628387', '28.328796386', '-47.167785645', '16.844676971', '29.307113647', '-45.157318116', '16.844676971', '29.307113647', '-45.157318116', '17.075733184', '30.285446166', '-44.152084351', '17.075733184', '30.285446166', '-44.152084351', '17.306785583', '31.263763427', '-43.146850586', '17.537837982', '32.242080688', '-42.141601563', '17.768894195', '33.220428466', '-41.136367798', '17.999946594', '34.198745727', '-41.136367798', '18.231002807', '35.177078247', '-40.131134034', '18.462051391', '36.155395507', '-39.125900269', '18.462051391', '36.155395507', '-39.125900269', '18.69310379', '37.133712768', '-38.120666504', '18.69310379', '37.133712768', '-38.120666504', '18.924160003', '38.112045288', '-37.11543274', '19.386268615', '40.068710327', '-36.110198975', '19.617321014', '41.047027587', '-35.104949952', '19.617321014', '41.047027587', '-35.104949952', '19.848369598', '42.025329589', '-34.099731446', '20.079425811', '43.003677368', '-34.099731446', '20.31047821', '43.981994628', '-33.094482422', '20.541534423', '44.960327148', '-32.089248658', '20.772586822', '45.938644409', '-31.084014893', '21.003643035', '46.916976928', '-31.084014893', '21.465744018', '48.87361145', '-31.084014893', '21.696800231', '49.851959228', '-30.078781128', '21.92785263', '50.830276489', '-30.078781128', '22.158908843', '51.808609008', '-30.078781128', '22.389961242', '52.786926269', '-29.073547364', '22.389961242', '52.786926269', '-29.073547364', '22.621009826', '53.76524353', '-28.068313599', '22.621009826', '53.76524353', '-27.063079834', '22.852069854', '54.743576049', '-27.063079834', '23.083118438', '55.72189331', '-26.057830811', '23.314174652', '56.700241088', '-26.057830811', '23.54522705', '57.678558349', '-25.052597046', '23.776283264', '58.656890869', '-25.052597046', '24.007335662', '59.635208129', '-24.047363282', '24.238384246', '60.61352539', '-24.047363282', '24.469444274', '61.59185791', '-24.047363282', '24.700492858', '62.57017517', '-24.047363282', '24.931549072', '63.548522949', '-24.047363282', '25.16260147', '64.526824951', '-24.047363282', '25.393653869', '65.50515747', '-24.047363282', '25.624710083', '66.48348999', '-24.047363282', '25.855758666', '67.46180725', '-24.047363282', '26.08681488', '68.440124511', '-24.047363282', '26.317867279', '69.418457031', '-24.047363282', '26.548923492', '70.39678955', '-24.047363282', '26.779975891', '71.375106811', '-24.047363282', '27.011028289', '72.353439331', '-24.047363282', '27.242080688', '73.331756591', '-24.047363282', '27.473133087', '74.310089111', '-24.047363282', '27.7041893', '75.288406372', '-24.047363282', '27.935241699', '76.266738891', '-24.047363282', '28.166297912', '77.245071411', '-24.047363282', '28.397350311', '78.223388671', '-24.047363282', '28.628402709', '79.201705932', '-24.047363282', '28.859455108', '80.180038452', '-24.047363282', '29.090507507', '81.158370971', '-24.047363282', '29.32156372', '82.136688232', '-24.047363282', '29.783672332', '84.093353271', '-25.052597046', '30.014720916', '85.071655273', '-25.052597046', '30.476829528', '87.028320312', '-25.052597046', '30.707881927', '88.006637573', '-25.052597046', '31.169990539', '89.963302612', '-25.052597046', '31.401042938', '90.941619873', '-25.052597046', '31.86315155', '92.898269653', '-25.052597046', '32.094203948', '93.876602172', '-25.052597046', '32.325256347', '94.854919433', '-25.052597046', '32.556308746', '95.833236694', '-25.052597046', '33.249469757', '98.768218994', '-25.052597046', '34.173683166', '102.681518554', '-25.052597046', '34.404735565', '103.659851074', '-25.052597046', '34.866844177', '105.616500854', '-25.052597046', '35.09790039', '106.594833374', '-25.052597046', '35.328948974', '107.573150634', '-25.052597046', '35.560005187', '108.551467895', '-25.052597046', '35.791057586', '109.529800415', '-25.052597046', '36.253166198', '111.486450195', '-25.052597046', '36.484218597', '112.464782714', '-25.052597046', '36.715270996', '113.443099975', '-25.052597046', '36.946323394', '114.421432495', '-25.052597046', '37.177379608', '115.399749755', '-25.052597046', '37.870536804', '118.334732055', '-25.052597046', '38.101593017', '119.313049316', '-25.052597046', '38.332645416', '120.291381835', '-25.052597046', '38.563697814', '121.269714355', '-25.052597046', '38.794754028', '122.248031616', '-25.052597046', '38.563697814', '121.269714355', '-25.052597046', '38.332645416', '120.291381835', '-25.052597046', '38.101593017', '119.313049316', '-25.052597046', '37.870536804', '118.334732055', '-25.052597046', '37.63948822', '117.356414794', '-25.052597046', '37.408432006', '116.378082275', '-25.052597046', '36.946323394', '114.421432495', '-25.052597046', '36.715270996', '113.443099975', '-25.052597046', '36.484218597', '112.464782714', '-26.057830811', '36.484218597', '112.464782714', '-26.057830811', '36.253166198', '111.486450195', '-26.057830811', '36.022109985', '110.508132934', '-27.063079834', '36.022109985', '110.508132934', '-27.063079834', '35.791057586', '109.529800415', '-27.063079834', '35.560005187', '108.551467895', '-28.068313599', '35.560005187', '108.551467895', '-28.068313599', '35.328948974', '107.573150634', '-28.068313599', '35.09790039', '106.594833374', '-28.068313599', '34.866844177', '105.616500854', '-27.063079834', '33.942630767', '101.703201293']

    #calculateContourArray
    contourSequence.append(contour1)

    roiContour1.ReferencedROINumber = "1"
    roiContourSequence.append(roiContour1)

    # RT ROI Observations Sequence
    rtroiObservationsSequence = Sequence()
    newDicom.RTROIObservationsSequence = rtroiObservationsSequence

    # RT ROI Observations Sequence: RT ROI Observations 1
    rtroiObservations1 = Dataset()
    rtroiObservations1.ObservationNumber = "1"
    rtroiObservations1.ReferencedROINumber = "1"
    rtroiObservations1.ROIObservationLabel = "1"
    rtroiObservations1.ROIObservationDescription = "1"
    rtroiObservations1.RTROIInterpretedType = 'ORGAN'
    rtroiObservations1.ROIInterpreter = ""
    rtroiObservationsSequence.append(rtroiObservations1)

    pydicom.filewriter.dcmwrite(newFilePath, newDicom, write_like_original=True)

    return