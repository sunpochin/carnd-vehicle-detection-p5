## Udacity Vehicle Detection and Tracking Project
---

**Vehicle Detection Project**

The goals / steps of this project are the following:

* Perform a Histogram of Oriented Gradients (HOG) feature extraction on a labeled training set of images and train a classifier Linear SVM classifier
* Optionally, you can also apply a color transform and append binned color features, as well as histograms of color, to your HOG feature vector.
* Note: for those first two steps don't forget to normalize your features and randomize a selection for training and testing.
* Implement a sliding-window technique and use your trained classifier to search for vehicles in images.
* Run your pipeline on a video stream (start with the test_video.mp4 and later implement on full project_video.mp4) and create a heat map of recurring detections frame by frame to reject outliers and follow detected vehicles.
* Estimate a bounding box for vehicles detected.

[//]: # (Image References)
[image1]: ./examples/car_not_car.png
[image2]: ./examples/HOG_example.jpg
[image3]: ./examples/sliding_windows.jpg
[image4]: ./examples/sliding_window.jpg
[image5]: ./examples/bboxes_and_heat.png
[image6]: ./examples/labels_map.png
[image7]: ./examples/output_bboxes.png
[video1]: ./project_video.mp4

[image11]: ./eda/vehicle-and-non.png

[image12]: ./eda/noncars/image15.png

[image14]: ./eda/car-image-0040.png
[image16]: ./eda/noncars-16.png
[image17]: ./eda/search-1.png
[image18]: ./eda/search-2.png

[image21]: ./eda/findcars-1.png
[image22]: ./eda/findcars-1-heatmap.png
[image23]: ./eda/findcars-2.png
[image24]: ./eda/findcars-2-heatmap.png

## [Rubric](https://review.udacity.com/#!/rubrics/513/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.

You're reading it!

### Histogram of Oriented Gradients (HOG)

#### 1. Explain how (and identify where in your code) you extracted HOG features from the training images.

I started by reading in all the `vehicle` and `non-vehicle` images.  Here is an example of one of each of the `vehicle` and `non-vehicle` classes:

Images of vehicle and non-vehicle: ![alt text][image11]


I then explored different color spaces and different `skimage.hog()` parameters (`orientations`, `pixels_per_cell`, and `cells_per_block`).  I used images from each of the two classes and displayed them to get a feel for what the `skimage.hog()` output looks like.

Here is an example using the `YUV` color space and HOG parameters of `orientations=9`, `pixels_per_cell=(8, 8)` and `cells_per_block=(2, 2)`:

Vehicle image, image in YUV color space, HOG:

![alt text][image14]

non-vehicle image, image in YUV color space, HOG:

![alt text][image16]

The code used HOG is contained in `def loadimageandfeatures()` of the file `tool_functions.py`.
Codes in the cell `Decide if need to train a classifier or just load from previous model` will decide if it's needed to call `def train_classifier():` and `def loadimageandfeatures()` .

#### 2. Explain how you settled on your final choice of HOG parameters.

I started a pipeline with the parameters in the lectures: color_space = grayscale, pix_per_cell = 8, cell_per_block = 2, orient = 9.
Then I experimented with different color_space, 'HSV' and 'HLS' doesn't seem to work, while 'YCrCb' was able to produce a working but wobbly result:
 https://www.youtube.com/watch?v=Q98r-bd85Zw&feature=youtu.be&t=7s

I also experimented with `pix_per_cell`, it seems to have better results on `test_video.mp4` if I set `pix_per_cell = 4`, but it will make processing the whole project_video.mp4 very slow, which is bad for finding good parameters.

After I used the technique of `averaging heatmaps` to remove false positives, I used `pix_per_cell = 16` to have faster processing speed.

#### 3. Describe how (and identify where in your code) you trained a classifier using your selected HOG features (and color features if you used them).

I trained a linear SVM using all 3 features mentioned mentioned in the class: Spatial Binning of Color, Histograms of Color, and HOG.

The codes are in `def train_classifier()` and `def extract_features()`, training accuracy is above 98% .



### Sliding Window Search

#### 1. Describe how (and identify where in your code) you implemented a sliding window search.  How did you decide what scales to search and how much to overlap windows?

The codes are in `find_cars()` of `tool_functions.py`, it calls `bin_spatial()`, `color_hist()`, `get_hog_features()` to get color features and HOG features of a part of whole image frame, and use the SVM classifier trained to identify if it's a vehicle or non-vehicle image.

I settled with `scale = 1.5` and `cells_per_step = 1` by experimenting on test images. The following are results of 2 test images:
![alt text][image17]
![alt text][image18]


#### 2. Show some examples of test images to demonstrate how your pipeline is working.  What did you do to optimize the performance of your classifier?

Codes in `find_cars()` of `tool_functions.py` used HOG sub-sampling technique mentioned in the lectures. I tried to use multiprocessing to calculate HOG all 3 channels concurrently but didn't succeed.
Here are some example images:
![alt text][image21]
![alt text][image23]

---

### Video Implementation

#### 1. Provide a link to your final video output.  Your pipeline should perform reasonably well on the entire project video (somewhat wobbly or unstable bounding boxes are ok as long as you are identifying the vehicles most of the time with minimal false positives.)
Here's a [link to my video result](https://www.youtube.com/watch?v=CY7TenfbOJg)


#### 2. Describe how (and identify where in your code) you implemented some kind of filter for false positives and some method for combining overlapping bounding boxes.


To filter false positive, I used a deque to record 30 heatmaps, sum them and average them, them apply a threshold to identify real vehicle positions. The codes are in `makeheatmap()` .
![alt text][image21]
![alt text][image22]
![alt text][image23]
![alt text][image24]

---

### Discussion

#### 1. Briefly discuss any problems / issues you faced in your implementation of this project.  Where will your pipeline likely fail?  What could you do to make it more robust?

Here I'll talk about the approach I took, what techniques I used, what worked and why, where the pipeline might fail and how I might improve it if I were going to pursue this project further.  
