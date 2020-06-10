# -*- coding: utf-8 -*-
"""Main.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xIgkXw2xK8muOoOIPGmwnwA9DUv7tnHd

@article{bailo2018efficient,
  title={Efficient adaptive non-maximal suppression algorithms for homogeneous spatial keypoint distribution},
  author={Bailo, Oleksandr and Rameau, Francois and Joo, Kyungdon and Park, Jinsun and Bogdan, Oleksandr and Kweon, In So},
  journal={Pattern Recognition Letters},
  volume={106},
  pages={53--60},
  year={2018},
  publisher={Elsevier}
}
"""

#!pip install opencv-python==3.4.2.17 opencv-contrib-python==3.4.2.17

#!pip install pyro-ppl

#from google.colab import drive
#drive.mount('/content/drive')

# this code section is from: https://github.com/BAILOOL/ANMS-Codes
# Adaptive Non-Maximal supression is used to evenly distribute feature points
import cv2 as cv
import sys
import numpy as np
import matplotlib.pyplot as plt
import argparse
from random import shuffle
import logging

import torch
import os
import pyro
import pyro.distributions as dist
import pyro.poutine as poutine
from pyro.infer import MCMC, NUTS
import pptk
#from google.colab.patches import cv2_imshow
import math
import copy
from ssc import *
from helper import *
import open3d as o3d



def ssc(keypoints, num_ret_points, tolerance, cols, rows):
    exp1 = rows + cols + 2 * num_ret_points
    exp2 = 4 * cols + 4 * num_ret_points + 4 * rows * num_ret_points + rows * rows + cols * cols - \
           2 * rows * cols + 4 * rows * cols * num_ret_points
    exp3 = math.sqrt(exp2)
    exp4 = num_ret_points - 1

    sol1 = -round(float(exp1 + exp3) / exp4)  # first solution
    sol2 = -round(float(exp1 - exp3) / exp4)  # second solution

    high = sol1 if (sol1 > sol2) else sol2  # binary search range initialization with positive solution
    low = math.floor(math.sqrt(len(keypoints) / num_ret_points))

    prev_width = -1
    selected_keypoints = []
    result_list = []
    result = []
    complete = False
    k = num_ret_points
    k_min = round(k - (k * tolerance))
    k_max = round(k + (k * tolerance))

    while not complete:
        width = low + (high - low) / 2
        if width == prev_width or low > high:  # needed to reassure the same radius is not repeated again
            result_list = result  # return the keypoints from the previous iteration
            break

        c = width / 2  # initializing Grid
        num_cell_cols = int(math.floor(cols / c))
        num_cell_rows = int(math.floor(rows / c))
        covered_vec = [[False for _ in range(num_cell_cols + 1)] for _ in range(num_cell_rows + 1)]
        result = []

        for i in range(len(keypoints)):
            row = int(math.floor(keypoints[i].pt[1] / c))  # get position of the cell current point is located at
            col = int(math.floor(keypoints[i].pt[0] / c))
            if not covered_vec[row][col]:  # if the cell is not covered
                result.append(i)
                # get range which current radius is covering
                row_min = int((row - math.floor(width / c)) if ((row - math.floor(width / c)) >= 0) else 0)
                row_max = int(
                    (row + math.floor(width / c)) if (
                            (row + math.floor(width / c)) <= num_cell_rows) else num_cell_rows)
                col_min = int((col - math.floor(width / c)) if ((col - math.floor(width / c)) >= 0) else 0)
                col_max = int(
                    (col + math.floor(width / c)) if (
                            (col + math.floor(width / c)) <= num_cell_cols) else num_cell_cols)
                for rowToCov in range(row_min, row_max + 1):
                    for colToCov in range(col_min, col_max + 1):
                        if not covered_vec[rowToCov][colToCov]:
                            # cover cells within the square bounding box with width w
                            covered_vec[rowToCov][colToCov] = True

        if k_min <= len(result) <= k_max:  # solution found
            result_list = result
            complete = True
        elif len(result) < k_min:
            high = width - 1  # update binary search range
        else:
            low = width + 1
        prev_width = width

    for i in range(len(result_list)):
        selected_keypoints.append(keypoints[result_list[i]])

    return selected_keypoints

"""First, load left and right (multiple images later on)"""

fx = 499.70
fy = 502.22
cx = 315.28
cy = 240.62
K = np.array([[fx , 0 , cx]  ,[0  ,fy , cy]  ,[0  ,0  ,1]])

dim = (1600,1200)




#1.Generating Keypoints for all images using ssc.
img_dir = os.getcwd() + '/images'

keypoints = []
descriptors = []
fn_list = os.listdir(img_dir)

print(img_dir)

sift = cv.xfeatures2d.SIFT_create()
for i, filename in enumerate(fn_list):
    img     = cv.imread(img_dir + '/' + filename,cv.IMREAD_GRAYSCALE)
    img     = cv.resize(img, dim, interpolation = cv.INTER_AREA)
    img     = cv.GaussianBlur(img,(5,5),1)
    kp      = sift.detect(img,None)
    shuffle(kp)  # simulating sorting by score with random shuffle
    s_kp = ssc(kp, 10000, 0.01, img.shape[1], img.shape[0])
    print(filename + ": found keypoints :" + str(len(s_kp)))
    keypoints.append(s_kp)
    s_kp2,des = sift.compute(img,s_kp)
    descriptors.append(des)


#2.Matching all image points and constructing D
D_list = []

#처음에는 desL == descriptors[0]
# ... matches 구함
# 두번째부터는 desL == 


kp_L = None
kp_R = None
match_list = [[]] #list of list 형태다

match_list = [[None]*len(keypoints) for _ in range(len(keypoints))]

for idx1,kp1 in enumerate(keypoints):
    des1 = descriptors[idx1]
    for idx2,kp2 in enumerate(keypoints):
        des2 = descriptors[idx2]

        if(idx2<=idx1):
            match_list[idx1][idx2]= None
        else:
            bf = cv.BFMatcher()
            matches = bf.knnMatch(des1,des2,k=2)

            pts1 = []
            pts2 = []
            for i,(m,n) in enumerate(matches):
                if m.distance < 0.7*n.distance: # == 서로 비슷하면
                    (x1,y1) = kp1[m.queryIdx].pt
                    (x2,y2) = kp2[m.trainIdx].pt
                    x1 = int(x1)
                    x2 = int(x2)
                    y1 = int(y1)
                    y2 = int(y2)

                    pts1.append((x1,y1))
                    pts2.append((x2,y2))
            #pts1 pts2 filled in
            match_list[idx1][idx2] = (pts1,pts2)

#match_list 완성, 




