import cv2
import numpy as np

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