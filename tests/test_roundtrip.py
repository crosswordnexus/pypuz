import os
from pypuz.pypuz import Puzzle

def test_clue_answer():
    puz_file = os.path.join('pypuz', 'test_files', '3x.puz')
    puzzle = Puzzle().fromPuz(puz_file)
    
    print(f"Testing puzzle: {puz_file}")
    for cluelist in puzzle.clues:
        print(f"\n{cluelist['title']}:")
        for clue in cluelist['clues']:
            print(f"{clue.number}. {clue.clue} -> {clue.answer}")
            assert clue.answer is not None, f"Answer for clue {clue.number} is None"
            assert len(clue.answer) > 0, f"Answer for clue {clue.number} is empty"

    # Test toIPuz and fromIPuz roundtrip for answer
    ipuz_file = 'test_temp.ipuz'
    puzzle.toIPuz(ipuz_file)
    
    puzzle2 = Puzzle().fromIPuz(ipuz_file)
    print(f"\nTesting roundtrip from IPuz:")
    for cluelist in puzzle2.clues:
        print(f"\n{cluelist['title']}:")
        for clue in cluelist['clues']:
            print(f"{clue.number}. {clue.clue} -> {clue.answer}")
            assert clue.answer is not None, f"Answer for clue {clue.number} is None after roundtrip"

    os.remove(ipuz_file)
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_clue_answer()
