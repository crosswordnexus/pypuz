# pypuz

`pypuz` is a Python library for reading, writing, and manipulating crossword puzzle files. It provides a common interface for interacting with several popular crossword formats.

## Features

- **Multi-format Support**: Read and write (or convert between) various crossword formats.
- **Common Interface**: Access metadata, grids, and clues through a unified object model.
- **Automatic Numbering**: Generates standard crossword numbering for grids.
- **Clue Inference**: Can reconstruct clue answers from the grid if they are missing in the source file.
- **Rebus and Markup Support**: Handles special cell types like rebuses and circles.

## Supported Formats

- **.puz**: The classic Across Lite format.
- **.ipuz**: The open, JSON-based format (v1).
- **.jpz**: The XML-based format used by many modern applications.
- **.cfp**: CrossFire project files.
- **AmuseLabs**: Supports loading from AmuseLabs JSON data.

## Installation

```bash
pip install pypuz
```

Or using Poetry:

```bash
poetry add pypuz
```

## Basic Usage

### Loading a Puzzle

The easiest way to load a puzzle is using the `load` function, which automatically detects the format based on the file extension.

```python
import pypuz

# Load any supported file type (.puz, .ipuz, .jpz, .xml, .cfp)
puzzle = pypuz.load('my_puzzle.puz')

# Access metadata
print(f"Title: {puzzle.metadata.title}")
print(f"Author: {puzzle.metadata.author}")
```

You can also load specifically if needed (maintains backward compatibility):

```python
from pypuz import Puzzle

puzzle = Puzzle().fromPuz('my_puzzle.puz')
puzzle = Puzzle().fromIPuz('my_puzzle.ipuz')
```

### Inspecting the Grid

```python
# Access a specific cell
cell = puzzle.grid.cellAt(0, 0)
print(f"Solution at (0,0): {cell.solution}")

# Get the solution as a 2D array
arr = puzzle.grid.solutionArray()
```

### Accessing Clues

```python
for cluelist in puzzle.clues:
    print(f"\n{cluelist['title']}:")
    for clue in cluelist['clues']:
        print(f"{clue.number}. {clue.clue} -> {clue.answer}")
```

### Exporting to Another Format

```python
# Save as .ipuz
puzzle.toIPuz('output.ipuz')

# Save as .puz (Note: this format is lossy)
puzzle.toPuz('output.puz')
```

## Running Tests

Tests are located in the `tests/` directory and can be run with Python:

```bash
python tests/test_roundtrip.py
python tests/test_grid.py
python tests/test_file_types.py
```

## Development

To build the package:
```bash
poetry build
```

To install locally (after build):
```bash
pip install dist/pypuz-VERSION-py3-none-any.whl
```

To upload to PyPI:
```bash
twine upload dist/*
```

*Note: Remember to bump the version in `pyproject.toml` before making changes.*

## License

MIT
