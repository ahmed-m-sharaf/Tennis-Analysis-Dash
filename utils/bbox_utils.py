def get_center_of_bbox(bbox):
    x1, y1, x2, y2 = bbox
    center_x = int((x1 + x2) / 2)
    center_y = int((y1 + y2) / 2)
    return (center_x, center_y)

def measure_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 # phisagourse
    return distance

def get_foot_position(bbox):
    x1, y1, x2, y2 = bbox
    foot_x = int((x1 + x2) / 2)
    foot_y = y2
    return (foot_x, foot_y)

def get_closest_keypoint_index(point, keypoints, keypoint_indices):
    closest_distance = float('inf')
    key_point_index = keypoint_indices[0]
    for keypoint_index in keypoint_indices:
        keypoint = keypoints[keypoint_index*2], keypoints[keypoint_index*2 + 1]
        distance = abs(point[1] - keypoint[1])
        if distance < closest_distance:
            closest_distance = distance
            key_point_index = keypoint_index
    return key_point_index

def get_height_of_bbox(bbox):
    x1, y1, x2, y2 = bbox
    height = y2 - y1
    return height

def measure_xy_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    distance_x = abs(x2 - x1)
    distance_y = abs(y2 - y1)
    return distance_x, distance_y
