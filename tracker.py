import math
import time

class EuclideanDistTracker:
    def __init__(self):
        # Store the center positions of the objects
        self.center_points = {}
        # key: id, value: iterations
        self.still_counts = {}
        # Keep the count of the IDs
        # each time a new object id detected, the count will increase by one
        self.id_count = 0
        # number of iterations an object has been
        self.still_count = 0

    def update(self, objects_rect):  # list of [x, y, w, h] -> list of [x, y, w, h, id]
        # objects_rect is an array that consists of [x, y, w, h] arrays
        # Objects boxes and ids

        objects_bxs_ids = []
        # delay because otherwise the frames are too close together,
        # resulting in unnecessary still_count increments
        time.sleep(0.05)


        # Get center point of new object
        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            # Find out if that object was detected already
            same_object_detected = False
            for id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])

                if 1 < dist < 50:
                    self.center_points[id] = (cx, cy)
                    # print(self.center_points)
                    objects_bxs_ids.append([x, y, w, h, self.still_count, id])
                    same_object_detected = True
                    break

                elif dist <= 1:
                    # iterate the frame only when it's still!
                    self.still_counts[id] += 1
                    # still register the same center points and center points (object is still valid)
                    self.center_points[id] = (cx, cy)
                    # print(self.center_points)
                    objects_bxs_ids.append([x, y, w, h, self.still_count, id])
                    same_object_detected = True
                    break


            # New object is detected we assign the ID to that object
            if same_object_detected is False:
                self.center_points[self.id_count] = (cx, cy)
                objects_bxs_ids.append([x, y, w, h, self.still_count, self.id_count])
                self.still_counts[self.id_count] = 0
                self.id_count += 1

        # Clean the dictionary by center points to remove IDS not used anymore
        new_center_points = {}
        new_still_counts = {}

        # implement still_counts into objects_bxs_ids using dictionary indexing

        for obj_bx_id in objects_bxs_ids:
            _, _, _, _, _, object_id = obj_bx_id
            # updates the final element of the objects_box_ids: still_count
            obj_bx_id[4] = self.still_counts[object_id]

            center = self.center_points[object_id]
            new_center_points[object_id] = center

            n = self.still_counts[object_id]
            new_still_counts[object_id] = n

        # Update dictionary with IDs not used removed
        self.center_points = new_center_points.copy()
        self.still_counts = new_still_counts.copy()

        return objects_bxs_ids
