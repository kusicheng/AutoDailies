from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time


class WordleBot:
    """Bot to interact with the NYT Wordle game."""
    
    def __init__(self):
        self.url = "https://www.nytimes.com/games/wordle/index.html"
        self.driver = None
        self.driver_path = r"D:\ConnectionsGUI\FirefoxDriver\geckodriver.exe"
        self.guess_history = []
        
    def setup_driver(self):
        """Configure and initialize the Firefox driver."""
        service = Service(executable_path=self.driver_path)
        firefox_options = Options()
        firefox_options.add_argument("--incognito")
        firefox_options.add_argument("--start-maximized")
        
        self.driver = webdriver.Firefox(options=firefox_options, service=service)
        print("Navigating to Wordle website...")
        self.driver.get(self.url)
        
    def click_play_button(self):
        """Click the play button to start the game."""
        wait = WebDriverWait(self.driver, 10)
        play_xpath = "/html/body/div/div[2]/div[1]/div/div/div/div[2]/div/button[2]"
        
        play_button = wait.until(
            ec.element_to_be_clickable((By.XPATH, play_xpath))
        )
        play_button.click()
        print("Play button clicked, waiting for game to load...")
        time.sleep(2)
        
    def input_word(self, word: str):
        """Input a 5-letter word by simulating keyboard input."""
        word = word.lower()
        if len(word) != 5:
            raise ValueError(f"Word must be exactly 5 letters, got: {word}")
            
        # Simulate typing each letter
        for letter in word:
            self.driver.switch_to.active_element.send_keys(letter)
            time.sleep(0.1)
            
        # Press enter to submit
        self.driver.switch_to.active_element.send_keys(Keys.ENTER)
        print(f"Submitted word: {word.upper()}")
        
    def extract_row_state(self, row_index: int) -> list:
        """
        Extract the state of a single row (5 tiles).
        
        Args:
            row_index: 1-based row index (1-6)
            
        Returns:
            List of dicts with 'letter' and 'state' for each tile
        """
        wait = WebDriverWait(self.driver, 10)
        row_xpath = f"/html/body/div/div[2]/div[1]/div[4]/main/div[2]/div/div[{row_index}]"
        
        tiles = []
        for tile_index in range(1, 6):
            tile_xpath = f"{row_xpath}/div[{tile_index}]/div"
            
            try:
                tile_element = wait.until(
                    ec.presence_of_element_located((By.XPATH, tile_xpath))
                )
                
                letter = tile_element.text.strip().upper()
                state = tile_element.get_attribute("data-state")
                
                tiles.append({
                    "letter": letter,
                    "state": state  # "absent", "present", or "correct"
                })
            except Exception as e:
                print(f"Error extracting tile {tile_index}: {e}")
                tiles.append({"letter": "?", "state": "unknown"})
                
        return tiles
        
    def extract_game_state(self) -> dict:
        """
        Extract the current game state after a guess.
        
        Returns:
            Dict with 'rows' containing tile states and 'is_complete' boolean
        """
        wait = WebDriverWait(self.driver, 10)
        
        # Check for congratulations message
        is_complete = False
        try:
            congrats_xpath = "//h1[contains(@class, 'Header-module_regiwallText') and contains(text(), 'Congratulations')]"
            congrats_elements = self.driver.find_elements(By.XPATH, congrats_xpath)
            if congrats_elements:
                is_complete = True
                print("Game completed! Congratulations!")
        except Exception:
            pass
            
        # Extract all rows that have been filled
        rows = []
        for row_idx in range(1, 7):
            try:
                row_xpath = f"/html/body/div/div[2]/div[1]/div[4]/main/div[2]/div/div[{row_idx}]"
                row_element = self.driver.find_element(By.XPATH, row_xpath)
                
                # Check if row has content
                tiles = self.extract_row_state(row_idx)
                if tiles and any(t["letter"] for t in tiles):
                    rows.append(tiles)
            except Exception:
                break
                
        return {
            "rows": rows,
            "is_complete": is_complete
        }
        
    def format_feedback_for_api(self, game_state: dict) -> str:
        """
        Format the game state as a string for the API.
        
        Format:
        Guess 1: CRANE
        C (correct) R (absent) A (present) N (absent) E (absent)
        """
        feedback_lines = []
        
        for row_idx, row in enumerate(game_state["rows"], 1):
            word = "".join(tile["letter"] for tile in row)
            feedback_lines.append(f"Guess {row_idx}: {word}")
            
            state_parts = []
            for tile in row:
                letter = tile["letter"]
                state = tile["state"]
                state_parts.append(f"{letter} ({state})")
                
            feedback_lines.append(" | ".join(state_parts))
            
        return "\n".join(feedback_lines)
        
    def make_guess(self, word: str) -> dict:
        """
        Make a guess and return the resulting game state.
        
        Args:
            word: 5-letter word to guess
            
        Returns:
            Dict with game state after the guess
        """
        self.input_word(word)
        
        # Wait for animation to complete
        print("Waiting 5 seconds for animation...")
        time.sleep(5)
        
        game_state = self.extract_game_state()
        self.guess_history.append({
            "word": word,
            "result": game_state
        })
        
        return game_state
        
    def run(self) -> dict:
        """
        Run the bot to start the game and wait for first guess.
        
        Returns:
            Initial game state dict
        """
        try:
            print("Setting up driver...")
            self.setup_driver()
            
            print("Clicking play button...")
            self.click_play_button()
            
            print("Game ready for guesses...")
            return {"status": "ready", "rows": [], "is_complete": False}
            
        except Exception as e:
            print(f"Error running bot: {e}")
            raise
            
    def cleanup(self):
        """Close the driver."""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            print(f"Cleanup error: {e}")


if __name__ == "__main__":
    bot = WordleBot()
    try:
        bot.run()
        # Keep browser open for testing
        time.sleep(10)
    finally:
        bot.cleanup()
