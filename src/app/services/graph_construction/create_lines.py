from app.models.bounding_box import BoundingBox
from app.models.line_detection.line_segment import LineSegment
from shapely import Point, LineString


def create_line_from_boundingbox(boundingBox: BoundingBox, line: LineSegment) -> LineSegment:
    """
        Creates line from text node
        :param text: Text
        :param line: Line
        :return: Line
    """
    # Checking if line connected from the left of the text
    if line.startX < boundingBox.topX:
        return LineSegment(
            startX=line.endX,
            startY=line.endY,
            endX=line.endX + (boundingBox.bottomX - boundingBox.topX),
            endY=line.endY
        )
    # Checking if line connected from the right of the text
    elif line.endX > boundingBox.bottomX:
        return LineSegment(
            startX=line.startX - (boundingBox.bottomX - boundingBox.topX),
            startY=line.startY,
            endX=line.startX,
            endY=line.startY
        )
    # Checking if line connected from the top of the text
    elif line.startY < boundingBox.topY:
        return LineSegment(
            startX=line.endX,
            startY=line.endY,
            endX=line.endX,
            endY=line.endY + (boundingBox.bottomY - boundingBox.topY)
        )
    # Els line connected from the bottom of the text
    else:
        return LineSegment(
            startX=line.startX,
            startY=line.startY - (boundingBox.bottomY - boundingBox.topY),
            endX=line.startX,
            endY=line.startY
        )


def create_line_from_symbol(boundingBox: BoundingBox, line: LineSegment) -> LineSegment:
    """
        Creates line from symbol node
        :param text: Text
        :param line: Line
        :return: Line
    """
    # Checking if line connected from the left of the symbol
    if line.startX < boundingBox.topX:
        return LineSegment(
            startX=line.endX,
            startY=line.endY,
            endX=boundingBox.topX,
            endY=line.endY
        )
    # Checking if line connected from the right of the symbol
    elif line.endX > boundingBox.bottomX:
        return LineSegment(
            startX=boundingBox.bottomX,
            startY=line.startY,
            endX=line.startX,
            endY=line.startY
        )
    # Checking if line connected from the top of the symbol
    elif line.startY < boundingBox.topY:
        return LineSegment(
            startX=line.endX,
            startY=line.endY,
            endX=line.endX,
            endY=boundingBox.topY
        )
    # Els line connected from the bottom of the symbol
    else:
        return LineSegment(
            startX=line.startX,
            startY=boundingBox.bottomY,
            endX=line.startX,
            endY=line.startY
        )


def create_line_from_line(line1: LineSegment, line2: LineSegment) -> LineSegment:
    """
        create a line to connect two lines
        :param line1: LineSegment
        :param line: LineSegment
        :return: LineSegment
    """
    # Checking if line connected from the left of the text
    start_l1 = Point(line1.startX, line1.startY)
    end_l1 = Point(line1.endX, line1.endY)
    start_l2 = Point(line2.startX, line2.startY)
    end_l2 = Point(line2.endX, line2.endY)

    line_1 = LineString([(line1.startX, line1.startY), (line1.endX, line1.endY)])
    line_2 = LineString([(line2.startX, line2.startY), (line2.endX, line2.endY)])

    # We need to connect the lines from the closes points
    if start_l1.distance(line_2) < end_l1.distance(line_2):
        new_start = start_l1
    else:
        new_start = end_l1

    if start_l2.distance(line_1) < end_l2.distance(line_1):
        new_end = start_l2
    else:
        new_end = end_l2

    # make sure start point for thew new line is the most left/top point
    if new_start.x > new_end.x or (new_start.x == new_end.x and new_start.y > new_end.y):
        new_line = LineSegment(
            startX=new_end.x,
            startY=new_end.y,
            endX=new_start.x,
            endY=new_start.y
        )
    else:
        new_line = LineSegment(
            startX=new_start.x,
            startY=new_start.y,
            endX=new_end.x,
            endY=new_end.y
        )
    return new_line


def create_line_between_two_boundingbox(box1: BoundingBox, box2: BoundingBox) -> LineSegment:
    """
        create a line to connect two bounding boxes from their centers

        :param box1: BoundingBox
        :param box2: BoundingBox
        :return: LineSegment
    """
    return LineSegment(
        startX=(box1.topX + box1.bottomX) / 2,
        startY=(box1.topY + box1.bottomY) / 2,
        endX=(box2.topX + box2.bottomX) / 2,
        endY=(box2.topY + box2.bottomY) / 2)
