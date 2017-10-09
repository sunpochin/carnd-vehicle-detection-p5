### TODO: Tweak these parameters and see how the results change.
#color_space = 'RGB' # Can be RGB, HSV, LUV, HLS, YUV, YCrCb
# color_space = 'HSV'
#color_space = 'HLS'
#color_space = 'YCrCb'
color_space = 'LUV'
orient = 9  # HOG orientations
pix_per_cell = 8 # HOG pixels per cell
# making it 4 to have more rect in find_cars
#pix_per_cell = 4 # HOG pixels per cell

cell_per_block = 2 # HOG cells per block

hog_channel = 'ALL' # Can be 0, 1, 2, or "ALL"

spatial_size = (16, 16) # Spatial binning dimensions

hist_bins = 16    # Number of histogram bins

spatial_feat = True # Spatial features on or off
hist_feat = True # Histogram features on or off
hog_feat = True # HOG features on or off
y_start_stop = [None, None] # Min and max in y to search in slide_window()
sample_size = 4000

xy_window=(64, 64)
xy_overlap=(0.8, 0.8)
