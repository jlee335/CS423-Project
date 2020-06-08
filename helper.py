def drawlines(img1,img2,lines,pts1,pts2):
    ''' img1 - image on which we draw the epilines for the points in img2
        lines - corresponding epilines '''
    r,c = img1.shape
    img1 = cv.cvtColor(img1,cv.COLOR_GRAY2BGR)
    img2 = cv.cvtColor(img2,cv.COLOR_GRAY2BGR)
    for r,pt1,pt2 in zip(lines,pts1,pts2):
        color = tuple(np.random.randint(0,255,3).tolist())
        x0, y0 = map(int, [0, -r[2] / r[1] ]) 
        x1, y1 = map(int, [c, -(r[2] + r[0] * c) / r[1] ]) 
        img1 = cv.line(img1, (x0,y0), (x1,y1), color,1)
        
        img1 = cv.circle(img1,tuple(pt1.astype(int)),5,color,-1)
        img2 = cv.circle(img2,tuple(pt2.astype(int)),5,color,-1)
    return (img1,img2)
# Find epilines corresponding to points in right image (second image) and
# drawing its lines on left image
def epipolar_draw():
    ptsR_2 = ptsR[:,0:2]
    ptsL_2 = ptsR[:,0:2]

    lines1 = cv.computeCorrespondEpilines(ptsR_2.reshape(-1,1,2), 2,F)
    lines1 = lines1.reshape(-1,3)

    (img5,img6) = drawlines(left,right,lines1,ptsL_2,ptsR_2)
    # Find epilines corresponding to points in left image (first image) and
    # drawing its lines on right image
    lines2 = cv.computeCorrespondEpilines(ptsL_2.reshape(-1,1,2), 1,F)
    lines2 = lines2.reshape(-1,3)

    (img3,img4) = drawlines(right,left,lines2,ptsR_2,ptsL_2)

    plt.figure(figsize = (40,20))

    plt.subplot(121),plt.imshow(img5)
    plt.subplot(122),plt.imshow(img3)
    plt.show()