import json
import base64

def read_amuselabs_data(s):
    """
    Read in an amuselabs string, return a dictionary of data
    """
    # Data might be base64'd or not
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        s1 = base64.b64decode(s)
        data = json.loads(s1)

    ret = {}

    # metadata
    # technically these can be codewords but i've never seen one
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
    # no notepad?
    }

    # grid
    grid = []
    box = data['box']
    cellInfos = data.get('cellInfos', [])
    # Reshape cellInfos to make lookup easier
    markup = {}
    for c in cellInfos:
        markup[(c['x'], c['y'])] = c
    for y in range(height):
        for x in range(width):
            cell = {'x': x, 'y': y, 'value': None}
            if box[x][y] == '\x00':
                cell['isBlock'] = True
            else:
                cell['solution'] = box[x][y]
            style = {}
            if markup.get((x, y)):
                thisMarkup = markup[(x, y)]
                if thisMarkup.get('isCircled'):
                    style['shapebg'] = 'circle'
                if thisMarkup.get('isVoid'):
                    cell['isBlock'] = False
                    cell['isVoid'] = True
                bar_string = ''
                for letter, side in {'B': 'bottom', 'R': 'right'}.items():
                    if thisMarkup.get(f'{side}Wall'):
                        bar_string += letter
                if bar_string:
                    style['barred'] = bar_string
                cell['style'] = style
            grid.append(cell)
    ret['grid'] = grid

    # clues
    placed_words = data['placedWords']
    across_words = [word for word in placed_words if word['acrossNotDown']]
    down_words = [word for word in placed_words if not word['acrossNotDown']]
    # sorting is probably unnecessary
    across_words = sorted(across_words, key=lambda x: (x['y'], x['x']))
    down_words = sorted(down_words, key=lambda x: (x['y'], x['x']))
    across_clues = [{'number': str(x['clueNum']), 'clue': x['clue']['clue']} for x in across_words]
    down_clues = [{'number': str(x['clueNum']), 'clue': x['clue']['clue']} for x in down_words]
    ret['clues'] = [{'title': 'Across', 'clues': across_clues}, {'title': 'Down', 'clues': down_clues}]
    return ret
