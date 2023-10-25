"""Bounding box methods useful for Amsterdam."""

from math import pi, cos
from django.contrib.gis.geos import GEOSGeometry, Point
from rest_framework.request import Request
from rest_framework.serializers import ValidationError

# Default Amsterdam bbox lon, lat, lon, lat
# square around Amsterdam.
BBOX = [52.03560, 4.58565,
        52.48769, 5.31360]


def parse_xyr(value: str) -> tuple[GEOSGeometry, float]:
    """Parse x, y, radius input."""
    try:
        x_str, y_str, radius_str = value.split(',')
    except ValueError:
        raise ValidationError(
            "Locatie must be rdx,rdy,radius(m) or lat,long,radius(m)"
        )

    try:
        x = float(x_str)
        y = float(y_str)
        radius = float(radius_str)
    except ValueError:
        raise ValidationError(
            "Locatie must be x: float, y: float, r: int"
        )

    # Checking if the given coords are in RD, otherwise converting
    if y > 10:
        point = Point(x, y, srid=28992).transform(4326, clone=True)
    else:
        radius = dist_to_deg(radius, x)
        point = Point(x, y, srid=4326)

    return point, radius


def dist_to_deg(distance: float, latitude: float) -> float:
    """
    Convert meters to degrees.

    distance = distance in meters, latitude = latitude in degrees

    At the equator, the distance of one degree is equal in latitude and longitude.
    at higher latitudes, a degree longitude is shorter in length, proportional to cos(latitude)
    http://en.wikipedia.org/wiki/Decimal_degrees
    This function is part of a distance filter where the database 'distance' is in degrees.
    There's no good single-valued answer to this problem.
    The distance/ degree is quite constant N/S around the earth (latitude),
    but varies over a huge range E/W (longitude).
    Split the difference: I'm going to average the the degrees latitude and degrees longitude
    corresponding to the given distance. At high latitudes, this will be too short N/S
    and too long E/W. It splits the errors between the two axes.
    Errors are < 25 percent for latitudes < 60 degrees N/S.
    """  # noqa
    #   d * (180 / pi) / earthRadius   ==> degrees longitude
    #   (degrees longitude) / cos(latitude)  ==> degrees latitude

    lat = latitude if latitude >= 0 else -1 * latitude
    rad2deg = 180 / pi
    earth_radius = 6378160.0
    latitude_correction = 0.5 * (1 + cos(lat * pi / 180))

    return distance / (earth_radius * latitude_correction) * rad2deg


def determine_bbox(request: Request) -> tuple[list[float] | None, str | None]:
    """Create a bounding box if it is given with the request."""
    if 'bbox' not in request.query_params:
        # set default value
        return BBOX, None

    bboxp = request.query_params['bbox']
    bbox, err = valid_bbox(bboxp)

    if err:
        return None, err

    return bbox, err


def valid_bbox(bboxp: str, srid: int = 4326) -> tuple[list[float], str | None]:
    """Check if bbox is a valid bounding box. (wgs84) for now.

    TODO write tests.
    """
    bbox_str = bboxp.split(',')
    err = None

    # check if we got 4 parameters
    if len(bbox_str) != 4:
        return [], "wrong numer of arguments (lon, lat, lon, lat)"

    # check if we got floats
    try:
        bbox = [float(f) for f in bbox_str]
    except ValueError:
        return [], "Did not recieve floats"

    # max bbox sizes from mapserver
    # RD  EXTENT      100000    450000   150000 500000
    # WGS             52.03560, 4.58565  52.48769, 5.31360
    lat_min = 52.03560
    lat_max = 52.48769
    lon_min = 4.58565
    lon_max = 5.31360

    if srid == 28992:
        # RD bbox from mapserver
        # 94000 465000 170000 514000
        lat_min = 465000
        lat_max = 514000
        lon_min = 94000
        lon_max = 170000

    # check if coorinates are withing amsterdam
    # lat1, lon1, lat2, lon2 = bbox

    # bbox given by leaflet
    lon1, lat1, lon2, lat2 = bbox

    if not lat_max >= lat1 >= lat_min:
        err = f"lat not within max bbox {lat_max} > {lat1} > {lat_min}"

    if not lat_max >= lat2 >= lat_min:
        err = f"lat not within max bbox {lat_max} > {lat2} > {lat_min}"

    if not lon_max >= lon2 >= lon_min:
        err = f"lon not within max bbox {lon_max} > {lon2} > {lon_min}"

    if not lon_max >= lon1 >= lon_min:
        err = f"lon not within max bbox {lon_max} > {lon1} > {lon_min}"

    # this is how the code expects the bbox
    # bbox = [lat1, lon1, lat2, lon2]
    bbox = [lon1, lat1, lon2, lat2]

    return bbox, err
