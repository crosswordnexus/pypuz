import json
import re
from collections import OrderedDict

def ordereddict_to_dict(d):
    """
    Helper function to convert an ordered dict to a dict
    This is probably not necessary but slightly cleaner
    """
    return json.loads(json.dumps(d))

def read_ipuzfile(f):
    """
    Read in an ipuz file, return a dictionary of data
    """
    ret = dict()
    # Note that we need to load an OrderedDict
    # as the order of the keys is important
    with open(f, encoding='utf-8') as fid:
        ipuzdata = json.load(fid, object_pairs_hook=OrderedDict)

    # Collect metadata
    # Remove some stuff from the puzzleKind
    kind = ipuzdata.get('kind', ["http://ipuz.org/crossword#1"])[0]
    kind = kind.replace('http://ipuz.org/', '')
    kind = re.sub('\#\d+$', '', kind)
    # We'll need the width and height later
    width = ipuzdata.get('dimensions', {}).get('width')
    height = ipuzdata.get('dimensions', {}).get('height')
    ret['metadata'] = {
      'kind': kind
    , 'author': ipuzdata.get('author')
    , 'title': ipuzdata.get('title')
    , 'copyright': ipuzdata.get('copyright')
    , 'notes': ipuzdata.get('notes')
    , 'width': width
    , 'height': height
    }

    # Get the grid
    # iPuz allows cells to be strings or dicts
    # we convert everything to a dict
    BLOCK = ipuzdata.get('block', '#')
    EMPTY = ipuzdata.get('empty', '0')
    grid = []
    puzzle = ipuzdata['puzzle']
    for y in range(height):
        for x in range(width):
            ipuzcell = puzzle[y][x]
            cell = {'x': x, 'y': y}
            # case 0: this is null
            if ipuzcell is None:
                cell['isEmpty'] = True
            # case 1: we have a string (or int)
            elif isinstance(ipuzcell, (str, int)):
                # cast to string to be safe
                ipuzcell = str(ipuzcell)
                if ipuzcell == BLOCK:
                    cell['isBlock'] = True
                elif ipuzcell is None:
                    cell['isEmpty'] = True
                elif ipuzcell != EMPTY:
                    cell['number'] = str(ipuzcell)
                try:
                    if ipuzcell != BLOCK and ipuzcell is not None:
                        sol = ipuzdata['solution'][y][x]
                        if isinstance(sol, (dict, OrderedDict)):
                            sol = sol['value']
                        cell['solution'] = sol
                except: # no solution
                    pass
            # case 2: we have a dictionary
            else:
                icell = ipuzcell.get('cell', EMPTY)
                if icell == BLOCK:
                    cell['isBlock'] = True
                elif icell is None:
                    cell['isEmpty'] = True
                elif icell != EMPTY:
                    cell['number'] = str(icell)
                cell['style'] = ordereddict_to_dict(ipuzcell.get('style', {}))
                if ipuzcell.get('value'):
                    cell['value'] = ipuzcell.get('value')
                try:
                    if icell != BLOCK and icell is not None:
                        # we pull the solution value from the "solution"
                        # this can either be a string or a dictionary
                        sol = ipuzdata['solution'][y][x]
                        if isinstance(sol, (dict, OrderedDict)):
                            sol = sol['value']
                        cell['solution'] = sol
                except: # no solution
                    pass
                #END try
            #END if/else
            grid.append(cell)
        #END for x
    #END for y
    ret['grid'] = grid

    ## Clues ##
    # Clues don't always come with explicit cell locations, which is unfortunate
    # but we'll handle that in post, so to speak
    ret_clues = []
    # The way clues are set up, it can either be a list or a dictionary
    for title, clues in ipuzdata.get('clues', {}).items():
        #[ {'title': 'Across', 'clues': [...], 'title': 'Down', 'clues': [...]} ]
        thisClues = []
        for clue1 in clues:
            if isinstance(clue1, list):
                # Indicate in the metadata that we are not given explicit cells
                ret['metadata']['noClueCells'] = True
                number, clue = clue1
                number = str(number)
                thisClues.append({'number': number, 'clue': clue})
            else:
                number = str(clue1.get('number', ''))
                clue = clue1.get('clue', '')
                if 'cells' in clue1.keys():
                    # cells are 1-indexed unfortunately
                    cells1 = clue1['cells']
                    cells = []
                    for cell in cells1:
                        cells.append([cell[0]-1, cell[1]-1])
                    thisClues.append({'number': number, 'clue': clue, 'cells': cells})
                else:
                    # if no clue cells we'll have to infer them
                    ret['metadata']['noClueCells'] = True
                    thisClues.append({'number': number, 'clue': clue})
            #END if/else
        #END for clue1
        ret_clues.append({'title': title, 'clues': thisClues})
    #END for title/clues
    ## Hack for CrossFire-exported iPuz files ##
    if len(ret_clues) == 2:
        if ret_clues[0]['title'].lower() == 'down' and ret_clues[1]['title'].lower() == 'across':
            ret_clues = [ret_clues[1], ret_clues[0]]
    #END hack
    ret['clues'] = ret_clues
    return ret
