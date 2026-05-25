from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

class ConnectionsBot:
    #__init__ initialize bot with firefox options
    def __init__(self):
        self.url = "https://www.nytimes.com/games/connections"
        self.driver = None
        self.driver_path = r"D:\ConnectionsGUI\FirefoxDriver\geckodriver.exe"
        self.words = []

    #setup_driver configure firefox driver with incognito mode
    def setup_driver(self):
        service = Service(executable_path=self.driver_path)
        firefox_options = Options()
        #add_argument enable incognito mode
        firefox_options.add_argument("--incognito")
        #add_argument run in full screen
        firefox_options.add_argument("--start-maximized")
        
        self.driver = webdriver.Firefox(options=firefox_options, service=service)
        print("get website")
        self.driver.get(self.url)
        
    #click_play_button find and click the play button using xpath
    def click_play_button(self):
        #if xpath breaks then update or use css
        wait = WebDriverWait(self.driver, 10)
        play_xpath = "/html/body/div[3]/div[2]/div[2]/div[6]/div[3]/div/div[1]/div/div/div/div/div[2]/div/button[1]"
        
        play_button = wait.until(
            ec.element_to_be_clickable((By.XPATH, play_xpath))
        )
        #click execute click action
        play_button.click()
        #sleep wait for game board to load
        time.sleep(1)
        
    #extract_words get all 16 words from the game board
    def extract_words(self):
        wait = WebDriverWait(self.driver, 10)
        container_xpath = "/html/body/div[3]/div[2]/div[2]/div[6]/div[3]/div/div[1]/article/form/fieldset/div/div"
        
        #wait for container to be present
        container = wait.until(
            ec.presence_of_element_located((By.XPATH, container_xpath))
        )
        
        #get all label elements within container
        labels = container.find_elements(By.TAG_NAME, "label")
        
        self.words = []
        for i, label in enumerate(labels):
            #text extract word text
            word = label.text.strip()
            if word:
                self.words.append(word)
                print(f"[{i+1}] {word}")
                
        return self.words
        
    #run execute full bot workflow
    def run(self):
        try:
            print("setup_driver starting firefox...")
            self.setup_driver()
            
            print("click_play_button waiting for play button...")
            self.click_play_button()
            
            print("extract_words extracting words...")
            words = self.extract_words()
            
            print(f"\nrun extracted {len(words)} words")
            return words
            
        except Exception as e:
            print(f"run error: {e}")
            raise
            
    #cleanup close driver
    def cleanup(self):
        try:
            self.driver.quit()
        except Exception as e:
            print(f"cleanup error: {e}")


#__main__ entry point
if __name__ == "__main__":
    bot = ConnectionsBot()
    try:
        bot.run()
        #sleep keep browser open for user to see
        time.sleep(5)
    finally:
        bot.cleanup()
