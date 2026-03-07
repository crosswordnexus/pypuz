"""
Functions for reading crossword data from JPZ (puzzle XML) files.
Support includes zipped JPZ files and various puzzle types like crossword, coded, and acrostic.
"""

import json
import re
from collections import OrderedDict, defaultdict
import xml.etree.ElementTree as ET
import zipfile
from lxml import etree

# via https://stackoverflow.com/a/51972010
def cleanup_namespaces(input_xml):
    """
    Remove namespace URIs from XML tags and attributes.
    
    This simplifies processing by allowing tag name lookups without 
    worrying about XML namespaces.

    Args:
        input_xml (bytes or str): The raw XML content.

    Returns:
        str: The XML content with namespaces removed, as a UTF-8 string.
    """
    root = etree.fromstring(input_xml)

    # Iterate through all XML elements
    for elem in root.getiterator():
        # Skip comments and processing instructions,
        # because they do not have names
        if not (
            isinstance(elem, etree._Comment)
            or isinstance(elem, etree._ProcessingInstruction)
        ):
            # Remove a namespace URI in the element's name
            elem.tag = etree.QName(elem).localname

    # Remove unused namespace declarations
    etree.cleanup_namespaces(root)
    return etree.tostring(root).decode('utf-8')

# courtesy of https://stackoverflow.com/a/32842402
def etree_to_ordereddict(t):
    """
    Convert an XML ElementTree into an OrderedDict.
    
    Special handling is included for 'clue' tags to preserve internal 
    XML tags as strings (e.g., for bold or italic formatting).

    Args:
        t (xml.etree.ElementTree.Element): The XML element to convert.

    Returns:
        OrderedDict: A dictionary representation of the XML tree.
    """
    d = OrderedDict()
    t_tag = t.tag
    d[t_tag] = OrderedDict() if t.attrib else None
    children = list(t)
    # Don't recurse into 'clue' children, as they contain formatted text
    if children and t_tag != 'clue':
        dd = OrderedDict()
        for dc in map(etree_to_ordereddict, children):
            for k1, v in dc.items():
                if k1 not in dd:
                    dd[k1] = list()
                dd[k1].append(v)
        d = OrderedDict()
        d[t_tag] = OrderedDict()
        for k1, v in dd.items():
            if len(v) == 1:
                d[t_tag][k1] = v[0]
            else:
                d[t_tag][k1] = v
    if t.attrib:
        d[t_tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t_tag]['#text'] = text
        else:
            d[t_tag] = text
    elif t_tag == 'clue':
        # Preserve internal formatting tags in clues by converting back to string
        d[t_tag]['#text'] = ''.join([ET.tostring(_).decode('utf-8') for _ in list(t)])
    return d


def read_jpzfile(f):
    """
    Read a JPZ file and return a dictionary of puzzle data.
    
    Handles both raw .jpz (XML) files and .jpz files wrapped in a ZIP container.

    Args:
        f (str): Path to the JPZ file.

    Returns:
        dict: A dictionary structured for use with the pypuz Puzzle class, containing
              'metadata', 'grid', and 'clues'.
    """
    ret = dict()
    # Try to open as a zip file first, as many JPZ files are actually zipped
    try:
        with zipfile.ZipFile(f, 'r') as myzip:
            this_file = myzip.namelist()[0]
            with myzip.open(this_file) as fid:
                xml = fid.read()
    except zipfile.BadZipFile:
        # If not a zip, read as a raw XML file
        with open(f, 'rb') as fid:
            xml = fid.read()
            
    # Clean namespaces and convert to dictionary
    tree = ET.XML(cleanup_namespaces(xml))
    jpzdata = etree_to_ordereddict(tree)
    # JPZ can have various root nodes; we skip the wrapper to find 'rectangular-puzzle'
    jpzdata = jpzdata[list(jpzdata.keys())[0]]
    jpzdata = jpzdata['rectangular-puzzle']

    # Identify the specific puzzle type
    CROSSWORD_TYPES = ['crossword', 'coded', 'acrostic']
    crossword_type = 'crossword'
    for ct in CROSSWORD_TYPES:
        if ct in jpzdata.keys():
            crossword_type = ct
            break

    # Metadata extraction
    kind = crossword_type
    metadata = jpzdata['metadata']
    ret['metadata'] = {
      'kind': kind
    , 'author': metadata.get('creator')
    , 'title': metadata.get('title')
    , 'copyright': metadata.get('copyright')
    , 'notes': metadata.get('description')
    }

    puzzle = jpzdata[crossword_type]
    grid1 = puzzle['grid']
    width = int(grid1['@width'])
    height = int(grid1['@height'])
    ret['metadata']['width'] = width
    ret['metadata']['height'] = height

    # Grid construction
    grid = []
    # JPZ grid coordinates are 1-based, pypuz uses 0-based
    for c in grid1['cell']:
        y = int(c['@y'])
        x = int(c['@x'])
        cell = {'x': x-1, 'y': y-1}
        value = c.get('@solve-state')
        solution = c.get('@solution')
        number = c.get('@number')
        
        # If there's a hint, we treat the solution as the current value
        if c.get('@hint'):
            value = solution

        # Special cell types
        if c.get('@type') == 'clue':
            value = solution

        if value:
            cell['value'] = value
        if solution:
            cell['solution'] = solution
        if number:
            cell['number'] = number

        # Block and Void cells
        if c.get('@type') == 'block':
            cell['isBlock'] = True
        elif c.get('@type') == 'void':
            cell['isEmpty'] = True
            
        # Style extraction
        style = {}
        # Background shape (e.g., circle)
        if c.get('@background-shape') == 'circle':
             style["shapebg"] = "circle"
        # Background color
        if c.get('@background-color'):
            style['color'] = c.get('@background-color').replace('#', '')
        # Barred walls (Top, Bottom, Left, Right)
        bar_string = ''
        for letter, side in {'T': 'top', 'B': 'bottom', 'L': 'left', 'R': 'right'}.items():
            if c.get(f'@{side}-bar'):
                bar_string += letter
        if bar_string:
            style['barred'] = bar_string
        # Secondary numbers (e.g., top-right)
        if c.get('@top-right-number'):
            style['mark'] = {"TR": c.get('@top-right-number')}

        cell['style'] = style
        grid.append(cell)
    ret['grid'] = grid

    # Clue and Word handling
    # In JPZ, "words" define the range of cells, and "clues" reference those words.

    def cells_from_xy(x, y):
        """
        Helper to convert JPZ coordinate strings (e.g., '1-3') into cell coordinates.
        """
        word_cells = []
        split_x = x.split('-')
        split_y = y.split('-')
        if len(split_x) > 1:
            # Horizontal word
            x_from, x_to = map(int, split_x)
            y1 = int(split_y[0])
            step = 1 if x_to >= x_from else -1
            for k in range(x_from, x_to + step, step):
                word_cells.append([k-1, y1-1])
        elif len(split_y) > 1:
            # Vertical word
            y_from, y_to = map(int, split_y)
            x1 = int(split_x[0])
            step = 1 if y_to >= y_from else -1
            for k in range(y_from, y_to + step, step):
                word_cells.append([x1-1, k-1])
        else:
            # Single cell word
            word_cells.append([int(split_x[0])-1, int(split_y[0])-1])
        return word_cells

    # Extract word definitions
    words = dict()
    words_arr = puzzle['word']
    if not isinstance(words_arr, list):
        words_arr = [words_arr]
    for w in words_arr:
        _id = w['@id']
        x = w.get('@x')
        y = w.get('@y')
        cells = []
        if x and y:
            cells = cells_from_xy(x, y)
        # Some JPZ files define words via child <cells> elements
        wc = w.get('cells', [])
        if isinstance(wc, OrderedDict):
            wc = [wc]
        for xy in wc:
            _x, _y = xy.get('@x'), xy.get('@y')
            new_cells = cells_from_xy(_x, _y)
            cells.extend(new_cells)
        words[_id] = cells

    # Extract clues
    clues = []
    # Coded crosswords don't have standard clues
    if crossword_type != 'coded':
        clues1 = puzzle['clues']
        if not isinstance(clues1, list):
            clues1 = [clues1]
        for clue_list in clues1:
            clue_el_title = clue_list.get('title')
            if isinstance(clue_el_title, OrderedDict):
                # Handle cases where title might be nested
                clue_el_title = list(clue_el_title.values())[0]
            clue_el_clues = clue_list.get('clue', [])
            if not isinstance(clue_el_clues, list):
                clue_el_clues = [clue_el_clues]
            
            this_clues = {'title': clue_el_title, 'clues': []}
            for c in clue_el_clues:
                number = c.get('@number')
                word_id = c.get('@word')
                clue_text = c.get('#text')
                # Optional format (length) string: e.g., "(5)"
                fmt = c.get('@format')
                if fmt:
                    clue_text = f"{clue_text} ({fmt})"
                cells = words[word_id]
                this_clues['clues'].append({
                    'number': number, 
                    'clue': clue_text, 
                    'cells': cells
                })
            clues.append(this_clues)

    ret['clues'] = clues
    return ret
