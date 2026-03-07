import os
import pypuz

def test_unified_load():
    test_files = [
        '3x.puz',
        '3x.ipuz',
        '3x.jpz',
        '3x.cfp',
        '3x.xml'
    ]
    
    for filename in test_files:
        print(f"Testing unified load with {filename}...")
        path = os.path.join('pypuz', 'test_files', filename)
        puzzle = pypuz.load(path)
        assert puzzle is not None
        assert puzzle.metadata.title is not None
        # Check that clues were loaded
        assert len(puzzle.clues) > 0
        print(f"Successfully loaded {filename}")

if __name__ == "__main__":
    test_unified_load()
    print("\nUnified load tests passed!")
