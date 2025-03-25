import tkinter as tk


# Instead of using regular integers for these values, lists are used because lists are mutable unlike ints.
CANVAS_WIDTH = [800]
CANVAS_HEIGHT = [800]


class GameObject:
    pass

class Node(GameObject):
    nodes = []
    last_clicked_node = None

    # Initialization, creates an id, places the node on the canvas and determines the coordinates of the centerpoint.
    def __init__(self, canvas, rx, ry, node_radius):

        # Converts given relative values to the actual coordinates on the canvas
        x1 = CANVAS_WIDTH[0] * rx / 1000 - node_radius / 2
        y1 = CANVAS_HEIGHT[0] * ry / 1000 - node_radius / 2
        x2 = CANVAS_WIDTH[0] * rx / 1000 + node_radius / 2
        y2 = CANVAS_HEIGHT[0] * ry / 1000 + node_radius / 2

        # Node attributes:
        self.already_used = False
        self.x = (x2 - x1) / 2 + x1  # These are the coordinates of the center point of the node.
        self.y = (y2 - y1) / 2 + y1
        self.id = canvas.create_oval(x1, y1, x2, y2, fill="white")
        pass

class Obstacle(GameObject):
    obstacles = []   # (Obstacles are also lines.)

    def __init__(self, canvas, rx1, ry1, rx2, ry2, obstacle_radius):

        # Given values are offsets, here they get turned to coordinates
        self.x1 = CANVAS_WIDTH[0] * rx1 / 1000
        self.y1 = CANVAS_HEIGHT[0] * ry1 / 1000
        self.x2 = CANVAS_WIDTH[0] * rx2 / 1000
        self.y2 = CANVAS_HEIGHT[0] * ry2 / 1000

        self.id = canvas.create_line(self.x1, self.y1, self.x2, self.y2, fill="#4e4e4e", width=obstacle_radius)
        pass

class ConnectorLine(GameObject):
    connector_lines = []

    def __init__(self, canvas, x1, y1, x2, y2, connector_line_radius):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        self.id = canvas.create_line(x1, y1, x2, y2, fill="white", width=connector_line_radius)
        pass

def lines_intersect(p1, p2, p3, p4):    # This function was not written by me
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    # Calculate the determinants
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if denominator == 0:
        return False  # Lines are parallel

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
    u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / denominator

    # Check if intersection is within the segments
    return 0 <= t <= 1 and 0 <= u <= 1


class Level:
    def __init__(self, canvas, obstacle_positions, node_positions, node_radius, lines_width):
        if obstacle_positions:
            for rx1, ry1, rx2, ry2 in obstacle_positions:
                new_obstacle = Obstacle(canvas, rx1, ry1, rx2, ry2, lines_width)
                Obstacle.obstacles.append(new_obstacle)


        for rx, ry in node_positions:
            Node.nodes.append(Node(canvas, rx, ry, node_radius))

class Game:

    def __init__(self, root, CANVAS_WIDTH, CANVAS_HEIGHT):

        # Creates canvas and basic deco
        self.canvas = tk.Canvas(root, width=CANVAS_WIDTH[0], height=CANVAS_HEIGHT[0], bg="black")
        self.canvas.pack()

        # These are the values that are relative to the screen size. Can and will be recalculated when toggling fullscreen
        # using self.recalc_values() function.
        self.lines_width = None
        self.node_radius = None
        self.circle_coords = [] # Deco circle

        self.recalc_values()

        self.circle_decoration = self.canvas.create_oval(self.circle_coords[0], self.circle_coords[1], self.circle_coords[2],
                                                         self.circle_coords[3], fill="gray")

        self.start_new_level()

        self.bind_events()  # Keybindings

        self.screen_height_value = root.winfo_screenheight()

    fullscreen = False
    def toggle_fullscreen(self, CANVAS_WIDTH, CANVAS_HEIGHT):
        # (ConnectorLine.connector_lines contains ConnectorLine objects. )
        # Before clearing the game state, creates a copies that can be worked with later.
        local_connector_lines = [i for i in ConnectorLine.connector_lines]
        local_nodes = [i for i in Node.nodes]
        local_last_clicked_node = Node.last_clicked_node

        previous_width = CANVAS_WIDTH[0]
        if self.fullscreen:
            root.attributes("-fullscreen", False)

            CANVAS_WIDTH[0] = 800
            CANVAS_HEIGHT[0] = 800

            self.fullscreen = False
        else:
            root.attributes("-fullscreen", True)

            CANVAS_WIDTH[0] = self.screen_height_value
            CANVAS_HEIGHT[0] = self.screen_height_value

            self.fullscreen = True

        # Resizes canvas
        self.canvas.config(width=CANVAS_WIDTH[0], height=CANVAS_HEIGHT[0])

        # Recalculates values that are relative to the screen size
        self.recalc_values()

        # Resizes circle decoration.
        self.canvas.coords(self.circle_decoration, self.circle_coords[0], self.circle_coords[1], self.circle_coords[2],
                           self.circle_coords[3])

        # Starting a new level initializes nodes and obstacles, but nodes' attrs aren't correct yet.
        self.current_level -= 1
        self.start_new_level()

        # Sets up last_clicked_node variable
        if local_last_clicked_node:
            Node.last_clicked_node = local_last_clicked_node

            # These two lines ensure connector lines after the toggle will be in their right position.
            Node.last_clicked_node.x = Node.last_clicked_node.x * CANVAS_WIDTH[0] / previous_width
            Node.last_clicked_node.y = Node.last_clicked_node.y * CANVAS_WIDTH[0] / previous_width

        # Every node that was used prior will have its already_used attr set to True.
        for index, node in enumerate(Node.nodes):
            node.already_used = local_nodes[index].already_used

        # If there are connector lines, it initializes them and fills up connector_lines list
        if local_connector_lines:
            for connector_line in local_connector_lines:
                nx1 = connector_line.x1 * CANVAS_WIDTH[0] / previous_width
                ny1 = connector_line.y1 * CANVAS_WIDTH[0] / previous_width
                nx2 = connector_line.x2 * CANVAS_WIDTH[0] / previous_width
                ny2 = connector_line.y2 * CANVAS_WIDTH[0] / previous_width
                new_connector_line = ConnectorLine(self.canvas, nx1, ny1, nx2, ny2, self.lines_width)
                ConnectorLine.connector_lines.append(new_connector_line)


    def recalc_values(self):

        self.lines_width = CANVAS_WIDTH[0] / 40

        self.node_radius = CANVAS_WIDTH[0] * 3 / 40

        # Values of the circle that is for decoration
        circle_x1 = round(CANVAS_WIDTH[0] / 8)
        circle_y1 = round(CANVAS_HEIGHT[0] / 8)
        circle_x2 = round(CANVAS_WIDTH[0] / 8 * 7)
        circle_y2 = round(CANVAS_HEIGHT[0] / 8 * 7)
        self.circle_coords = [circle_x1, circle_y1, circle_x2, circle_y2]

    current_level = 0

    def start_new_level(self):
        self.current_level += 1

        """Coordinates use values in a 1000x1000 grid, and these values will be recalculated to match the actual supposed 
        coordinates. They are calculated like so: x1 = CANVAS_WIDTH[0] * rx / 1000 - self.node_radius / 2
                                                  x2 = CANVAS_WIDTH[0] * ry / 1000 + self.node_radius / 2
        
        Here, the given relative values correspond to the center of the nodes."""

        node_positions = []
        if self.current_level == 1:
            node_positions = [(250, 500), (750, 500)]
        elif self.current_level == 2:
            node_positions = [(270, 660), (730, 660), (500, 250)]
        elif 2 < self.current_level < 10:
            node_positions = [(380, 270), (620, 270), (270, 390), (270, 610), (380, 720), (620, 720), (730, 390), (730, 610)]

        obstacle_positions_per_level = {1: None,
                                        2: [(500, 560, 500, 760)],
                                        3: [(706, 300, 643, 362), (300, 725, 400, 456)],
                                        4: [(481, 781, 531, 575), (493, 200, 493, 325), (718, 500, 793, 500)]}

        # Clears game state before initializing the next level
        self.clear_game_state()

        # Tries to initialize the next level
        try:
            Level(self.canvas, obstacle_positions_per_level[self.current_level], node_positions, self.node_radius, self.lines_width)
        except KeyError:
            if self.current_level == 5:
                print("You beat all the levels, I hope you enjoyed it :D")
            else:
                print("Tried to initialize a level where its obstacles weren't given.")

    # Only used for testing
    """
    def choose_level(self, event):
        pressed_number = int(event.keysym)
        self.current_level = pressed_number - 1
        self.start_new_level()
        
    """

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind("<Key-f>", lambda a : self.toggle_fullscreen(CANVAS_WIDTH, CANVAS_HEIGHT, ))
        self.canvas.focus_set()

        # Only used for testing
        """
        for i in range(10):
            self.canvas.bind(f"<Key-{i}>", self.choose_level)
        """

    def are_there_free_nodes(self):
        for node in Node.nodes:
            if not node.already_used:
                return True
        return False

    def on_canvas_click(self, event):   # (left click)
        # print(f"point with relative coordinates: {event.x / 800 * 1000}, {event.y / 800 * 1000}")
        clicked_items = self.canvas.find_closest(event.x, event.y)

        if clicked_items:
            for node in Node.nodes:     # Checks which node was clicked
                if node.id == clicked_items[0]:

                    # If last_clicked_node doesn't have a value, returns.
                    if not Node.last_clicked_node:
                        Node.last_clicked_node = node
                        node.already_used = True
                        return

                    # Otherwise, it continues and validates the path.
                    else:
                        # If the same node was clicked again, it returns.
                        if Node.last_clicked_node == node:
                            return

                        # If validation was successful
                        if self.validate_new_path(node):
                            new_connector_line = ConnectorLine(self.canvas, x1=node.x, y1=node.y, x2=Node.last_clicked_node.x,
                                                               y2=Node.last_clicked_node.y,
                                                               connector_line_radius=self.lines_width)
                            ConnectorLine.connector_lines.append(new_connector_line)

                            # Set the node value already_used to True for both utilized nodes.
                            node.already_used = True
                            Node.last_clicked_node.already_used = True

                            Node.last_clicked_node = node

                            # Checks if all nodes have been used before or not, starts next level if yes
                            if not self.are_there_free_nodes():
                                self.canvas.after(1000, self.start_new_level)

                            return
                        else:
                            return

    def clear_player_inputs(self):

        # Deletes connector lines
        for connector_line in ConnectorLine.connector_lines:
            self.canvas.delete(connector_line.id)
        ConnectorLine.connector_lines = []

        # Deletes node variable states.
        Node.last_clicked_node = None
        for node in Node.nodes:
            node.already_used = False

        print("Cleared all player given inputs.")

    def clear_game_state(self):

        # Deletes connector lines
        for connector_line in ConnectorLine.connector_lines:
            self.canvas.delete(connector_line.id)
        ConnectorLine.connector_lines = []

        # Deletes obstacles
        for obstacle in Obstacle.obstacles:
            self.canvas.delete(obstacle.id)
        Obstacle.obstacles = []

        # Deletes nodes
        for node in Node.nodes:
            self.canvas.delete(node.id)
        Node.nodes = []
        Node.last_clicked_node = None

        # print("Cleared game state")

    def on_canvas_right_click(self, event):
        self.clear_player_inputs()

    def validate_new_path(self, node):
        # Checks if node hasn't been used before
        if node.already_used:
            print("Node once already used.")
            return False

        # Checks if new line intersects with any of the existing obstacles.
        node_points = [node.x, node.y]
        last_clicked_node_points = [Node.last_clicked_node.x, Node.last_clicked_node.y]
        for existing_line in Obstacle.obstacles + ConnectorLine.connector_lines[:-1]:
            existing_line_points = [[existing_line.x1, existing_line.y1], [existing_line.x2, existing_line.y2]]
            if lines_intersect(node_points, last_clicked_node_points, existing_line_points[1], existing_line_points[0]):
                print("This line intersects with another!")
                return False
        return True

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Connect the nodes")
    root.geometry("800x800+500+100")
    root.resizable(True, True)
    root.config(bg="black")
    game = Game(root, CANVAS_WIDTH, CANVAS_HEIGHT)
    root.mainloop()
    
