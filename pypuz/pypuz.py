from file_types import puz
import json
CROSSWORD_TYPE = 'crossword'

# Class for crossword metadata
# This is a mostly uninteresting class
class MetaData:
    """
    Metadata for a crossword.
    Mandatory components:
    kind (the puzzle type)
    Optional:
    author, title, copyright, notes, width, height
    """
    def __init__(self, kind):
        self.kind = kind
#END class MetaData

# Class for a crossword cell
class Cell:
    """
    A crossword cell.
    The only necessary components are x and y (the coordinates, 0-indexed).
    Other possible components:
    solution (string)
    number (string -- the number or letter in the top left)
    isBlock (boolean -- set to True if the cell is a black square)
    isEmpty (boolean -- set to True if the cell is a "void")
    styleSpec (dictionary -- see the relevant section on http://www.ipuz.org/)
    """
    def __init__(self, x, y, solution=None, number=None, isBlock=None, isEmpty=None, styleSpec={}):
        self.x = x
        self.y = y
        self.solution = solution
        self.number = number
        self.isBlock = isBlock
        self.isEmpty = isEmpty
        self.styleSpec = styleSpec

    def __repr__(self):
        return f"Cell({{({self.x}, {self.y}), {self.solution}}})"

class Grid:
    """
    Class for a crossword grid
    """
    # here "solution" is a list of Cell objects
    def __init__(self, cells):
        self.cells = cells
        self.height = max(c.y for c in cells) + 1
        self.width = max(c.x for c in cells) + 1

    def __repr__(self):
        return json.dumps(self.solutionArray())

    def solutionArray(self):
        arr = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                c = self.cellAt(x, y)
                letter = c.solution
                if c.isBlock:
                    letter = '#'
                if c.isEmpty:
                    letter = '_'
                row.append(letter)
            arr.append(row)
        return arr

    # return the cell at (x,y)
    def cellAt(self, x, y):
        for c in self.cells:
            if c.x == x and c.y == y:
                return c

    # Return the solution at (x, y)
    def letterAt(self, x, y):
        return self.cellAt(x, y).solution

    # Return True if the cell at (x,y) is empty or a block
    def isBlack(self, x, y):
        thisCell = self.cellAt(x, y)
        return (thisCell.isEmpty or thisCell.isBlock)

    # check if we have a black square (or a bar) in a given direction
    def hasBlack(self, x, y, dir):
        mapping_dict = {
          'R': {'xcheck': self.width-1, 'xoffset': 1, 'yoffset': 0, 'dir2': 'L'}
        , 'L': {'xcheck': 0, 'xoffset': -1, 'yoffset': 0, 'dir2': 'R'}
        , 'T': {'ycheck': 0, 'xoffset': 0, 'yoffset': -1, 'dir2': 'B'}
        , 'B': {'ycheck': self.height-1, 'xoffset': 0, 'yoffset': 1, 'dir2': 'T'}
        }
        md = mapping_dict[dir]
        dir2 = md['dir2']
        if x == md.get('xcheck') or y == md.get('ycheck'):
            return True
        elif self.isBlack(x + md['xoffset'], y + md['yoffset']):
            return True
        elif dir in self.cellAt(x, y).styleSpec.get('barred', ''):
            return True
        elif dir2 in self.cellAt(x + md['xoffset'], y + md['yoffset']).styleSpec.get('barred', ''):
            return True
        return False
    #END hasBlack

    # Whether the coordinates are the starting letter for a word
    # both startAcrossWord and startDownWord have to account for bars
    def startAcrossWord(self, x, y):
        return self.hasBlack(x, y, 'L') and not self.isBlack(x, y) and not self.hasBlack(x, y, 'R')
    def startDownWord(self, x, y):
        return self.hasBlack(x, y, 'T') and not self.isBlack(x, y) and not self.hasBlack(x, y, 'B')

    # Set the default numbers
    def setNumbering(self):
        thisNumber = 1
        for y in range(self.height):
            thisNumbers = []
            for x in range(self.width):
                if self.startAcrossWord(x, y) or self.startDownWord(x, y):
                    self.cellAt(x, y).number = thisNumber
                    thisNumber += 1
                #END if
            #END for x
        #END for y
    #END def gridNumbering

    # Return the across entries (TODO)
    def acrossEntries(self):
        # Set the numbering if it doesn't already exist
        self.setNumbering()
        acrossEntries = {}
        thisNum = None
        for y in range(self.height):
            for x in range(self.width):
                if self.startAcrossWord(x, y):
                    thisNum = self.cellAt(x, y).number
                    if acrossEntries.get(thisNum) is None and thisNum is not None:
                        acrossEntries[thisNum] = {'word': '', 'cells': []}
                if not self.isBlack(x, y) and thisNum is not None:
                    letter = self.letterAt(x, y)
                    acrossEntries[thisNum]['word'] += letter
                    acrossEntries[thisNum]['cells'].append([x, y])
                # end the across entry if we hit an edge
                if self.hasBlack(x, y, 'R'):
                    thisNum = None
        return acrossEntries
    #END acrossEntries()

    # Return the down entries (TODO)
    def downEntries(self):
        # Set the numbering if it doesn't already exist
        self.setNumbering()
        downEntries = {}
        thisNum = None
        for x in range(self.width):
            for y in range(self.height):
                if self.startDownWord(x, y):
                    thisNum = self.cellAt(x, y).number
                    if downEntries.get(thisNum) is None and thisNum is not None:
                        downEntries[thisNum] = {'word': '', 'cells': []}
                if not self.isBlack(x, y) and thisNum is not None:
                    letter = self.letterAt(x, y)
                    downEntries[thisNum]['word'] += letter
                    downEntries[thisNum]['cells'].append([x, y])
                # end the down entry if we hit the bottom
                if self.hasBlack(x, y, 'B'):
                    thisNum = None
        return downEntries
#END class Grid

class Clue:
    """
    The class for an individual clue
    This has three components:
    * clue -- the actual clue
    * number (optional) -- the number of the clue
    * cells -- the coordinates of the cells for the entry corresponding to the clue
    """
    def __init__(self, clue, cells, number=None):
        self.clue = clue
        self.cells = cells
        self.number = number

    def __repr__(self):
        return self.clue
#END Clue

class Puzzle:
    """
    Class for a crossword
    """
    def __init__(self, metadata=None, grid=None, clues=None):
        # metadata is a MetaData class
        self.metadata = metadata
        # grid is a Grid class
        self.grid = grid
        # clues is just a list of dictionaries, e.g.
        # [ {'title': 'Across', 'clues': [...], 'title': 'Down', 'clues': [...]} ]
        self.clues = clues

    def fromPuz(self, puzFile):
        # Read in the file
        pz = puz.read(puzFile)

        # Set up the metadata
        kind = CROSSWORD_TYPE
        if pz.puzzletype == 1025:
            kind = 'diagramless'
        metadata = MetaData(kind)
        metadata.title = pz.title
        metadata.author = pz.author
        metadata.copyright = pz.copyright
        metadata.notes = pz.notes
        metadata.width = pz.width
        metadata.height = pz.height

        # Create the grid
        # TODO: deal with circles and rebuses
        cells = []
        i = 0
        for y in range(metadata.height):
            for x in range(metadata.width):
                cell_value, isBlock = pz.solution[i], None
                # black squares can occasionally be ":" in puz files
                if cell_value in ('.', ':'):
                    cell_value, isBlock = None, True
                # Rebus
                if pz.has_rebus():
                    r = pz.rebus()
                    if i in r.get_rebus_squares():
                        cell_value = r.get_rebus_solution(i)
                # Circles
                stylespec = {}
                if pz.has_markup():
                    m = pz.markup()
                    if i in m.get_markup_squares():
                        stylespec = {"shapebg": "circle"}
                cell = Cell(x, y, solution=cell_value, isBlock=isBlock, styleSpec=stylespec)
                cells.append(cell)
                i += 1
            #END for x
        #END for y
        grid = Grid(cells)
        # Set the numbering
        grid.setNumbering()

        # clues
        # Get the across and down entries
        adEntries = (grid.acrossEntries(), grid.downEntries())
        numbering = pz.clue_numbering()
        acrossClues, downClues = numbering.across, numbering.down
        allClues = [acrossClues, downClues]
        clues = [ {'title': 'Across', 'clues': []}, {'title': 'Down', 'clues': []} ]
        for i, clueList in enumerate(allClues):
            for c in clueList:
                number = c['num']
                clue = c['clue']
                cells = adEntries[i][number]['cells']
                clue = Clue(clue=clue, cells=cells, number=number)
                clues[i]['clues'].append(clue)

        return Puzzle(metadata=metadata, grid=grid, clues=clues)
