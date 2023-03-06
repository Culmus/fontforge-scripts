import cv2
import numpy as np
import numpy.ma as ma

def AscenderMeanX(contour, x_height):
    x_height = int(x_height)
    contour = np.array(contour).astype(np.int32)

    contour_bbox = (np.amin(contour, axis=0), np.amax(contour, axis=0))
    canvas_size = (contour_bbox[1] - contour_bbox[0]).astype(np.uint32)
            
    # Create image to draw the glyph contour on. Note the flipped dimensions,
    # as required by OpenCV
    canvas = np.zeros((canvas_size[1], canvas_size[0]), dtype=np.uint8)
    canvas = cv2.fillPoly(canvas,[contour - contour_bbox[0]],1)

    # Compute the visual center of the ascender as a COM
    ascender = canvas[x_height:, :]
    center_of_mass = np.mean(np.nonzero(ascender), axis=1)

    # Horizontal COM location wrt glyph contour
    return center_of_mass[1] + contour_bbox[0][0]

# Find vertical shift which corresponds to the requred distance between
# the contours.
def StackAccents(contour1, contour2, distance):

    # In OpenCV and numpy first axis is vertical, in FontForge the first axis
    # is horizontal, so we need to swap x and y by horizontal flipping
    contour1 = np.fliplr(contour1).astype(np.int32)
    contour2 = np.fliplr(contour2).astype(np.int32)
    distance = int(distance)

    # Compute bounding boxes
    c_bb1 = np.vstack((np.amin(contour1, axis=0), np.amax(contour1, axis=0)))
    c_bb2 = np.vstack((np.amin(contour2, axis=0), np.amax(contour2, axis=0)))

    # Allocate canvas for both accent stacked with maximum gap, so that the
    # desired shift is present somewhere in-between.
    size_x = max(c_bb1[1,1], c_bb2[1,1]) - min(c_bb1[0,1], c_bb2[0,1])
    size_y = (c_bb1[1,0] - c_bb1[0,0]) + (c_bb2[1,0] - c_bb2[0,0]) + distance
    canvas = np.zeros((size_x, size_y), dtype=np.uint8)

    # Draw the first contour on the common canvas
    shift1 = (c_bb1[0,1] - min(c_bb1[0,1], c_bb2[0,1]), 0)
    filled = cv2.fillPoly(canvas,[contour1 - c_bb1[0] + shift1], 1)

    # Compute distance transform from the first contour
    dst_mat = cv2.distanceTransform(1-filled, cv2.DIST_L2, cv2.DIST_MASK_3)

    # Draw the second contour as a mask
    mask = np.zeros(np.flip(c_bb2[1]-c_bb2[0]), dtype=np.uint8)
    mask = cv2.fillPoly(mask,[contour2 - c_bb2[0]],1)
    mask = (1 - mask).astype(bool)

    distance_map = []
    # Iterate over all shifts from most negative (both contours at the bottom)
    # to the maximum distance (second contour above the first with suffcient gap)
    for i in reversed(range(-c_bb1[1,0] + c_bb1[0,0], distance)):
        shift2 = (c_bb2[0,1] - min(c_bb1[0,1], c_bb2[0,1]), (c_bb1[1,0] - c_bb1[0,0]) + i)

        # Extract the relevant range from the distance matrix
        dst_submat = dst_mat[shift2[0]:shift2[0] + mask.shape[0], shift2[1]:shift2[1] + mask.shape[1]]

        # Compute distance between contours as a minimum over all pixels of the
        # second filled contour from the first contour
        masked = ma.masked_array(dst_submat, mask=mask)
        l2_dist = masked.min()

        # Collect the shift with its calculated distance
        distance_map.append((i, l2_dist))

    # Find shift nearest to the required distance
    ii = sorted(distance_map, key = lambda x: abs(distance - x[1]))[0][0]

    return ii + (c_bb1[1,0] - c_bb2[0,0])