import numpy as np

# calculate distance between two points
def distance(p1, p2):
    p1 = np.array(p1)
    p2 = np.array(p2)
    return np.linalg.norm(p1 - p2)

# calculate angle between three points (p1, p2, p3) with p2 as the vertex point
def angle(p1, p2, p3):
    p1 = np.array(p1)
    p2 = np.array(p2)
    p3 = np.array(p3)

    v1 = p1 - p2
    v2 = p3 - p2

    cos_theta = np.dot(v1, v2) / (
        np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6
    )

    return np.degrees(
        np.arccos(
            np.clip(cos_theta, -1.0, 1.0)
        )
    )

# calculate angle of a line defined by two points (p1, p2) with respect to the horizontal axis
def line_angle(p1, p2):
    p1 = np.array(p1)
    p2 = np.array(p2)

    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]

    return np.degrees(np.arctan2(dy, dx))
