from file_types import puz
CROSSWORD_TYPE = 'crossword'

# Class for crossword metadata
# This is a mostly uninteresting class
class MetaData:
    def __init__(self):
        pass

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
    StyleSpec (dictionary -- see the relevant section on http://www.ipuz.org/)
    """
    def __init__(self, x, y, solution=None, number=None, isBlock=None, isEmpty=None, StyleSpec={}):
        self.x = x
        self.y = y
        self.solution = solution
        self.number = number
        self.isBlock = isBlock
        self.isEmpty = isEmpty
        self.StyleSpec = StyleSpec

# Class for a crossword grid
class Grid:
    # here "solution" is a list of Cell objects
    def __init__(self, solution):
        this.cells = cells
        this.height = max(c.y for c in cells) + 1
        this.width = max(c.x for c in cells) + 1
        # Set the numbering
        this.gridNumbering()

    # return the cell at (x,y)
    def cellAt(self, x, y):
        for c in this.cells:
            if c.x == x and c.y == y:
                return c

    # Return the solution at (x, y)
    def letterAt(self, x, y):
        return this.cellAt(x, y).solution

    # Return True if the cell at (x,y) is empty or a block
    def isBlack(self, x, y):
        var thisCell = this.cellAt(x, y)
        return (thisCell.isEmpty or thisCell.isBlock)

    # check if we have a black square (or a bar) in a given direction
    def hasBlack(self, x, y, dir):
        mapping_dict = {
          'R': {'xcheck': this.width-1, 'xoffset': 1, 'yoffset': 0, 'dir2': 'L'}
        , 'L': {'xcheck': 0, 'xoffset': -1, 'yoffset': 0, 'dir2': 'R'}
        , 'T': {'ycheck': 0, 'xoffset': 0, 'yoffset': -1, 'dir2': 'B'}
        , 'B': {'ycheck': this.height-1, 'xoffset': 0, 'yoffset': 1, 'dir2': 'T'}
        }
        md = mapping_dict[dir]
        if x == md['xcheck'] or y == md['ycheck']:
            return True
        elif this.isBlack(x + md['xoffset'], y + md['yoffset'])):
            return True
        elif dir in this.cellAt(x, y).StyleSpec.get('barred', ''):
            return True
        elif dir2 in this.cellAt(x + md['xoffset'], y + md['yoffset']).StyleSpec.get('barred', ''):
            return True
        return False
    #END hasBlack

    # Whether the coordinates are the starting letter for a word
    # both startAcrossWord and startDownWord have to account for bars
    def startAcrossWord(self, x, y):
        return this.hasBlack(x, y, 'L') && !this.isBlack(x, y) && !this.hasBlack(x, y, 'R')
    def startDownWord(self, x, y):
        return this.hasBlack(x, y, 'T') && !this.isBlack(x, y) && !this.hasBlack(x, y, 'B')

    # An array of grid numbers
    def gridNumbering(self):
        thisNumber = 1
        for y in range(this.height):
            thisNumbers = []
            for x in range(this.width):
                if this.startAcrossWord(x, y) or this.startDownWord(x, y):
                    this.cellAt(x, y).number = thisNumber
                    thisNumber += 1
                #END if
            #END for x
        #END for y
    #END def gridNumbering

    def acrossEntries() {
        var acrossEntries = {}, x, y, thisNum;
        for (y = 0; y < this.height; y++) {
            for (x = 0; x < this.width; x++) {
                if (this.startAcrossWord(x, y)) {
                    thisNum = this.numbers[y][x];
                    if (!acrossEntries[thisNum] && thisNum) {
                        acrossEntries[thisNum] = {'word': '', 'cells': []};
                    }
                }
                if (!this.isBlack(x, y) && thisNum) {
                    var letter = this.letterAt(x, y);
                    acrossEntries[thisNum]['word'] += letter;
                    acrossEntries[thisNum]['cells'].push([x, y]);
                }
                // end the across entry if we hit the edge
                if (this.hasBlack(x, y, 'right')) {
                    thisNum = null;
                }
            }
        }
        return acrossEntries;
    }

    downEntries() {
        var downEntries = {}, x, y, thisNum;
        for (x = 0; x < this.width; x++) {
            for (y = 0; y < this.height; y++) {
                if (this.startDownWord(x, y)) {
                    thisNum = this.numbers[y][x];
                    if (!downEntries[thisNum] && thisNum) {
                        downEntries[thisNum] = {'word': '', 'cells': []};
                    }
                }
                if (!this.isBlack(x, y) && thisNum) {
                    var letter = this.letterAt(x, y);
                    downEntries[thisNum]['word'] += letter;
                    downEntries[thisNum]['cells'].push([x, y]);
                }
                // end the down entry if we hit the bottom
                if (this.hasBlack(x, y, 'bottom')) {
                    thisNum = null;
                }
            }
        }
        return downEntries;
    }
}

# Simple class for the dimensions of a crossword
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
