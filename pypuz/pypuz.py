from .file_types import puz, ipuz, cfp, jpz, amuselabs
import json
import itertools
from collections import OrderedDict

# This imports the _module_ unidecode, which converts Unicode strings to
# plain ASCII. The puz format, however, can accept Latin1, which is a larger
# subset. So the second line tells the module to leave codepoints 128-256
# untouched, then we import the _function_ unidecode.
import unidecode
unidecode.Cache[0] = [chr(c) if c > 127 else '' for c in range(256)]
from unidecode import unidecode as unidecode_fxn

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
    value (string -- the currently filled value of the cell)
    number (string -- the number or letter in the top left)
    isBlock (boolean -- set to True if the cell is a black square)
    isEmpty (boolean -- set to True if the cell is a "void")
    style (dictionary -- see the "StyleSpec" section on http://www.ipuz.org/)
    """
    def __init__(self, x, y, solution=None, value=None, number=None, isBlock=None, isEmpty=None, style={}):
        self.x = x
        self.y = y
        self.solution = solution
        self.value = value
        if number:
            self.number = str(number)
        else:
            self.number = None
        self.isBlock = isBlock
        self.isEmpty = isEmpty
        self.style = style

    def __repr__(self):
        return f"Cell({{({self.x}, {self.y}), {self.solution}}})"

class Grid:
    """
    Class for a crossword grid
    """
    # here "cells" is a list of Cell objects
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
        elif dir in self.cellAt(x, y).style.get('barred', ''):
            return True
        elif dir2 in self.cellAt(x + md['xoffset'], y + md['yoffset']).style.get('barred', ''):
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
                    self.cellAt(x, y).number = str(thisNumber)
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
                    acrossEntries[thisNum]['word'] += letter or ''
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
                    downEntries[thisNum]['word'] += letter or ''
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
        if number is not None:
            self.number = str(number)
        else:
            self.number = None

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
        cells = []
        i = 0
        for y in range(metadata.height):
            for x in range(metadata.width):
                cell_value, isBlock = pz.solution[i], None
                fill = pz.fill[i]
                if fill in ('-', '.', ':'):
                    fill = None
                # black squares can occasionally be ":" in puz files
                if cell_value in ('.', ':'):
                    cell_value, isBlock = None, True
                # Rebus
                if pz.has_rebus():
                    r = pz.rebus()
                    if i in r.get_rebus_squares():
                        cell_value = r.get_rebus_solution(i)
                # Circles
                style = {}
                if pz.has_markup():
                    m = pz.markup()
                    if i in m.get_markup_squares():
                        style = {"shapebg": "circle"}
                cell = Cell(x, y, solution=cell_value, value=fill, isBlock=isBlock, style=style)
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
                number = str(c['num'])
                clue = c['clue']
                cells = adEntries[i][number]['cells']
                clue = Clue(clue=clue, cells=cells, number=number)
                clues[i]['clues'].append(clue)

        return Puzzle(metadata=metadata, grid=grid, clues=clues)
    #END fromPuz()
    
    def toPuz(self, filename):
        """
        Write a .puz file.
        Because of limitations of the .puz format, this is lossy at best.
        In rare cases this may result in a nonsense .puz file
        99% of the time this should work.
        
        Many thanks to xword-dl for the bulk of this code.
        """
        pz = puz.Puzzle()
        # Metadata
        for a in ('author', 'title', 'copyright', 'notes'):
            setattr(pz, a, getattr(self.metadata, a, ''))
            
        # Dimensions
        pz.width, pz.height = self.grid.width, self.grid.height
        
        # Fill and solution
        circled = [(c.x, c.y) for c in self.grid.cells if c.style.get('shapebg') == 'circle']
        solution, fill, markup, rebus_board, rebus_index, rebus_table = '', '', b'', [], 0, ''
        
        for row_num in range(self.grid.height):
            for col_num in range(self.grid.width):
                cell = self.grid.cellAt(col_num, row_num)
                if c.isBlock:
                    solution += '.'
                    fill += '.'
                    markup += b'\x00'
                    rebus_board.append(0)
                elif len(c.solution) == 1:
                    solution += c.solution
                    fill += '-'
                    markup += b'\x80' if (col_num, row_num) in circled else b'\x00'
                    rebus_board.append(0)
                else:
                    solution += c.solution[0]
                    fill += '-'
                    rebus_board.append(rebus_index + 1)
                    rebus_table += '{:2d}:{};'.format(rebus_index, c.solution)
                    rebus_index += 1
                #END if/else
            #END for col_num
        #END for row_num
                    
        pz.solution = solution
        pz.fill = fill
        
        # Clues
        # there *must* be an "across" and "down" here, else we throw an exception
        all_clues = []
        num_dirs_found = 0
        for clue_list in self.clues:
            if clue_list['title'].lower() == 'across':
                num_dirs_found += 1
                for c in clue_list['clues']:
                    setattr(c, 'dir', 0)
                    all_clues.append(c)
            if clue_list['title'].lower() == 'down':
                num_dirs_found += 1
                for c in clue_list['clues']:
                    setattr(c, 'dir', 1)
                    all_clues.append(c)
                
        if num_dirs_found != 2:
            raise(BaseException('Proper clue lists not found'))
            
        weirdass_puz_clue_sorting = sorted(all_clues, key=lambda c: (c.number, c.dir))
        
        clues = [c.clue for c in weirdass_puz_clue_sorting]
        
        normalized_clues = [unidecode_fxn(clue) for clue in clues]
        pz.clues.extend(normalized_clues)

        has_markup = b'\x80' in markup
        has_rebus = any(rebus_board)

        if has_markup:
            pz.extensions[b'GEXT'] = markup
            pz._extensions_order.append(b'GEXT')
            pz.markup()

        if has_rebus:
            pz.extensions[b'GRBS'] = bytes(rebus_board)
            pz.extensions[b'RTBL'] = rebus_table.encode(puz.ENCODING)
            pz._extensions_order.extend([b'GRBS', b'RTBL'])
            pz.rebus()
        
        # Save the file
        pz.save(filename)
        
        return
    #END toPuz()
        
    def toIPuz(self, filename):
        """Write an iPuz file"""
        d = {}
        # Metadata first
        d["version"] = "http://ipuz.org/v1"
        ipuzkind = f"http://ipuz.org/{self.metadata.kind}#1"
        d['kind'] = [ipuzkind]
        for a in ('author', 'title', 'copyright', 'notes'):
            d[a] = getattr(self.metadata, a, '')
        # dimensions
        d['dimensions'] = {"width": self.grid.width, "height": self.grid.height}
        # we explicitly define "block" and "empty"
        BLOCK, EMPTY = '#', '_'
        d['block'] = BLOCK; d['empty'] = EMPTY
        # puzzle and solution
        puzzle, solution = [], []
        for y in range(self.grid.height):
            row, solrow = [], []
            for x in range(self.grid.width):
                c = self.grid.cellAt(x, y)
                if c.isBlock:
                    row.append(BLOCK)
                elif c.isEmpty:
                    row.append(None)
                else:
                    num = c.number or EMPTY
                    row.append({"cell": num, "style": c.style})
                solrow.append(c.solution)
            #END for x
            puzzle.append(row)
            solution.append(solrow)
        #END for y
        d['puzzle'] = puzzle
        # add a solution only if there is one
        solset = set(list(itertools.chain(*solution)))
        if not solset.issubset(set([BLOCK, None])):
            d['solution'] = solution

        # Take care of clues, remembering that they are 1-indexed
        clues = OrderedDict()
        for c1 in self.clues:
            c1_arr = []
            for c2 in c1['clues']:
                thisClue = {"clue": c2.clue, "number": c2.number}
                thisCells = []
                for c3 in c2.cells:
                    thisCells.append([c3[0]+1, c3[1]+1])
                thisClue["cells"] = thisCells
                c1_arr.append(thisClue)
            #END for c2
            clues[c1['title']] = c1_arr
        #END for c1
        d['clues'] = clues

        # write the file
        with open(filename, 'w') as fid:
            json.dump(d, fid)
    #END toIPuz

    def fromDict(self, d1):
        """
        our file_types folder creates standard dictionaries
        this method creates a Puzzle instance from the dictionary
        """
        # Metadata
        md = d1['metadata']
        metadata = MetaData(md['kind'])
        metadata.title = md.get('title')
        metadata.author = md.get('author')
        metadata.copyright = md.get('copyright')
        metadata.notes = md.get('notes')
        metadata.width = md.get('width')
        metadata.height = md.get('height')

        # Grid
        cells = []
        for c in d1['grid']:
            cell = Cell(c['x'], c['y'], solution=c.get('solution')
                , value=c.get('value'), number=c.get('number')
                , isBlock=c.get('isBlock'), isEmpty=c.get('isEmpty'), style=c.get('style', {}))
            cells.append(cell)
        #END for c
        grid = Grid(cells)

        # Clues
        clues = []
        # We use these if we don't have explicit clue cell values
        if d1['metadata'].get('noClueCells'):
            cellLists = (grid.acrossEntries(), grid.downEntries())
        else:
            cellLists = ({}, {})
        for i, cluelist in enumerate(d1['clues']):
            title = cluelist['title']
            clues1 = cluelist['clues']
            thisClues = []
            for j, clue in enumerate(clues1):
                number = clue.get('number')
                # Infer cell locations if they're not given
                cells = clue.get('cells', cellLists[i].get(number, {}).get('cells'))
                c = Clue(clue.get('clue'), cells, number=number)
                thisClues.append(c)
            #END for clues1
            clues.append({'title': title, 'clues': thisClues})
        #END for cluelists
        return Puzzle(metadata=metadata, grid=grid, clues=clues)
    #END fromIPuz()

    def fromIPuz(self, puzFile):
        ipz = ipuz.read_ipuzfile(puzFile)
        return Puzzle().fromDict(ipz)
    #END fromIPuz()

    def fromCFP(self, puzFile):
        cfpdata = cfp.read_cfpfile(puzFile)
        return Puzzle().fromDict(cfpdata)
    #END fromCFP()

    def fromJPZ(self, puzFile):
        jpzdata = jpz.read_jpzfile(puzFile)
        return Puzzle().fromDict(jpzdata)
    #END fromJPZ()

    def fromAmuseLabs(self, s):
        data = amuselabs.read_amuselabs_data(s)
        return Puzzle().fromDict(data)
    #END fromAmuseLabs()
