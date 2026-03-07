"""
Functions for reading crossword data from AmuseLabs formats.
"""

import json
import base64

def read_amuselabs_data(s):
    """
    Read an AmuseLabs puzzle string and return a dictionary of puzzle data.

    Args:
        s (str): JSON string or base64 encoded JSON string containing AmuseLabs puzzle data.

    Returns:
        dict: A dictionary structured for use with the pypuz Puzzle class, containing
              'metadata', 'grid', and 'clues'.
    """
    # AmuseLabs data may be provided as a raw JSON string or base64 encoded
    try:
        data = json.loads(s)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # If decoding as JSON fails, try base64 decoding first
        s1 = base64.b64decode(s)
        data = json.loads(s1)

    ret = {}

    # Metadata extraction
    kind = "crossword"
    width, height = data['w'], data['h']
    ret['metadata'] = {
      'width': width
    , 'height': height
    , 'kind': kind
    , 'author': data.get('author')
    , 'title': data.get('title')
    , 'copyright': data.get('copyright')
    , 'noClueCells': True
    }

    # Grid construction
    grid = []
    box = data['box']
    cellInfos = data.get('cellInfos', [])
    
    # Reshape cellInfos to make lookup by (x, y) coordinates easier
    markup = {}
    for c in cellInfos:
        markup[(c['x'], c['y'])] = c
        
    for y in range(height):
        for x in range(width):
            cell = {'x': x, 'y': y, 'value': None}
            # AmuseLabs uses '\x00' to represent block cells
            if box[x][y] == '\x00':
                cell['isBlock'] = True
            else:
                cell['solution'] = box[x][y]
            
            # Apply cell styles (circles, walls/bars, etc.)
            style = {}
            if markup.get((x, y)):
                thisMarkup = markup[(x, y)]
                if thisMarkup.get('isCircled'):
                    style['shapebg'] = 'circle'
                if thisMarkup.get('isVoid'):
                    cell['isBlock'] = False
                    cell['isVoid'] = True
                
                # Check for barred walls (Bottom and Right)
                bar_string = ''
                for letter, side in {'B': 'bottom', 'R': 'right'}.items():
                    if thisMarkup.get(f'{side}Wall'):
                        bar_string += letter
                if bar_string:
                    style['barred'] = bar_string
                cell['style'] = style
            grid.append(cell)
    ret['grid'] = grid

    # Clue extraction and organization
    placed_words = data['placedWords']
    across_words = [word for word in placed_words if word['acrossNotDown']]
    down_words = [word for word in placed_words if not word['acrossNotDown']]
    
    # Ensure clues are sorted by grid position (top-to-bottom, left-to-right)
    across_words = sorted(across_words, key=lambda x: (x['y'], x['x']))
    down_words = sorted(down_words, key=lambda x: (x['y'], x['x']))
    
    across_clues = [{'number': str(x['clueNum']), 'clue': x['clue']['clue']} for x in across_words]
    down_clues = [{'number': str(x['clueNum']), 'clue': x['clue']['clue']} for x in down_words]
    
    ret['clues'] = [
        {'title': 'Across', 'clues': across_clues},
        {'title': 'Down', 'clues': down_clues}
    ]
    return ret
