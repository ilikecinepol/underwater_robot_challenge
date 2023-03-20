import cv2
import numpy as np

img = cv2.imread('star.png', 0)
ret, thresh = cv2.threshold(img, 127, 255, 0)  # Перевод в ч/б
small = cv2.resize(thresh, (0,0), fx=0.25, fy=0.25)
contours, hierarchy = cv2.findContours(small, 1, 2)

cnt = contours[0]
M = cv2.moments(cnt)

cx = int(M['m10']/M['m00'])
cy = int(M['m01']/M['m00'])

cnt = contours[0]
area = cv2.contourArea(cnt)
print(area)

perimeter = cv2.arcLength(cnt,True)
print(perimeter)

hull = cv2.convexHull(cnt, returnPoints = True)
print(hull)
for i in hull:
    # print(i[0][0])
    cv2.circle(small, (i[0][0], i[0][1]), 10, (0,0,255), 2)

print(cv2.isContourConvex(cnt))

x,y,w,h = cv2.boundingRect(cnt)
# cv2.rectangle(small,(x,y),(x+w,y+h),(0,255,0),2)

rows,cols = small.shape[:2]
[vx,vy,x,y] = cv2.fitLine(cnt, cv2.DIST_L2,0,0.01,0.01)
lefty = int((-x*vy/vx) + y)
righty = int(((cols-x)*vy/vx)+y)
cv2.line(small,(cols-1,righty),(0,lefty),(0,255,0),2)

cv2.imshow('thresh', small)
cv2.waitKey(0)

