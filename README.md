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

To install the package for development:
```bash
poetry install
```

To install locally from a build:
```bash
poetry build
pip install dist/pypuz-VERSION-py3-none-any.whl
```

## Releasing

To make a new release of `pypuz`:

1.  **Merge to Main**: Ensure all changes are merged into the `main` (or `master`) branch.
2.  **Bump Version**: Update the `version` in `pyproject.toml` and document changes in `CHANGES.txt`.
3.  **Create a Release and Tag**:
    *   **Option A: CLI**:
        ```bash
        git checkout main
        git pull origin main
        git tag -a v2026.3.7 -m "Release version 2026.3.7"
        git push origin main --tags
        ```
    *   **Option B: GitHub UI**: Navigate to the "Releases" section of the repository, click "Draft a new release", and create a new tag (e.g., `v2026.3.7`) targeting the `main` branch. Use the contents of `CHANGES.txt` for the release description.
4.  **Publish to PyPI**:
    Regardless of how the Git tag is created, the package must be manually uploaded to PyPI (unless a GitHub Action is configured):
    ```bash
    poetry build
    twine upload dist/*
    ```
    *Note: PyPI authentication is independent of your local Git/GitHub user.*

## License

MIT
