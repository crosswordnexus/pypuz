import os
from pypuz.pypuz import Puzzle

def test_file_load(filename, loader_name):
    print(f"Testing {loader_name} with {filename}...")
    puz_file = os.path.join('pypuz', 'test_files', filename)
    
    puzzle = None
    if loader_name == 'fromPuz':
        puzzle = Puzzle().fromPuz(puz_file)
    elif loader_name == 'fromIPuz':
        puzzle = Puzzle().fromIPuz(puz_file)
    elif loader_name == 'fromJPZ':
        puzzle = Puzzle().fromJPZ(puz_file)
    elif loader_name == 'fromCFP':
        puzzle = Puzzle().fromCFP(puz_file)
    
    assert puzzle is not None, f"Failed to load {filename} using {loader_name}"
    
    # Check that clues have answers
    for cluelist in puzzle.clues:
        for clue in cluelist['clues']:
            assert clue.answer is not None, f"Clue {clue.number} has no answer in {filename}"
            assert len(clue.answer) > 0, f"Clue {clue.number} has empty answer in {filename}"
    print(f"Success for {filename}!")

def test_all_files():
    test_file_load('3x.puz', 'fromPuz')
    test_file_load('3x.ipuz', 'fromIPuz')
    test_file_load('3x.jpz', 'fromJPZ')
    test_file_load('3x.cfp', 'fromCFP')

if __name__ == "__main__":
    test_all_files()
    print("\nAll file type tests passed!")
