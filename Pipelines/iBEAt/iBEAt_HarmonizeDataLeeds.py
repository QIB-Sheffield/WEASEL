#**************************************************************************
# iBEAt - harmonize naming and structure of Series
# Leeds site
#***************************************************************************



def main(weasel):

    list_of_series = weasel.series() 
    
    # merge series with the same series number (needs a merge in place method)

    series_names = []                
    for i, series in list_of_series.enumerate():      
        weasel.progress_bar(max=list_of_series.length(), index=i+1, msg="Finding series name {}")
        series_names.append(iBEAt_series_name(series))

    series_names = iBEAt_series_names_update(series_names)

    for i, series in list_of_series.enumerate():      
        weasel.progress_bar(max=list_of_series.length(), index=i+1, msg="Renaming series {}")
        series.Item("SeriesDescription", series_names[i])

    weasel.refresh()            



def iBEAt_series_names_update(series_names): 
    """
    For some series the name must be extended
    """
    inject = series_names.index('DCE_kidneys_cor-oblique_fb')
    for i, name in enumerate(series_names[inject:]):
        if name[0:17] == 'T1w_abdomen_dixon': 
            series_names[inject+i] += '_post_contrast'

    asl = [i for i, x in enumerate(series_names) if x == 'ASL_kidneys_pCASL_cor-oblique_fb']
    nr_of_asl_series = int(len(asl)/5)
    for i in range(nr_of_asl_series):
        series_names[asl[5*i+0]] += '_M0_moco'
        series_names[asl[5*i+1]] += '_PW_moco'
        series_names[asl[5*i+2]] += '_RBF_moco'
        series_names[asl[5*i+3]] += '_control_moco'
        series_names[asl[5*i+4]] += '_label0_moco'

    return series_names
   


def iBEAt_series_name(series): 
    """
    The sequence names in Leeds have been removed by the anonymisation
    procedure and must be recovered from other attributes
    """
    ds = series.children[0].read()

    if ds.SequenceName == '*tfi2d1_192':
        if ds.FlipAngle > 30: 
            return 'localizer_bh_fix'
        else: 
            return 'localizer_bh_ISO'

    if ds.SequenceName == '*h2d1_320':
        return 'T2w_abdomen_haste_tra_mbh'

    if ds.SequenceName == '*fl3d2':
        sequence = 'T1w_abdomen_dixon_cor_bh'
        if ds.ImageType[3] == 'OUT_PHASE': return sequence + '_out_phase'
        if ds.ImageType[3] == 'IN_PHASE': return sequence + '_in_phase'
        if ds.ImageType[3] == 'FAT': return sequence + '_fat'
        if ds.ImageType[3] == 'WATER': return sequence + '_water'

    if ds.SequenceName == '*fl2d1r4':
        if ds.ImagePositionPatient[0] < 0:
            return 'PC_RenalArtery_Right_EcgTrig_fb_120'
        else: 
            return 'PC_RenalArtery_Left_EcgTrig_fb_120'

    if ds.SequenceName == '*fl2d1_v120in':
        if ds.ImagePositionPatient[0] < 0:
            sequence = 'PC_RenalArtery_Right_EcgTrig_fb_120'
        else:
            sequence = 'PC_RenalArtery_Left_EcgTrig_fb_120'
        if ds.ImageType[2] == 'MAG': return sequence + '_magnitude'
        if ds.ImageType[2] == 'P': return sequence + '_phase'

    if ds.SequenceName == '*fl2d12':
        if ds.InPlanePhaseEncodingDirection == 'COL':
            sequence = 'T2star_map_pancreas_tra_mbh'
        else:
            sequence = 'T2star_map_kidneys_cor-oblique_mbh'
        if ds.ImageType[2] == 'M': return sequence + '_magnitude'
        if ds.ImageType[2] == 'P': return sequence + '_phase'
        if ds.ImageType[2] == 'T2_STAR MAP': return sequence + '_T2star'

    if ds.SequenceName == '*fl2d1':
        sequence = 'T1w_kidneys_cor-oblique_mbh'
        if ds.ImageType[2] == 'M': return sequence + '_magnitude'
        if ds.ImageType[2] == 'P': return sequence + '_phase'

    if ds.SequenceName == '*tfl2d1r106': 
        sequence = 'T1map_kidneys_cor-oblique_mbh'
        if ds.ImageType[2] == 'T1 MAP': return sequence + '_T1map'
        if ds.ImageType[3] == 'MOCO': return sequence + '_moco'
        if ds.ImageType[2] == 'M': return sequence + '_magnitude'
        if ds.ImageType[2] == 'P': return sequence + '_phase'

    if ds.SequenceName == '*tfl2d1r96':
        sequence = 'T2map_kidneys_cor-oblique_mbh'
        if ds.ImageType[-1] == 'T2': return sequence + '_T2map'
        if ds.ImageType[-1] == 'MOCO': return sequence + '_moco'
        if ds.ImageType[2] == 'M': return sequence + '_magnitude'
        if ds.ImageType[2] == 'P': return sequence + '_phase'

    if ds.SequenceName[0:5] == '*ep_b':
        if series.numberChildren < 1000:
            return 'IVIM_kidneys_cor-oblique_fb '
        else:
            return 'DTI_kidneys_cor-oblique_fb '

    if ds.SequenceName == '*fl3d1':
        if ds.ScanOptions == 'PFP': 
            return 'MT_OFF_kidneys_cor-oblique_bh'
        else:
            return 'MT_ON_kidneys_cor-oblique_bh'

    if ds.SequenceName == '*tfi2d1_154': return 'ASL_planning_bh'
    if ds.SequenceName == 'tgse3d1_512': return 'ASL_kidneys_pCASL_cor-oblique_fb'
    if ds.SequenceName == '*tfl2d1_16': return 'DCE_kidneys_cor-oblique_fb'
    if ds.SequenceName == 'RAVE3d1': return 'RAVE_kidneys_fb'

    return 'Sequence not recognized'
    