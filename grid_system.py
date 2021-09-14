import cv2
import imutils
import numpy as np


class Board:
    # draws a frickin board around image
    def __init__(self, img, dilated):

        # converts xyz into json
        self.send_info = {}

        self.dilated = dilated

        # contours present in grid
        self.contours = self.get_contours()

        # width of largest cube in the frame's field of vision
        self.side_length = self.set_side_length()

        # dimensions of the frame
        # (x,y) = (480, 640)
        # dimensions of the screen
        self.width, self.height = img.shape[0], img.shape[1]

        # Creates an array with all the possible "drop points" on the board
        # Whatever is placed on the board will map to the closest center, to standardize where the blocks will map to in
        # Minecraft, which are the index set for top

        self.centers = [[(self.side_length // 2 + j * self.side_length,
                          self.side_length // 2 + i * self.side_length)
                         for j in range(self.height // self.side_length + 1)] for i in
                        range(self.width // self.side_length + 1)]

        # an array of arrays of the edges of the squares

        self.edges = [[(self.side_length * j, self.side_length * i)
                       for j in range(self.height // self.side_length + 1)]
                      for i in range(self.width // self.side_length + 1)]

        # Creates an array that represents a topological graph.
        # Each point represents the height (in blocks) at that point
        self.top = [[0 for j in range(self.height // self.side_length + 1)] for i in range(self.width // self.side_length + 1)]

        # Creates an array that represents a topological graph.
        # Each point represents the height (in blocks) at that point
        self.top = [[0 for j in range(self.height // self.side_length + 1)] for i in range(self.width // self.side_length + 1)]

    def add_single_json(self, q, p, r):
        if q not in self.send_info.keys():
            self.send_info[q] = {}
        if r not in self.send_info[q].keys():
            self.send_info[q][r] = {}
        self.send_info[q][r][p] = "wood"
        return self.send_info

    def set_side_length(self):
        self.side_length = 80
        return self.side_length


    # returns greatest width of the cube to a value used to create grid-lines
    def get_side_length(self):
        cnts = self.get_contours()
        ret = 0

        for c in cnts:

            x, y, w, h = cv2.boundingRect(c)

            # The temporary strategy is to find the maximum width among all quadrilateral contours
            if w > ret:
                ret = w

        # Only return the value if it's non-zero. Otherwise return None
        if ret != 0:
            return ret


    # Convert top corner coordinate to center coordinate
    def tc_to_center(self, x, y, w, h):
        return (x + (w // 2)), (y + (h // 2))

    # Get the index set mapped to the closest "drop point" based on (x, y) coordinates
    def get_center(self, x, y):
        # Update the board when new blocks come up
        for p in range(len(self.centers)):
            for q in range(len(self.centers[0])):
                # Determine where the block is based on which center it's closest to
                # Center is like a "drop point" -- see doc
                center = self.centers[p][q]
                x_diff = abs(center[0] - x)
                y_diff = abs(center[1] - y)

                # If within half of the width of the bounding box, then it is the closest point
                if x_diff <= self.side_length // 2 and y_diff <= self.side_length // 2:
                    return p, q

    
    def draw_grid_lines(self, img):
        # y values first aka rows ^
        for j in range(len(self.edges)):
            start_x, start_y = self.edges[j][0]
            end_x, end_y = self.edges[j][-1]

            img = cv2.line(img, (start_x, start_y), (end_x, end_y), (255,255,255), 4)

        for i in range(len(self.edges[0])):
            start_x, start_y = self.edges[0][i]
            end_x, end_y = self.edges[-1][i]

            img = cv2.line(img, (start_x, start_y), (end_x, end_y), (255,255,255), 4)


    # Draws a square around the given indicies of the centers
    def draw_squares(self, img, p, q, r):
        if p < len(self.edges)-1 or q < len(self.edges[0])-1:
            start_x, start_y = self.edges[p][q]
            end_x, end_y = start_x + self.side_length, start_y + self.side_length
            img = cv2.rectangle(img, (start_x, start_y), (end_x, end_y), (30*r, 60*r, r*30), 5 + r * 4)
        else:
            pass

    def get_contours(self):
        self.contours, _ = cv2.findContours(self.dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return self.contours

