# Todo list:
# 1. implement find parameters function.
# https://classroom.udacity.com/nanodegrees/nd013/parts/fbf77062-5703-404e-b60c-95b78b2f3f9e/modules/2b62a1c3-e151-4a0e-b6b6-e424fa46ceab/lessons/fd66c083-4ccb-4fe3-bda1-c29db76f50a0/concepts/1a96426f-9ea1-4ca0-bb41-9b2bafbaea3e
# Parameter Tuning in Scikit-learn
# Scikit-learn includes two algorithms for carrying out an automatic parameter search:
#
# GridSearchCV
# RandomizedSearchCV

# 2. use opencv HOG. It's faster.
import collections
heatmap_depth = 30
heatmaps = collections.deque(maxlen=heatmap_depth)

import matplotlib.image as mpimg
import numpy as np
import cv2
from skimage.feature import hog
import matplotlib.pyplot as plt
import glob
import time
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from skimage.feature import hog
import pickle
import time
from scipy.ndimage.measurements import label
import multiprocessing
# start_time = time.time()

# NOTE: the next import is only valid for scikit-learn version <= 0.17
# for scikit-learn >= 0.18 use:
# from sklearn.model_selection import train_test_split
from sklearn.cross_validation import train_test_split

import params
### TODO: Tweak these parameters and see how the results change.
#color_space = 'RGB' # Can be RGB, HSV, LUV, HLS, YUV, YCrCb
#color_space = 'HSV'
color_space = params.color_space
# HOG orientations
orient = params.orient
#pix_per_cell = 8 # HOG pixels per cell
# making it 4 to have more rect in find_cars
# HOG pixels per cell
pix_per_cell = params.pix_per_cell
cell_per_block = params.cell_per_block # HOG cells per block
hog_channel = params.hog_channel # Can be 0, 1, 2, or "ALL"
spatial_size = params.spatial_size # Spatial binning dimensions
hist_bins = params.hist_bins    # Number of histogram bins
spatial_feat = params.spatial_feat # Spatial features on or off
hist_feat = params.hist_feat # Histogram features on or off
hog_feat = params.hog_feat # HOG features on or off
y_start_stop = params.y_start_stop # Min and max in y to search in slide_window()

sample_size = params.sample_size
heatmap_threshold = params.heatmap_threshold

# Define a function to extract features from a single image window
# This function is very similar to extract_features()
# just for a single image rather than list of images
def single_img_features(img, color_space='RGB', spatial_size=(32, 32),
                        hist_bins=32, orient=9,
                        pix_per_cell=8, cell_per_block=2, hog_channel=0,
                        spatial_feat=True, hist_feat=True, hog_feat=True):
    #1) Define an empty list to receive features
    img_features = []
    #2) Apply color conversion if other than 'RGB'
    if color_space != 'RGB':
        if color_space == 'HSV':
            feature_image = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        elif color_space == 'LUV':
            feature_image = cv2.cvtColor(img, cv2.COLOR_RGB2LUV)
        elif color_space == 'HLS':
            feature_image = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)
        elif color_space == 'YUV':
            feature_image = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
        elif color_space == 'YCrCb':
            feature_image = cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
    else: feature_image = np.copy(img)
    #3) Compute spatial features if flag is set
    if spatial_feat == True:
        spatial_features = bin_spatial(feature_image, size=spatial_size)
        #4) Append features to list
        img_features.append(spatial_features)
    #5) Compute histogram features if flag is set
    if hist_feat == True:
        hist_features = color_hist(feature_image, nbins=hist_bins)
        #6) Append features to list
        img_features.append(hist_features)
    #7) Compute HOG features if flag is set
    if hog_feat == True:
        if hog_channel == 'ALL':
            hog_features = []
            for channel in range(feature_image.shape[2]):
                hog_features.extend(get_hog_features(feature_image[:,:,channel],
                                    orient, pix_per_cell, cell_per_block,
                                    vis=False, feature_vec=True))
        else:
            hog_features = get_hog_features(feature_image[:,:,hog_channel], orient,
                        pix_per_cell, cell_per_block, vis=False, feature_vec=True)
        #8) Append features to list
        img_features.append(hog_features)

    #9) Return concatenated array of features
    return np.concatenate(img_features)


# Define a function you will pass an image
# and the list of windows to be searched (output of slide_windows())
def search_windows(img, windows, clf, scaler, color_space='RGB',
                    spatial_size=(32, 32), hist_bins=32,
                    hist_range=(0, 256), orient=9,
                    pix_per_cell=8, cell_per_block=2,
                    hog_channel=0, spatial_feat=True,
                    hist_feat=True, hog_feat=True):

    #1) Create an empty list to receive positive detection windows
    on_windows = []
    #2) Iterate over all windows in the list
    for window in windows:
        #3) Extract the test window from original image
        test_img = cv2.resize(img[window[0][1]:window[1][1], window[0][0]:window[1][0]], (64, 64))
        #4) Extract features for that window using single_img_features()
        features = single_img_features(test_img, color_space=color_space,
                            spatial_size=spatial_size, hist_bins=hist_bins,
                            orient=orient, pix_per_cell=pix_per_cell,
                            cell_per_block=cell_per_block,
                            hog_channel=hog_channel, spatial_feat=spatial_feat,
                            hist_feat=hist_feat, hog_feat=hog_feat)

#        print('features shape: ',features.shape)
        #5) Scale extracted features to be fed to classifier
        test_features = scaler.transform(np.array(features).reshape(1, -1))
        #6) Predict using your classifier
        prediction = clf.predict(test_features)
        #7) If positive (prediction == 1) then save the window
        if prediction == 1:
            on_windows.append(window)
#            print('prediction == 1:')
        else:
#            print('no prediction')
            pass

    #8) Return windows for positive detections
    return on_windows


# Define a function to return HOG features and visualization
def get_hog_features(img, orient, pix_per_cell, cell_per_block,
                        vis=False, feature_vec=True):
    # Call with two outputs if vis==True
    if vis == True:
        features, hog_image = hog(img, orientations=orient,
                                  pixels_per_cell=(pix_per_cell, pix_per_cell),
                                  cells_per_block=(cell_per_block, cell_per_block),
                                  transform_sqrt=True,
                                  visualise=vis, feature_vector=feature_vec)
        return features, hog_image
    # Otherwise call with one output
    else:
        features = hog(img, orientations=orient,
                       pixels_per_cell=(pix_per_cell, pix_per_cell),
                       cells_per_block=(cell_per_block, cell_per_block),
                       transform_sqrt=True,
                       visualise=vis, feature_vector=feature_vec)
        return features

# # # the code in 28. Color Classify
# # # https://classroom.udacity.com/nanodegrees/nd013/parts/fbf77062-5703-404e-b60c-95b78b2f3f9e/modules/2b62a1c3-e151-4a0e-b6b6-e424fa46ceab/lessons/fd66c083-4ccb-4fe3-bda1-c29db76f50a0/concepts/be308636-742b-416a-8fcc-c6071865a11f
# Define a function to compute binned color features
def bin_spatial(img, size=(32, 32)):
    color1 = cv2.resize(img[:,:,0], size).ravel()
    color2 = cv2.resize(img[:,:,1], size).ravel()
    color3 = cv2.resize(img[:,:,2], size).ravel()
    return np.hstack((color1, color2, color3))


# Define a function to compute color histogram features
# NEED TO CHANGE bins_range if reading .png files with mpimg!
def color_hist(img, nbins=32, bins_range=(0, 256)):
    # Compute the histogram of the color channels separately
    channel1_hist = np.histogram(img[:,:,0], bins=nbins, range=bins_range)
    channel2_hist = np.histogram(img[:,:,1], bins=nbins, range=bins_range)
    channel3_hist = np.histogram(img[:,:,2], bins=nbins, range=bins_range)
    # Concatenate the histograms into a single feature vector
    hist_features = np.concatenate((channel1_hist[0], channel2_hist[0], channel3_hist[0]))
    # Return the individual histograms, bin_centers and feature vector
    return hist_features




def extract_features(imgs, color_space='RGB', orient=9, spatial_size=(32, 32), hist_bins=32,
                     pix_per_cell=8, cell_per_block=2, hog_channel='ALL',
                     bin_feature='Enabled',color_feature='Enabled'):
    features = []
    m_features=[]

    for file in imgs:
        image = mpimg.imread(file)
        if color_space != 'RGB':
            if color_space == 'HSV':
                feature_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            elif color_space == 'LUV':
                feature_image = cv2.cvtColor(image, cv2.COLOR_RGB2LUV)
            elif color_space == 'HLS':
                feature_image = cv2.cvtColor(image, cv2.COLOR_RGB2HLS)
            elif color_space == 'YUV':
                feature_image = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)
            elif color_space == 'YCrCb':
                feature_image = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
        else: feature_image = np.copy(image)

        # Call get_hog_features() with vis=False, feature_vec=True
        if hog_channel == 'ALL':
            hog_features = []
            for channel in range(feature_image.shape[2]):
                hog_features.append(get_hog_features(feature_image[:,:,channel],
                                    orient, pix_per_cell, cell_per_block,
                                    vis=False, feature_vec=True))
            hog_features = np.ravel(hog_features)
        else:
            hog_features = get_hog_features(feature_image[:,:,hog_channel], orient,
                        pix_per_cell, cell_per_block, vis=False, feature_vec=True)

        bin_features = []
        bin_features = bin_spatial (feature_image, size=spatial_size).ravel()

        color_features = []
        color_features = color_hist(feature_image, nbins=hist_bins).ravel()

        if (bin_feature=='Enabled' and color_feature =='Enabled'):
# Todo
#            m_features.append (np.hstack((bin_features, hog_features)))
            m_features.append (np.hstack((bin_features, color_features, hog_features)))

        elif (color_feature == 'Enabled'):
            m_features.append (np.hstack((color_features, hog_features,)))

        elif (bin_feature == 'Enabled'):
            m_features.append (np.hstack((bin_features, hog_features, color_features)))
        else:
            m_features.append (hog_features)

    return m_features



# Define a function that takes an image,
# start and stop positions in both x and y,
# window size (x and y dimensions),
# and overlap fraction (for both x and y)
def slide_window(img, x_start_stop=[None, None], y_start_stop=[None, None],
                    xy_window=(64, 64), xy_overlap=(0.5, 0.5)):
    # If x and/or y start/stop positions not defined, set to image size
    if x_start_stop[0] == None:
        x_start_stop[0] = 0
    if x_start_stop[1] == None:
        x_start_stop[1] = img.shape[1]
    if y_start_stop[0] == None:
        y_start_stop[0] = 0
    if y_start_stop[1] == None:
        y_start_stop[1] = img.shape[0]
    # Compute the span of the region to be searched
    xspan = x_start_stop[1] - x_start_stop[0]
    yspan = y_start_stop[1] - y_start_stop[0]
    # Compute the number of pixels per step in x/y
    nx_pix_per_step = np.int(xy_window[0]*(1 - xy_overlap[0]))
    ny_pix_per_step = np.int(xy_window[1]*(1 - xy_overlap[1]))
    # Compute the number of windows in x/y
    nx_buffer = np.int(xy_window[0]*(xy_overlap[0]))
    ny_buffer = np.int(xy_window[1]*(xy_overlap[1]))
    nx_windows = np.int((xspan-nx_buffer)/nx_pix_per_step)
    ny_windows = np.int((yspan-ny_buffer)/ny_pix_per_step)
    # Initialize a list to append window positions to
    window_list = []
    # Loop through finding x and y window positions
    # Note: you could vectorize this step, but in practice
    # you'll be considering windows one by one with your
    # classifier, so looping makes sense
    for ys in range(ny_windows):
        for xs in range(nx_windows):
            # Calculate window position
            startx = xs*nx_pix_per_step + x_start_stop[0]
            endx = startx + xy_window[0]
            starty = ys*ny_pix_per_step + y_start_stop[0]
            endy = starty + xy_window[1]

            # Append window position to list
            window_list.append(((startx, starty), (endx, endy)))
    # Return the list of windows
    return window_list

# # lecture 32. sliding window implementation.
# # https://classroom.udacity.com/nanodegrees/nd013/parts/fbf77062-5703-404e-b60c-95b78b2f3f9e/modules/2b62a1c3-e151-4a0e-b6b6-e424fa46ceab/lessons/fd66c083-4ccb-4fe3-bda1-c29db76f50a0/concepts/8e39c07e-afd5-4ba5-9204-8b44aa39285c
# Define a function to draw bounding boxes
def draw_boxes(img, bboxes, color=(0, 0, 255), thick=6):
    print('in draw_boxes' )
    ### TODO: Tweak these parameters and see how the results change.
    # HOG orientations
    orient = params.orient
    print('type params :', type(params), 'params :', params)
    print('orient :', orient)

    # Make a copy of the image
    imcopy = np.copy(img)
    # Iterate through the bounding boxes
    for bbox in bboxes:
        # Draw a rectangle given bbox coordinates
        cv2.rectangle(imcopy, bbox[0], bbox[1], color, thick)
    # Return the image copy with boxes drawn
    return imcopy



# def convert_color(img, conv='RGB2YCrCb'):
def convert_color(img, convto='YCrCb'): # conv='RGB2YCrCb'
    if 'YCrCb' == convto:
        return cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
    if 'LUV' == convto:
        return cv2.cvtColor(img, cv2.COLOR_RGB2LUV)
    if 'YUV' == convto:
        return cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    # if conv == 'RGB2YCrCb':
    #     return cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
    # if conv == 'BGR2YCrCb':
    #     return cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    # if conv == 'RGB2LUV':
    #     return cv2.cvtColor(img, cv2.COLOR_RGB2LUV)

def get_hog_features(img, orient, pix_per_cell, cell_per_block,
                        vis=False, feature_vec=True):
    # Call with two outputs if vis==True
    if vis == True:
        features, hog_image = hog(img, orientations=orient,
                                  pixels_per_cell=(pix_per_cell, pix_per_cell),
                                  cells_per_block=(cell_per_block, cell_per_block),
                                  transform_sqrt=False,
                                  visualise=vis, feature_vector=feature_vec)
        return features, hog_image
    # Otherwise call with one output
    else:
        features = hog(img, orientations=orient,
                       pixels_per_cell=(pix_per_cell, pix_per_cell),
                       cells_per_block=(cell_per_block, cell_per_block),
                       transform_sqrt=False,
                       visualise=vis, feature_vector=feature_vec)
        return features

def loadimageandfeatures():
    # todo: remove this!!!!!!!
    debug = 0
    # Read in car and non-car images
    cars = []
    notcars = []
    car_images = glob.glob('training_set/vehicles/GTI_MiddleClose/*.png')
    for image in car_images:
        cars.append(image)
    if 0 == debug:
        car_images = glob.glob('training_set/vehicles/GTI_Right/*.png')
        for image in car_images:
            cars.append(image)
        car_images = glob.glob('training_set/vehicles/GTI_Left/*.png')
        for image in car_images:
            cars.append(image)
        car_images = glob.glob('training_set/vehicles/GTI_Far/*.png')
        for image in car_images:
            cars.append(image)
        car_images = glob.glob('training_set/vehicles/KITTI_extracted/*.png')
        for image in car_images:
            cars.append(image)

    notcar_images = glob.glob('training_set/non-vehicles/GTI/*.png')
    for image in notcar_images:
        notcars.append(image)
    if 0 == debug:
        notcar_images = glob.glob('training_set/non-vehicles/Extras/*.png')
        for image in notcar_images:
            notcars.append(image)


    print('cars size : ', len(cars))
    print('notcars size : ', len(notcars))
    # Reduce the sample size because
    # if 1 == debug:
    # sample_size = 4000
    cars = cars[0:sample_size]
    notcars = notcars[0:sample_size]
    print('after sampled: ')
    print('cars size : ', len(cars))
    print('notcars size : ', len(notcars))

    car_features = extract_features(cars, color_space=color_space,
                            spatial_size=spatial_size, hist_bins=hist_bins,
                            orient=orient, pix_per_cell=pix_per_cell,
                            cell_per_block=cell_per_block,
                            hog_channel=hog_channel
    #                                , spatial_feat=spatial_feat, hist_feat=hist_feat, hog_feat=hog_feat
                                   )
    notcar_features = extract_features(notcars, color_space=color_space,
                            spatial_size=spatial_size, hist_bins=hist_bins,
                            orient=orient, pix_per_cell=pix_per_cell,
                            cell_per_block=cell_per_block,
                            hog_channel=hog_channel
    #                                   , spatial_feat=spatial_feat, hist_feat=hist_feat, hog_feat=hog_feat
                                      )

    print('car_features shape:, ', len(car_features) )
    return car_features, notcar_features

# get HOG features and train a classifier
def train_classifier():
    start_time = time.time()
    car_features, notcar_features = loadimageandfeatures()

    X = np.vstack((car_features, notcar_features)).astype(np.float64)
    # Fit a per-column scaler
    global X_scaler
    X_scaler = StandardScaler().fit(X)
    # Apply the scaler to X
    scaled_X = X_scaler.transform(X)

    print('X:, ', X.shape, ' X_scaler: ', X_scaler)
    # Define the labels vector
    y = np.hstack((np.ones(len(car_features)), np.zeros(len(notcar_features))))

    # Split up data into randomized training and test sets
    rand_state = np.random.randint(0, 100)
    X_train, X_test, y_train, y_test = train_test_split(
        scaled_X, y, test_size=0.2, random_state=rand_state)

    print('Using: ',orient,' orientations',pix_per_cell,
        'pixels per cell and', cell_per_block,'cells per block')
    print('Feature vector length:', len(X_train[0]))
    # Use a linear SVC
    svc = LinearSVC()
    # Check the training time for the SVC
    t=time.time()
    svc.fit(X_train, y_train)
    t2 = time.time()
    print(round(t2-t, 2), 'Seconds to train SVC...')
    # Check the score of the SVC
    print('Test Accuracy of SVC = ', round(svc.score(X_test, y_test), 4))
    # Check the prediction time for a single sample
    t=time.time()

    # after trainingm save the classifier and scaler
    with open('save/clf.pickle', 'wb') as f:
        pickle.dump(svc, f)
    with open('save/x_scaler.pickle', 'wb') as f:
        pickle.dump(X_scaler, f)

    elapsed_time = time.time() - start_time
    print('elapsed_time : ', elapsed_time )

    return svc


# example code from lecture 35. Hog Sub-sampling window search:
# https://classroom.udacity.com/nanodegrees/nd013/parts/fbf77062-5703-404e-b60c-95b78b2f3f9e/modules/2b62a1c3-e151-4a0e-b6b6-e424fa46ceab/lessons/fd66c083-4ccb-4fe3-bda1-c29db76f50a0/concepts/c3e815c7-1794-4854-8842-5d7b96276642

# Define a single function that can extract features using hog sub-sampling and make predictions
def find_cars(img, ystart, ystop, scale, svc, X_scaler, orient,
              pix_per_cell, cell_per_block, spatial_size, hist_bins, sample_window_cnt):


    #    print('in find_cars :', 'ystart: ', ystart, 'spatial_size: ', spatial_size)
    # array of rectangles where cars were detected
    rectangles = []
    draw_img = np.copy(img)
    # https://discussions.udacity.com/t/accuracy-of-svm-is-99-on-test-test-but-not-detecting-a-single-car-in-test-images/237614/5
    # Uncomment the following line if you extracted training
    # data from .png images (scaled 0 to 1 by mpimg) and the
    # image you are searching is a .jpg (scaled 0 to 255)
    img = img.astype(np.float32)/255

    # only need to search the lower part of image because cars normally don't fly.
    img_tosearch = img[ystart:ystop,:,:]
    ctrans_tosearch = convert_color(img_tosearch, convto = color_space)
    if scale != 1:
        imshape = ctrans_tosearch.shape
        ctrans_tosearch = cv2.resize(ctrans_tosearch, (np.int(imshape[1]/scale), np.int(imshape[0]/scale)))

    ch1 = ctrans_tosearch[:,:,0]
    ch2 = ctrans_tosearch[:,:,1]
    ch3 = ctrans_tosearch[:,:,2]

    # Define blocks and steps as above
    nxblocks = (ch1.shape[1] // pix_per_cell) - cell_per_block + 1
    nyblocks = (ch1.shape[0] // pix_per_cell) - cell_per_block + 1
    nfeat_per_block = orient*cell_per_block**2

    # 64 was the orginal sampling rate, with 8 cells and 8 pix per cell
    # todo: window, cells_per_step, should not be hard coded?
    # should edit code refer to this discussion:
    # https://discussions.udacity.com/t/hog-sub-sampling-window-search/235413/30?u=sun.pochin
# #    sample_window_cnt = 64
#     sample_window_cnt = 128
    nblocks_per_window = (sample_window_cnt // pix_per_cell) - cell_per_block + 1
#    cells_per_step = 2  # Instead of overlap, define how many cells to step
    cells_per_step = 1  # Instead of overlap, define how many cells to step
    nxsteps = (nxblocks - nblocks_per_window) // cells_per_step
    nysteps = (nyblocks - nblocks_per_window) // cells_per_step
    # print('nblocks_per_window : ', nblocks_per_window, ' nxsteps : ', nxsteps, ' nysteps : ', nysteps)

    # Compute individual channel HOG features for the entire image
    hog1 = get_hog_features(ch1, orient, pix_per_cell, cell_per_block, feature_vec=False)
    hog2 = get_hog_features(ch2, orient, pix_per_cell, cell_per_block, feature_vec=False)
    hog3 = get_hog_features(ch3, orient, pix_per_cell, cell_per_block, feature_vec=False)
    # print('hog2.shape : ', hog2.shape)

    for xb in range(nxsteps):
        for yb in range(nysteps):
            ypos = yb*cells_per_step
            xpos = xb*cells_per_step
            # Extract HOG for this patch
            # print(' ypos : ', ypos , ' nblocks_per_window : ', nblocks_per_window)
            hog_feat1 = hog1[ypos:ypos+nblocks_per_window, xpos:xpos+nblocks_per_window].ravel()
            hog_feat2 = hog2[ypos:ypos+nblocks_per_window, xpos:xpos+nblocks_per_window].ravel()
            hog_feat3 = hog3[ypos:ypos+nblocks_per_window, xpos:xpos+nblocks_per_window].ravel()
            hog_features = np.hstack((hog_feat1, hog_feat2, hog_feat3))

            xleft = xpos*pix_per_cell
            ytop = ypos*pix_per_cell

            # Extract the image patch, 64 x 64 is the shape of training set images.
            subimg = cv2.resize(ctrans_tosearch[ytop:ytop + sample_window_cnt, xleft:xleft + sample_window_cnt],
                (64,64))

            # Get color features
            spatial_features = bin_spatial(subimg, size=spatial_size)
            hist_features = color_hist(subimg, nbins=hist_bins)

            # Scale features and make a prediction
            test_features = X_scaler.transform(np.hstack((spatial_features, hist_features, hog_features)).reshape(1, -1))
            #test_features = X_scaler.transform(np.hstack((shape_feat, hist_feat)).reshape(1, -1))
            test_prediction = svc.predict(test_features)

            if test_prediction == 1:
                xbox_left = np.int(xleft*scale)
                ytop_draw = np.int(ytop*scale)
                win_draw = np.int(sample_window_cnt*scale)
                # print(' xbox_left : ', xbox_left, ' ytop_draw : ', ytop_draw, ' win_draw : ', win_draw)
                cv2.rectangle(draw_img,(xbox_left, ytop_draw+ystart),(xbox_left+win_draw,ytop_draw+win_draw+ystart),(0,0,255),6)
                rectangles.append(((xbox_left, ytop_draw+ystart),(xbox_left+win_draw,ytop_draw+win_draw+ystart)))

    return draw_img, rectangles


def add_heat(heatmap, bbox_list, debug = False):
    if debug:
        print('bbox_list len: ', len(bbox_list) )
    # Iterate through list of bboxes
    for box in bbox_list:
        # Add += 1 for all pixels inside each bbox
        # Assuming each "box" takes the form ((x1, y1), (x2, y2))
        heat_cor1 = box[0][1]
        heat_cor2 = box[1][1]
        heat_cor3 = box[0][0]
        heat_cor4 = box[1][0]
        heatmap[box[0][1]:box[1][1], box[0][0]:box[1][0]] += 1
        # if debug:
        #     print(' heat_cor1 : ', heat_cor1, ' heat_cor2 : ',heat_cor2, ' heat_cor3 : ',heat_cor3, ' heat_cor4 : ',heat_cor4)

    # Return updated heatmap
    return heatmap


def apply_threshold(heatmap, threshold):
    # Zero out pixels below the threshold
    heatmap[heatmap <= threshold] = 0
    # Return thresholded map
    return heatmap


def draw_labeled_bboxes(img, labels):
    # Iterate through all detected cars
    for car_number in range(1, labels[1]+1):
        # Find pixels with each car_number label value
        nonzero = (labels[0] == car_number).nonzero()
        # Identify x and y values of those pixels
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])
        # Define a bounding box based on min/max x and y
        bbox = ((np.min(nonzerox), np.min(nonzeroy)), (np.max(nonzerox), np.max(nonzeroy)))
        # Draw the box on the image
        cv2.rectangle(img, bbox[0], bbox[1], (255, 0, 0), 6)
    # Return the image
    return img

# create heatmap , sum them, and average them to get rid of false positives.
def makeheatmap(img, rect, heatmap_threshold, debug = False):
    heat = np.zeros_like(img[:,:,0]).astype(np.float)
#     print('heatmaps : ', heatmaps)
    heat = add_heat(heat, rect, debug)
    heatmaps.append(heat)
    heatmap_sum = sum(heatmaps)
#     print('heatmap_sum : ', heatmap_sum)
#     print('heatmap_sum.shape : ', heatmap_sum.shape)

    average = heatmap_sum / len(heatmaps)
    if debug:
        print('numpy.where( average > heatmap_threshold ) :',
            np.where( average > heatmap_threshold), ' \n ' ,
            average[np.where( average > heatmap_threshold) ] )
    thresholded = apply_threshold(average, heatmap_threshold)
    labels = label(average)

#     print('numpy.where( heatmap_sum > heatmap_threshold ) :',
#         np.where( heatmap_sum > heatmap_threshold), ' \n ' ,
#         heatmap_sum[np.where( heatmap_sum > heatmap_threshold) ] )
#     thresholded = apply_threshold(heatmap_sum, heatmap_threshold)
#     labels = label(thresholded)
#     print('numpy.where( thresholded > heatmap_threshold ) :', np.where( thresholded > heatmap_threshold), ' \n ',
#         thresholded[np.where( thresholded > heatmap_threshold) ] )

    if debug:
        print(labels[1], 'cars found')
#         print('labels: ', labels[0])
#         plt.imshow(labels[0], cmap='gray')
    # Visualize the heatmap when displaying
#    heatmap = np.clip(heat, 0, 255)
    heatmap = np.clip(thresholded, 0, 255)

    # Draw bounding boxes on a copy of the image
    draw_img = draw_labeled_bboxes(np.copy(img), labels)

    if debug:
#         # Display the image
# #         plt.imshow(draw_img)
#         fig = plt.figure()
#         plt.subplot(121)
#         plt.imshow(draw_img)
#         plt.title('Car Positions')
#         plt.subplot(122)
#         plt.imshow(heatmap, cmap='hot')
#         plt.title('Heat Map')
#         fig.tight_layout()
#         plt.show()
        plt.figure(figsize=(16, 16))
        plt.imshow(draw_img)
        plt.show()
        plt.figure(figsize=(16, 16))
        plt.imshow(heatmap, cmap='hot')
        plt.show()

    return draw_img
