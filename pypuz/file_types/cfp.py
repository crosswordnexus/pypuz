"""
Functions for reading crossword data from Crossfire (.cfp) files.
"""

import json
import re
from collections import OrderedDict, defaultdict
import xml.etree.ElementTree as ET


def etree_to_ordereddict(t):
    """
    Convert an XML ElementTree into an OrderedDict.
    
    This helper function recursively traverses the XML tree and builds a nested
    OrderedDict representation, preserving the order of elements and handling 
    attributes and text content.

    Args:
        t (xml.etree.ElementTree.Element): The XML element to convert.

    Returns:
        OrderedDict: A dictionary representation of the XML tree.
    """
    # courtesy of https://stackoverflow.com/a/32842402
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
    Read a Crossfire (.cfp) file and return a dictionary of puzzle data.

    Args:
        f (str): Path to the .cfp file.

    Returns:
        dict: A dictionary structured for use with the pypuz Puzzle class, containing
              'metadata', 'grid', and 'clues'.
    """
    ret = dict()
    with open(f, 'r') as fid:
        xml = fid.read()
    tree = ET.XML(xml)
    cfpdata = etree_to_ordereddict(tree)
    # Crossfire files wrap everything in a CROSSFIRE tag
    cfpdata = cfpdata['CROSSFIRE']

    # Metadata extraction
    kind = "crossword"
    grid1 = cfpdata['GRID']
    width = int(grid1['@width'])
    grid_text = grid1['#text']
    # Grid text in CFP is newline-separated rows
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
    , 'noClueCells': True
    }

    # Rebus information: CFP stores rebuses in a REBUSES section
    # mapping a single character in the grid to a multi-character string
    rebus1 = cfpdata.get('REBUSES', {})
    rebus = dict()
    # Check if REBUSES is a single item or a list
    if isinstance(rebus1, dict) and 'REBUS' in rebus1:
        rebus_items = rebus1['REBUS']
        if isinstance(rebus_items, dict):
            rebus_items = [rebus_items]
        for v in rebus_items:
            rebus[v['@input']] = v['@letters']

    # Circles: CFP stores indices of circled cells as a comma-separated string
    circles1 = cfpdata.get('CIRCLES', '-1')
    try:
        circles = set(map(int, circles1.split(',')))
    except ValueError:
        circles = set()


    # Grid construction
    grid = []
    # Remove newlines for linear indexing
    clean_grid_text = grid_text.replace('\n', '')
    for i, letter in enumerate(clean_grid_text):
        y = i // width
        x = i % width
        cell = {'x': x, 'y': y, 'value': None}
        
        # Check if this character is a rebus placeholder
        cell_value = rebus.get(letter, letter)
        
        # CFP uses '.' for black squares
        if cell_value == '.':
            cell_value = None
            cell['isBlock'] = True
        cell['solution'] = cell_value
        
        # Apply circle style if index is in the circles set
        if i in circles:
            cell['style'] = {"shapebg": "circle"}
        grid.append(cell)
    ret['grid'] = grid

    # Clue extraction
    # CFP stores clues in WORDS -> WORD elements
    ret_clues = [{'title': 'Across', 'clues': []}, {'title': 'Down', 'clues': []}]
    words = cfpdata.get('WORDS', {}).get('WORD', [])
    if isinstance(words, dict):
        words = [words]
        
    for c in words:
        clue = {'number': c.get('@num', ''), 'clue': c.get('#text', '')}
        # @dir is 'Across' or 'Down'
        is_down = c.get('@dir', '').lower() == 'down'
        this_ix = 1 if is_down else 0
        ret_clues[this_ix]['clues'].append(clue)
        
    ret['clues'] = ret_clues
    return ret
