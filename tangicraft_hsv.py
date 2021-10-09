import cv2
import numpy as np
from tracker import *
from grid_system import *

# 480 640
# dimensions of the screen

# Create tracker object
tracker = EuclideanDistTracker()


def nothing(x):
    pass


# p is the y coordinate and q is the x coordinate
def stack_block(p, q):
    heights[p][q] += 1


# if the [p][q] area does not see a block
def reset_block(p, q):
    heights[p][q] = -1


def get_height(p, q):
    return heights[p][q]


def add_single_json(dict, q, p, r):
    if q not in dict.keys():
        dict[q] = {}
    if r not in dict[q].keys():
        dict[q][r] = {}
    dict[q][r][p] = "ice"
    return dict


def remove_single_json(dict, q, p, r):
    # if q in dict.keys():
    #     if r in dict[q].keys():
    #         del dict[q][r]
    # return dict
    dict[q][r][p] = 'air'




#
# def configure_camera():
#     cap = cv2.VideoCapture(0)
#     cap1 = cv2.VideoCapture(1)
#
#     ret, frame0 = cap.read()
#     ret1, frame1 = cap1.read()
#
#     cv2.imshow('cam0', frame0)
#     cv2.imshow('cam1', frame1)
#
#     key = cv2.waitKey(0)
#
#         # if key == ord('l'):
#         #     break
#         # if key == ord('p'):
#         #     cv2.waitKey(-1)  # wait until any key is pressed
#
#     # cap.release()
#     cap1.release()
#     cv2.destroyAllWindows()


# Create a window
cv2.namedWindow('image')

# create trackbars for color change
# these represent the Hue values
cv2.createTrackbar('lowH', 'image', 0, 179, nothing)
cv2.createTrackbar('highH', 'image', 179, 179, nothing)

# saturation values
cv2.createTrackbar('lowS', 'image', 0, 255, nothing)
cv2.createTrackbar('highS', 'image', 255, 255, nothing)

# value values
cv2.createTrackbar('lowV', 'image', 0, 255, nothing)
cv2.createTrackbar('highV', 'image', 255, 255, nothing)

# INITIAL VARIABLES
# key: id
# value: (x, y, z) coordinates
permanent_objects = {}

# key: (x, y) coordinates
# value: height
xy_height = {}

# list of permanent objects' IDs
ids = []

# used for dilation/erosion/gradients
kernel = np.ones((3, 3), np.uint8)

# Creates an array that represents a topological graph.
# Each point represents the height (in blocks) at that point
side_length = 80
width, height = (480, 640)

heights = [[-1 for j in range(height // side_length + 1)] for i in range(width // side_length + 1)]

# iterations
gone_counter = [[0 for a in range(height // side_length + 1)] for b in range(width // side_length + 1)]
permanent_jsons = {}


def hsv_tracking():
    global permanent_jsons
    cap = cv2.VideoCapture(1)
    while (True):

        ret, frame = cap.read()

        # get current positions of the trackbars
        ilowH = cv2.getTrackbarPos('lowH', 'image')
        ihighH = cv2.getTrackbarPos('highH', 'image')
        ilowS = cv2.getTrackbarPos('lowS', 'image')
        ihighS = cv2.getTrackbarPos('highS', 'image')
        ilowV = cv2.getTrackbarPos('lowV', 'image')
        ihighV = cv2.getTrackbarPos('highV', 'image')

        # convert color to hsv because it is easy to track colors in this color model
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # max and min hsv values that I set using the trackbar
        # tracks blue cubes

        # # adjustable HSV trackbar values
        # based as of right now
        lower_blue = np.array([(91, 0, 77)])
        higher_blue = np.array([(179, 255, 255)])

        lower_purple = np.array([(59, 0, 91)])
        higher_purple = np.array([(179, 255, 255)])

        lower_green = np.array([(31, 0, 104)])
        higher_green = np.array([(63, 255, 255)])

        lower_yellow = np.array([(18, 170, 204)])
        higher_yellow = np.array([(131, 255, 255)])

        lower_orange = np.array([(0, 135, 175)])
        higher_orange = np.array([(13, 255, 255)])

        # lower_hsv = np.array([ilowH, ilowS, ilowV])
        # higher_hsv = np.array([ihighH, ihighS, ihighV])

        # dark lighting

        blue_mask = cv2.inRange(hsv, lower_blue, higher_blue)
        purple_mask = cv2.inRange(hsv, lower_purple, higher_purple)
        green_mask = cv2.inRange(hsv, lower_green, higher_green)
        yellow_mask = cv2.inRange(hsv, lower_yellow, higher_yellow)
        orange_mask = cv2.inRange(hsv, lower_orange, higher_orange)

        mask = blue_mask + purple_mask + green_mask + yellow_mask + orange_mask

        # Apply the mask on the image to extract the original color
        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=22)

        # exaggerates border between contours
        # avoids forming giant contours that mistake two small contours close to each other
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 3)
        ret2, sure_fg = cv2.threshold(dist_transform, 0.25 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        dilated = sure_fg

        # creates a brand new grid board per consecutive frame
        grid = Board(frame, dilated)
        copy = frame.copy()
        grid.draw_grid_lines(copy)

        contours = grid.get_contours()

        # list of all rectangles of valid objects on screen (being tracked)
        detections = []

        curr_jsons = {}

        for cnt in contours:
            area = cv2.contourArea(cnt)
            max_area = 8000
            min_area = 150
            if min_area <= area <= max_area:
                # extract x,y,w,h coordinates from bounding a contour
                x, y, w, h = cv2.boundingRect(cnt)

                # append these to the tracking program
                detections.append([x, y, w, h])

                # convert corner coordinates to center coordinates
                x, y = grid.tc_to_center(x, y, w, h)

                # get relative indexes of the x and y coordinates
                p, q = grid.get_center(x, y)
                x_ = q * side_length + side_length // 2
                y_ = p * side_length + side_length // 2

                # set the gone_counter to zero since it's no longer gone!
                gone_counter[p][q] = 0

                if (q, p) in xy_height.keys():
                    text2 = f"z: {xy_height[(q, p)]}"
                    r = xy_height[(q, p)]
                    curr_jsons = add_single_json(curr_jsons, q, p, r)
                    cv2.putText(copy, text2, (x_ - 15, y_ + 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2)

                    # draw a square around the contour
                    grid.draw_squares(copy, p, q, r)
                    text = f"({q}, {p})"
                    cv2.putText(copy, text, (x_ - 20, y_), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2)

                else:
                    text2 = "z: -"
                    r = '-'
                    curr_jsons = add_single_json(curr_jsons, q, p, r)
                    cv2.putText(copy, text2, (x_ - 15, y_ + 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2)

                    # draw a square around the contour
                    grid.draw_squares(copy, p, q, 0)
                    text = f"({q}, {p})"
                    cv2.putText(copy, text, (x_ - 20, y_), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2)

                text2 = f"current jsons: {curr_jsons}"
                cv2.putText(copy, text2, (20, 20), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2)

        cv2.imshow('copy', copy)

        # 2. OBJECT TRACKING
        # box_ids is an array of [x, y, w, h, id]
        box_ids = tracker.update(detections)

        for box_id in box_ids:
            x, y, w, h, n, id = box_id
            # Draw rectangle around the valid objects
            cv2.rectangle(frame, (x - 5, y - 5), (x + w + 5, y + h + 5), (0, 255, 0), 2)
            text = f"ID: {str(id)} cnt: {str(n)}"
            frame = cv2.putText(frame, text, (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 2)

        res = cv2.bitwise_and(frame, frame, mask=mask)

        # cv2.imshow('frame', frame)
        cv2.imshow('res', res)

        # box is a list of [x, y, w, h, counter, id]

        for box in box_ids:
            x, y, w, h, sc, id = box
            # convert corner coordinates to center coordinates
            x, y = grid.tc_to_center(x, y, w, h)
            # get relative indexes of the x and y coordinates

            if sc > 20 and id not in ids:
                ids.append(id)
                # q is the x value (grid notation)
                # p is the y value (grid notation)
                p, q = grid.get_center(x, y)

                # increments the height of the block by 1
                stack_block(p, q)

                # accesses the height of the (p, q) coordinate
                # get_height(p, q) indexes an array of initially zeros
                r = get_height(p, q)

                # adding key and values to permanent_objects dictionary
                permanent_objects[box[-1]] = (q, p, r)

                # q = x; r = y
                xy_height[(q, p)] = r
                # accumulates one to the initial array of zeros

                for key, value in permanent_objects.items():
                    # r is the z value
                    permanent_jsons = add_single_json(permanent_jsons, value[0], value[1], value[2])

                # permanent_objects is a dictionary whose keys are the permanent object's IDs
                # and the values are the (x, y, z) coordinates
                print(f"Permanent objects: {permanent_objects}")

                # xy_height is a dictionary whose keys are (x, y) of the permanent object
                # its values are the heights of the corresponding (x, y) point
                print(f"xy_height = {xy_height}")

                print(f"permanent jsons: {permanent_jsons}\n")

        dilated_circles = dilated.copy()

        for row in grid.centers:
            for center in row:
                x, y = center
                p, q = grid.get_center(x, y)
                # for debugging purposes, creates squares whos corners are white circles
                # if the dilated contour makes contact with at least a single corner, then it will be good
                # hl = half length of side length
                hl = 35
                # counts the number of frames that a grid does not have

                # this algorithm will work IF AND ONLY IF the contours are big enough (i.e. close enough to the camera)
                dilated_circles = cv2.circle(dilated_circles, (y, x), 1, (255, 0, 0), -1)
                dilated_circles = cv2.circle(dilated_circles, (y + hl, x + hl), 1, (255, 0, 0), -1)
                dilated_circles = cv2.circle(dilated_circles, (y, x + hl), 1, (255, 0, 0), -1)
                dilated_circles = cv2.circle(dilated_circles, (y + hl, x), 1, (255, 0, 0), -1)

                if y < dilated.shape[0] - hl and x < dilated.shape[1] - hl:
                    # if contour not visible in box grid then increment te cone_counter by one per frame
                    if int(dilated[y][x]) == 0 and int(dilated[y + hl][x + hl]) == 0 and int(
                            dilated[y][x + hl]) == 0 and int(dilated[y + hl][x]) == 0:
                        gone_counter[p][q] += 1
                    else:
                        continue
                # if the grid doesn't see a block for 20 frames,
                # reset the r to zero
                r = get_height(p, q)
                if gone_counter[p][q] > 30 and r != -1:
                    # sets corresponding height to zero
                    reset_block(p, q)

                    # ACTION 1: changes the display on the frame.copy() image
                    # if gone for 40 iterations, then the height of the (x, y) coordinate
                    # will be reset to -1
                    xy_height_keys = list(xy_height.keys())
                    xy_height_vals = list(xy_height.values())
                    if r in xy_height_vals:
                        pos = xy_height_vals.index(r)
                        desired_key = xy_height_keys[pos]
                        # test to see if permanent object is deleted
                        del xy_height[desired_key]

                    # ACTION 2: deletes the key value pair in the permanent objects list which influences
                    # permanent jsons dictionary
                    perm_obj_keys = list(permanent_objects.keys())
                    perm_obj_vals = list(permanent_objects.values())
                    perm_obj_vals_xy = [xy[0:2] for xy in perm_obj_vals]

                    if (q, p) in perm_obj_vals_xy:
                        while r > -1:
                            pos = perm_obj_vals.index((q, p, r))
                            desired_key = perm_obj_keys[pos]
                            # test to see if permanent object is deleted
                            print(f"deleting object # {desired_key}: ({q}, {p}, {r})")
                            print(f"perm obj before deleting: {permanent_objects}")
                            print(f"perm jsons before deleting: {permanent_jsons}")
                            del permanent_objects[desired_key]
                            remove_single_json(permanent_jsons, q, p, r)
                            # if len(permanent_jsons[q]) == 0:
                            #     del permanent_jsons[q]
                            # delete = [key for key in permanent_jsons if permanent_jsons[key] == {}]
                            # for key in delete:
                            #     del permanent_jsons[key]
                            print(f"perm obj after deleting: {permanent_objects}")
                            print(f"perm jsons after deleting: {permanent_jsons}\n")
                            r -= 1
        # cv2.imshow('dilated', dilated_circles)

        key = cv2.waitKey(1)
        if key == ord('l'):
            break
        if key == ord('p'):
            cv2.waitKey(-1)  # wait until any key is pressed

    print(f"[INFO] {len(permanent_objects)} permanent objects stored")
    print(permanent_objects)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # configure_camera()
    hsv_tracking()
