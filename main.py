import sys
from connections_extractor import ConnectionsBot
from wordle_extractor import WordleBot
from api import call_gemini_connections, call_gemini_wordle
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QVBoxLayout, 
    QPushButton, 
    QTextEdit, 
    QLabel,
)
from PyQt6.QtCore import QThread, pyqtSignal


class SolverWorker(QThread):
    """Worker thread to run the solver without blocking the GUI."""
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            result = solve_connections()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class WordleSolverWorker(QThread):
    """Worker thread to run the Wordle solver without blocking the GUI."""
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    update = pyqtSignal(str) #signal for progress updates
    
    def run(self):
        try:
            # Pass a callable to Wordle solver so it can emit progress updates
            result = solve_wordle(self.update.emit)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


def solve_connections() -> str:
    """
    Extract words from Connections game and solve using gemini 2.5.
    
    Returns:
        str: The solution as a formatted string
    """
    bot = ConnectionsBot()
    try:
        # Extract words from the game
        words = bot.run()
        
        if not words:
            return "No words extracted from the game."
        
        # Call the API to solve
        solution = call_gemini_connections(words)
        
        # Format the solution for display
        return format_solution(solution)
        
    finally:
        bot.cleanup()


def format_solution(solution: dict) -> str:
    """Format the solution dictionary for display."""
    import json
    if "raw_response" in solution:
        return solution["raw_response"]
    return json.dumps(solution, indent=2)


def solve_wordle(update_callback=None) -> str:
    """
    Solve the Wordle game using Gemini 2.5 for suggestions.
    
    Args:
        update_callback: Optional callback function for progress updates
        
    Returns:
        str: The final result as a formatted string
    """
    import json
    bot = WordleBot()
    max_guesses = 6
    
    def update(msg):
        if update_callback:
            update_callback(msg)
        print(msg)
    
    try:
        # Start the game
        update("Starting Wordle game...")
        bot.run()
        
        guess_count = 0
        
        while guess_count < max_guesses:
            guess_count += 1
            update(f"\n--- Guess {guess_count} ---")
            
            # Get feedback from previous guesses
            if bot.guess_history:
                feedback = bot.format_feedback_for_api(bot.guess_history[-1]["result"])
            else:
                feedback = "No previous guesses. This is the first guess."
            
            # Get suggestion from API
            update("Getting word suggestion from Gemini...")
            suggestion = call_gemini_wordle(feedback)
            
            # Extract the suggested word
            if "suggested_word" in suggestion:
                word = suggestion["suggested_word"].upper()
            elif "raw_response" in suggestion:
                update(f"Raw response: {suggestion['raw_response']}")
                # Try to extract word from raw response
                word = "CRANE"  # Default starting word
            else:
                update(f"Unexpected response: {suggestion}")
                word = "CRANE"
            
            # Ensure word is 5 letters
            word = word[:5].upper()
            if len(word) < 5:
                word = word.ljust(5, 'A')
            
            update(f"Suggested word: {word}")
            if "reasoning" in suggestion:
                update(f"Reasoning: {suggestion['reasoning']}")
            
            # Make the guess
            update(f"Submitting guess: {word}")
            game_state = bot.make_guess(word)
            
            # Check if game is complete
            if game_state["is_complete"]:
                result = f"\n🎉 SUCCESS! Word found in {guess_count} guesses!\n"
                result += f"The word was: {word}\n\n"
                result += "Guess history:\n"
                for i, guess in enumerate(bot.guess_history, 1):
                    result += f"  {i}. {guess['word'].upper()}\n"
                return result
            
        # If we get here, we didn't find the word
        result = f"\n❌ Failed to find the word in {max_guesses} guesses.\n"
        result += "Guess history:\n"
        for i, guess in enumerate(bot.guess_history, 1):
            result += f"  {i}. {guess['word'].upper()}\n"
        return result
        
    finally:
        bot.cleanup()


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NYT Games Solver")
        self.setMinimumSize(500, 400)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title label
        title_label = QLabel("NYT Games Solver")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Solve Connections button
        self.solve_button = QPushButton("Solve Connections")
        self.solve_button.setMinimumHeight(40)
        self.solve_button.clicked.connect(self.start_solving)
        layout.addWidget(self.solve_button)
        
        # Solve Wordle button
        self.solve_wordle_button = QPushButton("Solve Wordle")
        self.solve_wordle_button.setMinimumHeight(40)
        self.solve_wordle_button.clicked.connect(self.start_solving_wordle)
        layout.addWidget(self.solve_wordle_button)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Click a button to start solving...")
        layout.addWidget(self.results_text)
        
        # Worker thread references
        self.worker = None
        self.wordle_worker = None
    
    def start_solving(self):
        """Start the Connections solving process in a background thread."""
        self.solve_button.setEnabled(False)
        self.solve_wordle_button.setEnabled(False)
        self.results_text.setText("Extracting words and solving...")
        
        # Create and start worker thread
        self.worker = SolverWorker()
        self.worker.finished.connect(self.on_solved)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def start_solving_wordle(self):
        """Start the Wordle solving process in a background thread."""
        self.solve_button.setEnabled(False)
        self.solve_wordle_button.setEnabled(False)
        self.results_text.setText("Starting Wordle solver...")
        
        # Create and start worker thread
        self.wordle_worker = WordleSolverWorker()
        self.wordle_worker.finished.connect(self.on_wordle_solved)
        self.wordle_worker.error.connect(self.on_error)
        self.wordle_worker.update.connect(self.on_wordle_update)
        self.wordle_worker.start()
    
    def on_wordle_update(self, message: str):
        """Handle progress updates from Wordle solver."""
        current_text = self.results_text.toPlainText()
        self.results_text.setText(current_text + "\n" + message)
    
    def on_wordle_solved(self, result: str):
        """Handle successful Wordle solving."""
        current_text = self.results_text.toPlainText()
        self.results_text.setText(current_text + "\n" + result)
        self.solve_button.setEnabled(True)
        self.solve_wordle_button.setEnabled(True)
    
    def on_solved(self, result: str):
        """Handle successful solving."""
        self.results_text.setText(result)
        self.solve_button.setEnabled(True)
        self.solve_wordle_button.setEnabled(True)
    
    def on_error(self, error_msg: str):
        """Handle solving error."""
        self.results_text.setText(f"Error: {error_msg}")
        self.solve_button.setEnabled(True)
        self.solve_wordle_button.setEnabled(True)


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
