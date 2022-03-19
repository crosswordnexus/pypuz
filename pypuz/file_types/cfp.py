import json
import re
from collections import OrderedDict, defaultdict
import xml.etree.ElementTree as ET


# courtesy of https://stackoverflow.com/a/32842402
def etree_to_ordereddict(t):
    d = OrderedDict()
    d[t.tag] = OrderedDict() if t.attrib else None
    children = list(t)
    if children:
        dd = OrderedDict()
        for dc in map(etree_to_ordereddict, children):
            for k, v in dc.items():
                if k not in dd:
                    dd[k] = list()
                dd[k].append(v)
        d = OrderedDict()
        d[t.tag] = OrderedDict()
        for k, v in dd.items():
            if len(v) == 1:
                d[t.tag][k] = v[0]
            else:
                d[t.tag][k] = v
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


def read_cfpfile(f):
    """
    Read in a CFP file, return a dictionary of data
    """
    ret = dict()
    with open(f, 'r') as fid:
        xml = fid.read()
    tree = ET.XML(xml)
    cfpdata = etree_to_ordereddict(tree)
    cfpdata = cfpdata['CROSSFIRE']

    # Collect metadata
    kind = "crossword"
    # We'll need the width and height later
    grid1 = cfpdata['GRID']
    width = int(grid1['@width'])
    grid_text = grid1['#text']
    soln_arr = grid_text.split('\n')
    height = len(soln_arr)
    ret['metadata'] = {
      'kind': kind
    , 'author': cfpdata.get('AUTHOR')
    , 'title': cfpdata.get('TITLE')
    , 'copyright': cfpdata.get('COPYRIGHT')
    , 'notes': cfpdata.get('NOTES')
    , 'width': width
    , 'height': height
    }
    
    # Read in rebus info, if available
    rebus1 = cfpdata.get('REBUSES', {})
    rebus = dict()
    for _, v in rebus1.items():
        rebus[v['@input']] = v['@letters']
        
    # Circle info, if available

    # Get the grid
    grid = []
    for i, letter in enumerate(grid_text.replace('\n', '')):
        y = i // width
        x = i % width
        cell_value = rebus.get(letter, letter)
        fill = None
        # black squares
        if cell_value == '.':
            cell_value, isBlock = None, True
        
        
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
                thisClues.append({'number': number, 'clue': clue})
            else:
                number = clue1.get('number', '')
                clue = clue1.get('clue', '')
                # cells are 1-indexed unfortunately
                cells1 = clue1['cells']
                cells = []
                for cell in cells1:
                    cells.append([cell[0]-1, cell[1]-1])
                thisClues.append({'number': number, 'clue': clue, 'cells': cells})
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
