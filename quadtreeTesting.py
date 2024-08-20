from quadtree import Quadtree, Rectangle, Point

if __name__ == "__main__":
    # Create a quadtree with a boundary covering the entire space
    boundary = Rectangle(0, 0, 100, 100)
    quadtree = Quadtree(boundary)

    # Create some points
    points = [
        Point([10, 10]),
        Point([20, 20]),
        Point([30, 30]),
        Point([40, 40]),
        Point([50, 50]),
        Point([60, 60]),
        Point([70, 70]),
        Point([80, 80]),
        Point([90, 90]),
    ]

    # Insert the points into the quadtree
    for point in points:
        quadtree.insert(point)

    # Query the quadtree for points within a region
    query_region = Rectangle(25, 25, 75, 75)
    query_results = quadtree.query(query_region)

    print("Points within the query region:")
    for point in query_results:
        print(point.position)

    # Update the position of a point
    point_to_update = points[0]
    point_to_update.position = [55, 55]
    quadtree.update(point_to_update)

    # Query the quadtree again for points within the same region
    query_results = quadtree.query(query_region)

    print("\nPoints within the query region after update:")
    for point in query_results:
        print(point.position)

    
    
    # bQ = quadtree.batchQuery(points, 20)
