import os
import re
import datetime
import numpy as np
import pydicom
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
import CoreModules.WEASEL.iBeatImport as iBeatImport


def get_files_info(scan_directory):
    """This method returns the number of files and subfolders in a folder. It doesn't mean that they are all DICOM.
    """
    try:
        number_files = 0
        number_folders = 0
        for _, sub_folders, file_list in os.walk(scan_directory):
            number_files += len(file_list)
            number_folders += len(sub_folders)
        if number_files == 0:
            raise FileNotFoundError('No files present in the selected folder')
        return number_files, number_folders
    except Exception as e:
        print('Error in WriteXMLfromDICOM.get_files_info: ' + str(e))


def atof(text):
    """ This function is auxiliary for the natural sorting of the paths names"""
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    float regex comes from https://stackoverflow.com/a/12643073/190597
    """
    return [atof(c) for c in re.split(r'[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)', text)]


def series_sort(elem):
    """
    This is a helper function that will be used in key argument of sorted()
    in order to sort the list of series by series number
    """
    # return int(elem.split("_")[-1]) # USE THIS IF %SeriesDescription_%SeriesNumber
    return int(elem.split("_")[0])


def scan_tree(scan_directory):
    """Recursively yield DirEntry objects for given directory."""
    for entry in os.scandir(scan_directory):
        if entry.is_dir(follow_symlinks=False):
            yield from scan_tree(entry.path)
        else:
            yield entry


def get_scan_data(scan_directory):
    """This method opens all DICOM files in the provided path recursively and saves 
        each file individually as a variable into a list/array.
    """
    try:
        list_paths = list()
        list_dicom = list()
        file_list = [item.path for item in scan_tree(scan_directory) if item.is_file()]
        file_list.sort(key=natural_keys)
        for filepath in file_list:
            try:
                list_tags = ['InstanceNumber', 'SOPInstanceUID', 'PixelData', 'FloatPixelData', 'DoubleFloatPixelData', 'AcquisitionTime',
                             'AcquisitionDate', 'SeriesTime', 'SeriesDate', 'PatientName', 'PatientID', 'StudyDate', 'StudyTime', 
                             'SeriesDescription', 'SequenceName', 'ProtocolName', 'SeriesNumber']
                dataset = pydicom.dcmread(filepath, force=True, specific_tags=list_tags)
                if (hasattr(dataset, 'InstanceNumber') and hasattr(dataset, 'SOPInstanceUID') and 
                    any(hasattr(dataset, attr) for attr in ['PixelData', 'FloatPixelData', 'DoubleFloatPixelData'])
                    and ('DIRFILE' not in filepath) and ('DICOMDIR' not in filepath)):
                    list_paths.extend([filepath])
                    list_dicom.extend([dataset])
            except:
                continue
        if len(list_dicom) == 0:
            raise FileNotFoundError(
                'No DICOM files present in the selected folder')

        return list_dicom, list_paths
    except Exception as e:
        print('Error in WriteXMLfromDICOM.get_scan_data: ' + str(e))


def get_study_series(dicom):
    try:
        if hasattr(dicom, 'PatientName'):
            subject = str(dicom.PatientName)
        elif hasattr(dicom, 'PatientID'):
            subject = str(dicom.PatientID)
        else:
            subject = "No Subject Name"
        study = str(dicom.StudyDate) + "_" + str(dicom.StudyTime).split(".")[0]
        if hasattr(dicom, "SeriesDescription"):
            sequence = str(dicom.SeriesDescription)
        elif hasattr(dicom, "SequenceName"):
            sequence = str(dicom.SequenceName)
        elif hasattr(dicom, "ProtocolName"):
            sequence = str(dicom.ProtocolName)
        else:
            sequence = "No Sequence Name"
        series_number = str(dicom.SeriesNumber)

        return subject, study, sequence, series_number
    except Exception as e:
        print('Error in WriteXMLfromDICOM.get_study_series: ' + str(e))


def build_dictionary(list_dicom):
    try:
        xml_dict = {}
        for file in list_dicom:
            subject, study, sequence, series_number = get_study_series(file)
            if subject not in xml_dict:
                xml_dict[subject] = defaultdict(list)
            xml_dict[subject][study].append(series_number + "_" + sequence)
        for subject in xml_dict:
            for study in xml_dict[subject]:
                xml_dict[subject][study] = sorted(np.unique(xml_dict[subject][study]), key=series_sort)
        return xml_dict
    except Exception as e:
        print('Error in WriteXMLfromDICOM.build_dictionary: ' + str(e))


def get_studies_series_iBEAT(list_dicom):
    try:
        xml_dict = defaultdict(list)
        for file in list_dicom:
            individualStudy, individualSeries = iBeatImport.getScanInfo(file)
            xml_dict[individualStudy].append(individualSeries)
        for study in xml_dict:
            xml_dict[study] = np.unique(xml_dict[study])

        return xml_dict
    except Exception as e:
        print('Error in WriteXMLfromDICOM.get_studies_series_iBEAT: ' + str(e))


def open_dicom_to_xml(xml_dict, list_dicom, list_paths):
    """This method opens all DICOM files in the given list and saves 
        information from each file individually to an XML tree/structure.
    """
    try:    
        DICOM_XML_object = ET.Element('DICOM')
        comment = ET.Comment('WARNING: PLEASE, DO NOT MODIFY THIS FILE \n This .xml file is automatically generated by a script that reads folders containing DICOM files. \n Any changes can affect the software\'s functionality, so do them at your own risk')
        DICOM_XML_object.append(comment)

        for subject in xml_dict:
            subject_element = ET.SubElement(DICOM_XML_object, 'subject')
            subject_element.set('id', subject)
            for study in xml_dict[subject]:
                study_element = ET.SubElement(subject_element, 'study')
                study_element.set('id', study)
                for series in xml_dict[subject][study]:
                    series_element = ET.SubElement(study_element, 'series')
                    series_element.set('id', series)

        for index, file in enumerate(list_dicom):
            subject, study, sequence, series_number = get_study_series(file)
            subject_search_string = "./*[@id='" + subject + "']"
            study_root = DICOM_XML_object.find(subject_search_string)
            study_search_string = "./*[@id='" + study + "']"
            series_root = study_root.find(study_search_string)
            series_search_string = "./*[@id='"+ series_number + "_" + sequence + "']"
            image_root = series_root.find(series_search_string)
            image_element = ET.SubElement(image_root, 'image')
            label = ET.SubElement(image_element, 'label')
            name = ET.SubElement(image_element, 'name')
            time = ET.SubElement(image_element, 'time')
            date = ET.SubElement(image_element, 'date')
            label.text = str(len(list(image_root.iter('image')))).zfill(6)
            name.text =  os.path.normpath(list_paths[index])
            
            # The next lines save the time and date to XML - They consider multiple/eventual formats
            if len(file.dir("AcquisitionTime"))>0:
                try:
                    time.text = datetime.datetime.strptime(file.AcquisitionTime, '%H%M%S').strftime('%H:%M')
                except:
                    time.text = datetime.datetime.strptime(file.AcquisitionTime, '%H%M%S.%f').strftime('%H:%M')
                date.text = datetime.datetime.strptime(file.AcquisitionDate, '%Y%m%d').strftime('%d/%m/%Y')
            elif len(file.dir("SeriesTime"))>0:
                # It means it's Enhanced MRI
                try:
                    time.text = datetime.datetime.strptime(file.SeriesTime, '%H%M%S').strftime('%H:%M')
                except:
                    time.text = datetime.datetime.strptime(file.SeriesTime, '%H%M%S.%f').strftime('%H:%M')
                date.text = datetime.datetime.strptime(file.SeriesDate, '%Y%m%d').strftime('%d/%m/%Y')
            else:
                time.text = datetime.datetime.strptime('000000', '%H%M%S').strftime('%H:%M')
                date.text = datetime.datetime.strptime('20000101', '%Y%m%d').strftime('%d/%m/%Y')
        return DICOM_XML_object
    except Exception as e:
        print('Error in WriteXMLfromDICOM.open_dicom_to_xml: ' + str(e))


def open_dicom_to_xml_iBEAT(xml_dict, list_dicom, list_paths):
    """This method opens all DICOM files in the given list and saves 
        information from each file individually to an XML tree/structure.
    """
    try:    
        DICOM_XML_object = ET.Element('DICOM')
        comment = ET.Comment('WARNING: PLEASE, DO NOT MODIFY THIS FILE \n This .xml file is automatically generated by a script that reads folders containing DICOM files. \n Any changes can affect the software\'s functionality, so do them at your own risk')
        DICOM_XML_object.append(comment)

        for study in xml_dict:
            study_element = ET.SubElement(DICOM_XML_object, 'study')
            study_element.set('id',study)
            for series in xml_dict[study]:
                series_element = ET.SubElement(study_element, 'series')
                series_element.set('id', series)

        for index, file in enumerate(list_dicom):
            study_search_string, series_search_string = iBeatImport.getScanInfo(file)
            study_search_string = "./*[@id='" + study_search_string + "']"
            series_search_string = "./*[@id='" + series_search_string + "']"
            series_root = DICOM_XML_object.find(study_search_string)
            image_root = series_root.find(series_search_string)
            image_element = ET.SubElement(image_root, 'image')
            name = ET.SubElement(image_element, 'name')
            time = ET.SubElement(image_element, 'time')
            date = ET.SubElement(image_element, 'date')
            name.text =  os.path.normpath(list_paths[index])
            # The next lines save the time and date to XML - They consider multiple/eventual formats
            if len(file.dir("AcquisitionTime"))>0:
                try:
                    time.text = datetime.datetime.strptime(file.AcquisitionTime, '%H%M%S').strftime('%H:%M')
                except:
                    time.text = datetime.datetime.strptime(file.AcquisitionTime, '%H%M%S.%f').strftime('%H:%M')
                date.text = datetime.datetime.strptime(file.AcquisitionDate, '%Y%m%d').strftime('%d/%m/%Y')
            elif len(file.dir("SeriesTime"))>0:
                # It means it's Enhanced MRI
                try:
                    time.text = datetime.datetime.strptime(file.SeriesTime, '%H%M%S').strftime('%H:%M')
                except:
                    time.text = datetime.datetime.strptime(file.SeriesTime, '%H%M%S.%f').strftime('%H:%M')
                date.text = datetime.datetime.strptime(file.SeriesDate, '%Y%m%d').strftime('%d/%m/%Y')
            else:
                time.text = datetime.datetime.strptime('000000', '%H%M%S').strftime('%H:%M')
                date.text = datetime.datetime.strptime('20000101', '%Y%m%d').strftime('%d/%m/%Y')
        return DICOM_XML_object
    except Exception as e:
        print('Error in WriteXMLfromDICOM.open_dicom_to_xml_iBEAT: ' + str(e))


def create_XML_file(DICOM_XML_object, scan_directory):
    """This method creates a new XML file with the based on the structure of the selected DICOM folder"""
    try:
        xmlstr = ET.tostring(DICOM_XML_object, encoding='utf-8')
        XML_data = minidom.parseString(xmlstr).toprettyxml(encoding="utf-8", indent="  ")
        filename = os.path.basename(os.path.normpath(scan_directory)) + ".xml"
        with open(os.path.join(scan_directory, filename), "wb") as f:
            f.write(XML_data)  
        return os.path.join(scan_directory, filename)
    except Exception as e:
        print('Error in WriteXMLfromDICOM.create_XML_file: ' + str(e))