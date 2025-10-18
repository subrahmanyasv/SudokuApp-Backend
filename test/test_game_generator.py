from src.Services.game_generator import generate_games
def test_game_generator():
    print("Game generation test started!")
    difficulty = 'easy'
    puzzles = generate_games(difficulty)
    print(len(puzzles))
    for puzzle in puzzles:
        print(puzzle)
    print("Game generation test ended")


test_game_generator()
