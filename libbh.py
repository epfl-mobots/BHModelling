# This is a library with all the functions required to run the Box Hive Modelling using Plotly as the base package.
#

import plotly.graph_objects as go
import numpy as np
from abc import ABC, abstractmethod

# Theoretical max volume (ml) of honey a single ABC subregion can hold. honey_data values are
# raw ml, capped at this for opacity purposes.
MAX_HONEY_ML = 200

# Helper to make a flat colored wall (surface)
def make_wall(x, y, z, color="saddlebrown", opacity=0.5, name:str="", legendgroup:str="", legendrank:int=1000, legendgrouptitle:dict={}, showlegend:bool=False):
    return go.Surface(
        x=x, y=y, z=z,
        surfacecolor=np.ones((2,2)),  # flat shading
        cmin=0, cmax=1,
        showscale=False,
        opacity=opacity,
        name=name,
        legendrank = legendrank,
        legendgroup = legendgroup,
        legendgrouptitle = legendgrouptitle,
        colorscale = [[0, color], [1, color]],
        showlegend = showlegend
    )

class PlotlyObject(ABC): # Abstract class
    def __init__(self, textures:list):
        self.textures = textures

    @abstractmethod
    def draw_plotly(self, *args, **kwargs):
        """Child classes must implement this method"""
        pass

    def get_textures(self):
        if self.textures == []:
            return None
        return self.textures.copy()

class Frame(PlotlyObject):
    def __init__(self, x, height, depth, opacity):
        self.x = x
        self.opacity = opacity
        self.height = height
        self.depth = depth

        super().__init__([]) # No textures for now

    def draw_plotly(self, hive_height, hive_depth, color:str, name:str, show_legend:bool=False):
        z_low = (hive_height-self.height)/2
        z_high = (hive_height-self.height)/2 + self.height
        y_low = (hive_depth-self.depth)/2
        y_high = (hive_depth-self.depth)/2 + self.depth

        frame = make_wall(
            x=[[self.x, self.x], [self.x, self.x]],
            y=[[y_low, y_high], [y_low, y_high]],
            z=[[z_low, z_low], [z_high, z_high]],
            color=color,
            opacity=self.opacity,
            name=name,
            showlegend=show_legend
        )

        self.textures = [frame]

class Partition(Frame):
    def __init__(self, x, height, depth, opacity):
        super().__init__(x,height,depth,opacity)

    def draw_plotly(self, hive_height, hive_depth, show_legend:bool=False):
        super().draw_plotly(hive_height,hive_depth,"blue","partition", show_legend)
    
class ABC(Frame):
    htr_mapping = {
        0: {
            0: "h09",
            1: "h07",
            2: "h05",
            3: "h03",
            4: "h01"
        },
        1:{
            0: "h08",
            1: "h06",
            2: "h04",
            3: "h02",
            4: "h00"
        }
    }

    n_subframes_y = 5           # Number of subframes along y
    n_subframes_z = 2           # Number of subframes along z
    
    def __init__(self, name:str, x, height, depth, opacity:float, position:int):
        super().__init__(x,height,depth,opacity)
        
        assert name.startswith("abc"), "Name of ABC frame must start with 'abc'"
        self.name = name # Typically "abc21"
        self.position = position

    def draw_plotly(self, hive_height, hive_depth, show_legend:bool=False):
        # Check that brood and honey data have been loaded (nectar_data/pollen_data are always
        # set alongside them by load_data, defaulting to all-zero if not given)
        assert hasattr(self, 'brood_data'), "Brood data not loaded"
        assert hasattr(self, 'honey_data'), "Honey data not loaded"

        # Create subframes
        subframes = []
        subframe_height = self.height / ABC.n_subframes_z
        subframe_depth = self.depth / ABC.n_subframes_y
        for i in range(ABC.n_subframes_z):
            z0 = (hive_height-self.height)/2 + i * subframe_height
            z1 = (hive_height-self.height)/2 + (i + 1) * subframe_height
            for j in range(ABC.n_subframes_y):
                y0 = (hive_depth-self.depth)/2+ j * subframe_depth
                y1 = (hive_depth-self.depth)/2+ (j + 1) * subframe_depth



                htr_nb=int(ABC.htr_mapping[i][j][-1])
                # load_data already guarantees at most one of these is nonzero per subregion,
                # so the check order here doesn't matter - it's just which colour a subregion is.
                if self.brood_data[htr_nb] > 0:
                    color = "brown"
                    # Brood level is already a 0-1 coverage fraction (1 = Co, 0.5 = Co
                    # éparse, 0.3333 = Co en bordure) - use it as opacity directly.
                    opacity=self.brood_data[htr_nb] if self.brood_data[htr_nb] <= 1.0 else 1.0 # Cap opacity at 1.0
                elif self.honey_data[htr_nb] > 0:
                    color = "yellow"
                    # Honey volume is in ml; MAX_HONEY_ML is the theoretical max one subregion can hold.
                    opacity=self.honey_data[htr_nb]/MAX_HONEY_ML if self.honey_data[htr_nb] <= MAX_HONEY_ML else 1.0 # Cap opacity at 1.0
                elif self.nectar_data[htr_nb] > 0:
                    color = "beige"  # uncapped nectar/syrup - not yet capped as honey
                    # Coverage fraction, same convention as brood - use it as opacity directly.
                    opacity=self.nectar_data[htr_nb] if self.nectar_data[htr_nb] <= 1.0 else 1.0 # Cap opacity at 1.0
                elif self.pollen_data[htr_nb] > 0:
                    color = "orange"
                    # Coverage fraction, same convention as brood - use it as opacity directly.
                    opacity=self.pollen_data[htr_nb] if self.pollen_data[htr_nb] <= 1.0 else 1.0 # Cap opacity at 1.0
                else:
                    # Empty wax (Ci) / no tracked content - render like a plain, non-robotic
                    # frame (see add_frame) rather than invisible: same colour, same fixed
                    # opacity (the ABC's own base opacity, not a content-derived fraction).
                    color = "gray"
                    opacity = self.opacity

                subframe = make_wall(
                    x=[[self.x, self.x], [self.x, self.x]],
                    y=[[y0, y1], [y0, y1]],
                    z=[[z0, z0], [z1, z1]],
                    color=color,
                    opacity=opacity,
                    name=ABC.htr_mapping[i][j],
                    legendgroup=self.name,
                    legendrank=2,
                    showlegend=show_legend
                )
                subframes.append(subframe)

        # Modify the first subframe to change its legendgrouptitle to {text:self.name}
        subframes[0].legendgrouptitle = {"text": f"frame_{self.position} ({self.name})"}

        self.textures = subframes

    def load_data(self, brood_data: list, honey_data: list, nectar_data: list = None, pollen_data: list = None):
        """
        Loads the brood/honey/nectar/pollen data into the ABC object.

        :param brood_data: 10 values, indexed by htr_nb (0-9). Each is a 0-1 brood coverage
            fraction (0 = none, 0.3333 = Co en bordure, 0.5 = Co éparse, 1 = Co/full).
        :param honey_data: 10 values, indexed by htr_nb (0-9). Each is a honey volume in ml,
            capped at MAX_HONEY_ML for opacity purposes.
        :param nectar_data: 10 values, indexed by htr_nb (0-9). Each is a 0-1 coverage fraction
            for uncapped nectar/syrup (not yet capped as honey). Defaults to all zero.
        :param pollen_data: 10 values, indexed by htr_nb (0-9). Each is a 0-1 coverage fraction
            for pollen. Defaults to all zero.
        :raises AssertionError: if any subregion has more than one nonzero channel - a subregion
            can only be one thing at a time.
        """
        nectar_data = nectar_data if nectar_data is not None else [0] * 10
        pollen_data = pollen_data if pollen_data is not None else [0] * 10

        channels = {"brood": brood_data, "honey": honey_data, "nectar": nectar_data, "pollen": pollen_data}
        for htr_nb in range(10):
            active = [name for name, data in channels.items() if data[htr_nb] > 0]
            assert len(active) <= 1, (
                f"h{htr_nb:02d} is assigned to more than one content type at once: {active} "
                "- a subregion can only be one thing at a time."
            )

        self.brood_data = brood_data
        self.honey_data = honey_data
        self.nectar_data = nectar_data
        self.pollen_data = pollen_data

class BoxHive(PlotlyObject):
    def __init__(self, width, height, depth, opacity):
        """
        params:
        - width of the hive
        - height of the hive
        - depth of the hive
        - opacity for all elements of the hive
        """
        self.width = width
        self.height = height
        self.depth = depth
        self.opacity = opacity
        self.frame_positioning = {}
        for i in range(10):
            self.frame_positioning[i+1] = self.width/11 * (i+1)

        self.occupancy = {}
        for i in range(10):
            self.occupancy[i+1] = None # We start with an empty hive

        # Some typical frame dimensions
        self.frame_height = 0.8*self.height
        self.frame_depth = 0.92*self.depth
        super().__init__([]) # No textures as of yet

    def add_partition(self, position:int, show_legend:bool = True):
        """
        Adds a partition into the hive at the give position
        """
        # First check that position is between 1 and 10:
        assert position >=1 and position <=10, "Position must be an integer comprised between [0,10]"
        # Then check that the space is free
        assert self.occupancy[position] == None, f"Position {position} is already occupied!"
        
        _x = self.frame_positioning[position]
        # Create the partition
        partition = Partition(x=_x, height=self.frame_height,depth=self.frame_depth,opacity=self.opacity)
        partition.draw_plotly(self.height,self.depth,show_legend)
        # And store it in occupancy
        self.occupancy[position] = partition

    def add_frame(self, position:int, opacity:float, show_legend:bool = True):
        """
        Adds a frame into the hive at the give position
        """
        # First check that position is between 1 and 10:
        assert position >=1 and position <=10, "Position must be an integer comprised between [0,10]"
        # Then check that the space is free
        assert self.occupancy[position] == None, f"Position {position} is already occupied!"

        _x = self.frame_positioning[position]
        # Create the frame
        frame = Frame(x=_x, height=self.frame_height, depth=self.frame_depth, opacity=opacity)
        frame.draw_plotly(self.height, self.depth, "peru", f"frame_{position}", show_legend) # Same colour as the hive's own walls
        # And store it in occupancy
        self.occupancy[position] = frame

    def add_abc(self, position:int, opacity:float, name:str):
        """
        Adds an ABC frame into the hive at the given position and with the given opacity and name.
        """
        # First check that position is between 1 and 10:
        assert position >=1 and position <=10, "Position must be an integer comprised between [0,10]"
        # Then check that the space is free
        assert self.occupancy[position] == None, f"Position {position} is already occupied!"

        _x = self.frame_positioning[position]
        # Create the ABC frame
        abc = ABC(name, _x, self.frame_height, self.frame_depth, opacity, position)
        # And store it in occupancy
        self.occupancy[position] = abc

    def loadABCdata(self, brood_data: dict, honey_data: dict, nectar_data: dict = None, pollen_data: dict = None):
        """
        Loads the brood/honey/nectar/pollen data into the ABC objects.

        :param brood_data: {abc_name: 10 values (htr_nb 0-9)}, each a 0-1 brood coverage
            fraction. See ABC.load_data.
        :param honey_data: {abc_name: 10 values (htr_nb 0-9)}, each a honey volume in ml
            (MAX_HONEY_ML theoretical max per subregion). See ABC.load_data.
        :param nectar_data: {abc_name: 10 values (htr_nb 0-9)}, each a 0-1 coverage fraction.
            Optional - abc's not present here (or if the dict itself is None) default to all
            zero. See ABC.load_data.
        :param pollen_data: {abc_name: 10 values (htr_nb 0-9)}, each a 0-1 coverage fraction.
            Optional, same defaulting as nectar_data. See ABC.load_data.
        """
        for abc in self.occupancy.values():
            if isinstance(abc, ABC):
                name = abc.name
                assert name in brood_data.keys(), f"Brood data for {name} not found!"
                assert name in honey_data.keys(), f"Honey data for {name} not found!"

                abc.load_data(
                    brood_data[name], honey_data[name],
                    nectar_data.get(name) if nectar_data else None,
                    pollen_data.get(name) if pollen_data else None,
                )

    def getAllTextures(self):
        """
        Function to retrieve all (active) textures of the hive.
        """
        all_textures = self.get_textures()
        for pos in self.occupancy:
            if self.occupancy[pos] is None:
                continue
            if not issubclass(type(self.occupancy[pos]), PlotlyObject):
                raise(ValueError(f"Invalid object type in occupancy: {type(self.occupancy[pos])}, {self.occupancy[pos]}"))
            if issubclass(type(self.occupancy[pos]), ABC):
                self.occupancy[pos].draw_plotly(self.height, self.depth) # ABC textures computed at the very end
            all_textures.extend(self.occupancy[pos].get_textures())

        return all_textures

    def draw_plotly(self,show_legend:bool=False):
        """
        Creates the basic hive structures (walls and landing pad) and adds the textures to the parent class.
        """
        # Bottom wall (z = 0 plane)
        bottom_wall = make_wall(
            x=[[0, self.width], [0, self.width]],
            y=[[0, 0], [self.depth, self.depth]],
            z=[[0, 0], [0, 0]],
            color="peru",
            opacity=self.opacity,
            name="Bottom",
            legendgroup="hive",
            legendrank=1,
            showlegend = show_legend
        )

        # Front wall (y = 1 plane)
        front_wall = make_wall(
            x=[[0, self.width], [0, self.width]],
            y=[[0, 0], [0, 0]],
            z=[[0.1*self.height, 0.1*self.height], [self.height, self.height]],
            color="peru",
            opacity=self.opacity,
            name="Front",
            legendgroup="hive",
            legendrank=1,
            legendgrouptitle={"text": "Hive"},
            showlegend = show_legend
        )

        # Back wall (y = hive_depth plane)
        back_wall = make_wall(
            x=[[0, self.width], [0, self.width]],
            y=[[self.depth, self.depth], [self.depth, self.depth]],
            z=[[0, 0], [self.height, self.height]],
            color="peru",
            opacity=self.opacity,
            name="Back",
            legendgroup="hive",
            legendrank=1,
            showlegend = show_legend
        )

        # Right wall (x = 0 plane)
        right_wall = make_wall(
            x=[[0, 0], [0, 0]],
            y=[[0, self.depth], [0, self.depth]],
            z=[[0, 0], [self.height, self.height]],
            color="peru",
            opacity=self.opacity,
            name="Right",
            legendgroup="hive",
            legendrank=1,
            showlegend = show_legend
        )

        # Left wall (x = hive_width plane)
        left_wall = make_wall(
            x=[[self.width, self.width], [self.width, self.width]],
            y=[[0, self.depth], [0, self.depth]],
            z=[[0, 0], [self.height, self.height]],
            color="peru",
            opacity=self.opacity,
            name="Left",
            legendgroup="hive",
            legendrank=1,
            showlegend = show_legend
        )

        landing_pad = make_wall(
            x=[[0, self.width], [0, self.width]],
            y=[[0, 0], [-0.4*self.depth, -0.4*self.depth]],
            z=[[0, 0], [-0.2*self.height, -0.2*self.height]],
            color="black",
            opacity=self.opacity,
            name="Landing pad",
            legendgroup="hive",
            legendrank=1,
            showlegend = show_legend
        )
        self.textures = [bottom_wall, back_wall, front_wall, left_wall, right_wall, landing_pad]

def build_time_slider_figure(hive: BoxHive, data_over_time: dict) -> go.Figure:
    """
    Builds a Plotly figure with a time-navigation slider, showing how each ABC subregion's
    content evolves across a sequence of time steps (e.g. one per hive visit).

    :param hive: a BoxHive with its frames/partitions/ABCs already added, and hive.draw_plotly()
        already called once (the walls are static across time - only ABC content changes).
        Occupancy (which positions hold what) must stay the same for every time step; only call
        loadABCdata-style content on it, don't add/remove frames between steps.
    :param data_over_time: {label: {"brood": ..., "honey": ..., "nectar": ..., "pollen": ...}},
        one entry per time step - the inner dict is passed straight to hive.loadABCdata as
        keyword arguments ("nectar"/"pollen" are optional there, see loadABCdata). Slider steps
        follow sorted(data_over_time.keys()); label is typically a date or a string that sorts
        correctly (e.g. "2026-06-15").
    :return: a go.Figure with one frame per time step and a slider to move between them.
    """
    assert hive.textures, "Call hive.draw_plotly() before building the slider (walls are static across frames)."
    labels = sorted(data_over_time.keys())
    assert len(labels) > 0, "data_over_time must have at least one time step"

    frames = []
    for label in labels:
        step = data_over_time[label]
        hive.loadABCdata(
            step["brood"], step["honey"],
            step.get("nectar"), step.get("pollen"),
        )
        frames.append(go.Frame(data=hive.getAllTextures(), name=str(label)))

    return go.Figure(
        data=frames[0].data,
        frames=frames,
        layout=go.Layout(
            sliders=[{
                "active": 0,
                "currentvalue": {"prefix": "Time: "},
                "steps": [
                    {
                        "args": [[f.name], {"mode": "immediate",
                                             "frame": {"duration": 0, "redraw": True},
                                             "transition": {"duration": 0}}],
                        "label": f.name,
                        "method": "animate",
                    }
                    for f in frames
                ],
            }],
        ),
    )