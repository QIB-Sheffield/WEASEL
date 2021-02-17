#**************************************************************************
# Template part of a tutorial 
# Inverts a number of selected images and saves them in a new series, 
# image by image and showing a progress bar
#***************************************************************************

def main(Weasel):
    ImageList = Weasel.Images()    # get the list of images checked by the user
    if ImageList.Empty(): return
    newSeries = ImageList.List[0].newSeriesFrom(ImageList.List, suffix="_Invert")
    for i, Image in ImageList.Enumerate(): # Loop over images and display a progress Bar
        Weasel.ProgressBar(max=ImageList.Count(), index=i+1, msg="Inverting image {}", title="Invert pixel values ")
        newImage = Image.new(series=newSeries)
        newImage.write(-Image.PixelArray, series=newSeries)
    Weasel.CloseProgressBar()   # Close the progress bar
    Weasel.Refresh(new_series_name=newSeries.seriesID)
    newSeries.DisplaySeries()      # Display all images in the list in a single display
    #newSeries.Display()            # Display all images in the list in a single display