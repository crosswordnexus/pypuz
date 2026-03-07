from pypuz.pypuz import Grid, Cell

def test_get_word():
    # Create a 3x1 grid
    cells = [
        Cell(0, 0, solution='A'),
        Cell(1, 0, solution='B'),
        Cell(2, 0, solution='C')
    ]
    grid = Grid(cells)
    
    # Test getting word from all cells
    assert grid.getWord([[0, 0], [1, 0], [2, 0]]) == 'ABC'
    
    # Test getting word from partial cells
    assert grid.getWord([[0, 0], [2, 0]]) == 'AC'
    
    # Test out of order cells
    assert grid.getWord([[2, 0], [0, 0], [1, 0]]) == 'CAB'
    
    # Test empty input
    assert grid.getWord([]) is None
    
    # Test None input
    assert grid.getWord(None) is None

def test_get_word_with_missing_solutions():
    cells = [
        Cell(0, 0, solution='A'),
        Cell(1, 0, solution=None),
        Cell(2, 0, solution='C')
    ]
    grid = Grid(cells)
    
    # Should skip None solutions
    assert grid.getWord([[0, 0], [1, 0], [2, 0]]) == 'AC'

if __name__ == "__main__":
    test_get_word()
    test_get_word_with_missing_solutions()
    print("Grid tests passed!")
