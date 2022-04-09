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
    , 'noClueCells': True
    }

    # Read in rebus info, if available
    rebus1 = cfpdata.get('REBUSES', {})
    rebus = dict()
    for _, v in rebus1.items():
        rebus[v['@input']] = v['@letters']

    # Circle info, if available
    circles1 = cfpdata.get('CIRCLES', '-1')
    circles = set(map(int, circles1.split(',')))


    # Get the grid
    grid = []
    for i, letter in enumerate(grid_text.replace('\n', '')):
        y = i // width
        x = i % width
        cell = {'x': x, 'y': y, 'value': None}
        cell_value = rebus.get(letter, letter)
        # black squares
        if cell_value == '.':
            cell_value = None
            cell['isBlock'] = True
        cell['solution'] = cell_value
        # circles
        style = {}
        if i in circles:
            cell['style'] = {"shapebg": "circle"}
        grid.append(cell)
    ret['grid'] = grid

    ## Clues ##
    ret_clues = [{'title': 'Across', 'clues': []}, {'title': 'Down', 'clues': []}]
    for c in cfpdata.get('WORDS', {}).get('WORD', []):
        # {'number': number, 'clue': clue}
        clue = {'number': c.get('@num', ''), 'clue': c.get('#text', '')}
        this_ix = int(c['@dir'].lower() == 'down')
        ret_clues[this_ix]['clues'].append(clue)
    ret['clues'] = ret_clues
    return ret
