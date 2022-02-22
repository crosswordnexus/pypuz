from file_types import puz

BLOCK = '#'
EMPTY = '_'
CROSSWORD_TYPE = 'crossword'

class Dimensions:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def to_dict(self):
        return {'width': self.width, 'height': self.height}

class Puzzle:
    def __init__(self):
        # Define some constants here
        self.title = None
        self.author = None
        self.copyright = None
        self.kind = CROSSWORD_TYPE

    def fromPuz(self, puzFile):
        pz = puz.read(puzFile)
        self.title = pz.title
        self.author = pz.author
        self.copyright = pz.copyright
        self.kind = CROSSWORD_TYPE
        self.dimensions = Dimensions(pz.width, pz.height)
        self.puzzle = []
        
