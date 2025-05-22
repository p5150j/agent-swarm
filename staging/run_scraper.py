
from agent_profile_scraper import AgentProfileScraper
import logging

# who do you want to clone?
PROFILE_NAME = "Mahatma Gandhi Indian lawyer"


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraping.log'),
            logging.StreamHandler()
        ]
    )
    
    # Initialize and run the scraper
    scraper = AgentProfileScraper(PROFILE_NAME)
    profile_path = scraper.run()
    
    print(f"\nProfile has been generated at: {profile_path}")
    print(f"\nYou can find the raw data in: raw_data/{PROFILE_NAME}")
    print(f"Processed data in: processed_data/{PROFILE_NAME}")
    print(f"And the final profile in: profiles/{PROFILE_NAME}")

if __name__ == "__main__":
    main() 