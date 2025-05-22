import os
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import tweepy
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from datetime import datetime
import logging
from typing import Dict, List, Optional
import re
from pathlib import Path
from urllib.parse import quote_plus
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import nltk

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Try to import whisper, but make it optional
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available. Video transcription will be disabled falling back to youtube transcripts.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)

class AgentProfileScraper:
    def __init__(self, name: str, config_path: str = "config.json"):
        self.name = name
        self.config_path = config_path
        self.base_dir = Path(".")  # Use current directory instead of "staging"
        self.raw_data_dir = self.base_dir / "raw_data" / name
        self.processed_data_dir = self.base_dir / "processed_data" / name
        self.profiles_dir = self.base_dir / "profiles" / name
        
        # Create necessary directories
        for directory in [self.raw_data_dir, self.processed_data_dir, self.profiles_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.load_config()
        
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                "twitter_api_key": "",
                "twitter_api_secret": "",
                "twitter_access_token": "",
                "twitter_access_token_secret": "",
                "search_engines": ["google", "bing"],
                "max_results": 50,
                "video_download": True,
                "transcribe_videos": True
            }
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
    
    def search_web(self) -> List[Dict]:
        """Search the web for information about the person using multiple sources"""
        results = []
        
        # Define a smaller set of focused search queries
        search_queries = [
            f"{self.name} interview biography",
            f"{self.name} career achievements",
            f"{self.name} business ventures",
            f"{self.name} philanthropy"
        ]
        # date filtering if needed
        date_filter = "cdr:1,cd_min:1/1/2010,cd_max:12/31/2025"
        
        logging.info("Initializing Chrome WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            logging.info("Chrome WebDriver initialized successfully")
            
            # Process each search query
            for i, search_query in enumerate(search_queries, 1):
                logging.info(f"Processing search query {i}/{len(search_queries)}: {search_query}")
                encoded_query = quote_plus(search_query)
                
                # Search Google News
                logging.info(f"Searching Google News for: {search_query}")
                news_url = f"https://www.google.com/search?q={encoded_query}&tbm=nws&tbs={date_filter}"
                driver.get(news_url)
                time.sleep(2)
                
                # Extract news results
                news_results = driver.find_elements(By.CSS_SELECTOR, "div.SoaBEf")
                logging.info(f"Found {len(news_results)} news results")
                for result in news_results[:5]:  # Limit to 5 results per query
                    try:
                        link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        title = result.find_element(By.CSS_SELECTOR, "div.n0jPhd").text
                        snippet = result.find_element(By.CSS_SELECTOR, "div.GI74Re").text
                        date = result.find_element(By.CSS_SELECTOR, "div.LfVVr").text
                        
                        results.append({
                            "type": "article",
                            "url": link,
                            "title": title,
                            "snippet": snippet,
                            "date": date,
                            "source": "google_news",
                            "query": search_query
                        })
                    except Exception as e:
                        logging.warning(f"Error extracting news result: {str(e)}")
                
                # Search regular Google with date filter
                logging.info(f"Searching Google for: {search_query}")
                google_url = f"https://www.google.com/search?q={encoded_query}&tbs={date_filter}"
                driver.get(google_url)
                time.sleep(2)
                
                # Extract search results
                search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")
                logging.info(f"Found {len(search_results)} Google results")
                for result in search_results[:5]:  # Limit to 5 results per query
                    try:
                        link = result.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        title = result.find_element(By.CSS_SELECTOR, "h3").text
                        snippet = result.find_element(By.CSS_SELECTOR, "div.VwiC3b").text
                        
                        # Determine content type
                        content_type = "article"
                        if any(video_site in link.lower() for video_site in ["youtube.com", "vimeo.com"]):
                            content_type = "video"
                        elif any(social_site in link.lower() for social_site in ["twitter.com", "linkedin.com", "facebook.com"]):
                            content_type = "social"
                        
                        results.append({
                            "type": content_type,
                            "url": link,
                            "title": title,
                            "snippet": snippet,
                            "source": "google",
                            "query": search_query
                        })
                    except Exception as e:
                        logging.warning(f"Error extracting Google result: {str(e)}")
                
                # Search YouTube with date filter
                logging.info(f"Searching YouTube for: {search_query}")
                youtube_query = f"{encoded_query}&sp=EgIYAQ%253D%253D"
                youtube_url = f"https://www.youtube.com/results?search_query={youtube_query}"
                driver.get(youtube_url)
                time.sleep(2)
                
                video_results = driver.find_elements(By.CSS_SELECTOR, "ytd-video-renderer")
                logging.info(f"Found {len(video_results)} YouTube results")
                for video in video_results[:3]:  # Limit to 3 results per query
                    try:
                        link = video.find_element(By.CSS_SELECTOR, "a#video-title").get_attribute("href")
                        title = video.find_element(By.CSS_SELECTOR, "a#video-title").text
                        channel = video.find_element(By.CSS_SELECTOR, "ytd-channel-name a").text
                        
                        results.append({
                            "type": "video",
                            "url": link,
                            "title": title,
                            "channel": channel,
                            "source": "youtube",
                            "query": search_query
                        })
                    except Exception as e:
                        logging.warning(f"Error extracting YouTube result: {str(e)}")
                
                logging.info(f"Completed search query {i}/{len(search_queries)}")
            
        except Exception as e:
            logging.error(f"Error in web search: {str(e)}")
            raise
        finally:
            try:
                driver.quit()
            except:
                pass
        
        # Remove duplicates based on URL
        unique_results = []
        seen_urls = set()
        for result in results:
            if result["url"] not in seen_urls:
                seen_urls.add(result["url"])
                unique_results.append(result)
        
        logging.info(f"Found {len(unique_results)} unique results for {self.name}")
        return unique_results
    
    def extract_article_content(self, url: str) -> Dict:
        """Extract content from a news article"""
        try:
            # Skip Forbes articles as they block our requests
            if "forbes.com" in url:
                logging.warning(f"Skipping Forbes article: {url}")
                return {}
                
            article = Article(url)
            article.download()
            article.parse()
            
            # Skip NLP processing since it's causing issues with punkt
            return {
                "title": article.title,
                "text": article.text,
                "summary": "",  # Skip summary since it requires NLP
                "keywords": [],  # Skip keywords since it requires NLP
                "publish_date": article.publish_date,
                "url": url
            }
        except Exception as e:
            logging.error(f"Error extracting article content from {url}: {str(e)}")
            return {}
    
    def download_video(self, video_url: str) -> Optional[str]:
        """Download video content"""
        if not self.config["video_download"]:
            return None
            
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': str(self.raw_data_dir / f'video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4')
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
                return ydl_opts['outtmpl']
        except Exception as e:
            logging.error(f"Error downloading video from {video_url}: {str(e)}")
            return None
    
    def transcribe_video(self, video_url: str) -> Optional[str]:
        """Transcribe video content using YouTube's transcript API"""
        if not self.config["transcribe_videos"]:
            logging.info("Video transcription is disabled")
            return None
            
        try:
            # Extract video ID from URL
            video_id = None
            if "youtube.com" in video_url or "youtu.be" in video_url:
                if "youtube.com" in video_url:
                    video_id = video_url.split("v=")[1].split("&")[0]
                else:  # youtu.be
                    video_id = video_url.split("/")[-1]
                
                # Get transcript
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                # Combine all transcript pieces
                full_text = " ".join([entry["text"] for entry in transcript])
                return full_text
            else:
                logging.info(f"Video URL {video_url} is not a YouTube video, skipping transcription")
                return None
                
        except Exception as e:
            logging.error(f"Error transcribing video {video_url}: {str(e)}")
            return None
    
    def analyze_content(self, content: List[Dict]) -> Dict:
        """Analyze content to extract personality traits and characteristics"""
        analysis = {
            "goals": [],
            "motivations": [],
            "behaviors": [],
            "pain_points": [],
            "communication_style": [],
            "tone": [],
            "practical_advice": []
        }
        
        # Keywords and patterns for different categories
        patterns = {
            "goals": [
                r"aims to", r"goal is to", r"wants to", r"seeks to", r"strives to",
                r"objective is", r"mission is", r"vision is", r"aspires to"
            ],
            "motivations": [
                r"motivated by", r"driven by", r"inspired by", r"passionate about",
                r"believes in", r"values", r"cares about", r"dedicated to"
            ],
            "behaviors": [
                r"always", r"typically", r"usually", r"often", r"frequently",
                r"known for", r"characteristically", r"consistently"
            ],
            "pain_points": [
                r"challenge", r"struggle", r"difficulty", r"problem", r"issue",
                r"concern", r"worry", r"frustration", r"obstacle"
            ],
            "communication_style": [
                r"speaks", r"communicates", r"expresses", r"articulates",
                r"presents", r"conveys", r"shares", r"discusses"
            ],
            "tone": [
                r"tone", r"manner", r"style", r"approach", r"attitude",
                r"demeanor", r"personality", r"character"
            ],
            "practical_advice": [
                r"advice", r"recommendation", r"suggestion", r"tip",
                r"guidance", r"insight", r"lesson", r"wisdom"
            ]
        }
        
        # Process each content item
        for item in content:
            text = ""
            if "text" in item:
                text = item["text"]
            elif "snippet" in item:
                text = item["snippet"]
            elif "title" in item:
                text = item["title"]
            
            if not text:
                continue
            
            # Convert to lowercase for case-insensitive matching
            text_lower = text.lower()
            
            # Extract sentences containing relevant patterns
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Check each category's patterns
                for category, category_patterns in patterns.items():
                    for pattern in category_patterns:
                        if re.search(pattern, sentence.lower()):
                            # Clean and format the sentence
                            cleaned_sentence = re.sub(r'\s+', ' ', sentence).strip()
                            if cleaned_sentence and len(cleaned_sentence) > 10:  # Avoid very short matches
                                if cleaned_sentence not in analysis[category]:
                                    analysis[category].append(cleaned_sentence)
        
        # Remove duplicates and sort
        for category in analysis:
            analysis[category] = sorted(list(set(analysis[category])))
        
        # If any category is empty, add a default message
        for category in analysis:
            if not analysis[category]:
                analysis[category].append(f"No specific {category} identified in the content.")
        
        return analysis
    
    def generate_profile(self, analysis: Dict) -> str:
        """Generate markdown profile from analysis"""
        profile = f"""# {self.name} - Agent Profile

## Goals
{chr(10).join(f"- {goal}" for goal in analysis['goals'])}

## Motivations
{chr(10).join(f"- {motivation}" for motivation in analysis['motivations'])}

## Behaviors
{chr(10).join(f"- {behavior}" for behavior in analysis['behaviors'])}

## Pain Points
{chr(10).join(f"- {pain_point}" for pain_point in analysis['pain_points'])}

## Communication Style
{chr(10).join(f"- {style}" for style in analysis['communication_style'])}

## Tone
{chr(10).join(f"- {tone}" for tone in analysis['tone'])}

## Practical Advice
{chr(10).join(f"- {advice}" for advice in analysis['practical_advice'])}

## Sources
*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        return profile
    
    def run(self):
        """Main execution method"""
        logging.info(f"Starting profile scraping for {self.name}")
        
        # Search web for content
        search_results = self.search_web()
        
        # Process each result
        processed_content = []
        for result in search_results:
            if result.get("type") == "article":
                content = self.extract_article_content(result["url"])
                processed_content.append(content)
            elif result.get("type") == "video":
                video_path = self.download_video(result["url"])
                if video_path:
                    transcript = self.transcribe_video(result["url"])
                    if transcript:
                        processed_content.append({
                            "type": "video_transcript",
                            "text": transcript,
                            "url": result["url"]
                        })
        
        # Analyze content
        analysis = self.analyze_content(processed_content)
        
        # Generate profile
        profile = self.generate_profile(analysis)
        
        # Save profile
        profile_path = self.profiles_dir / f"{self.name.lower().replace(' ', '_')}_profile.md"
        with open(profile_path, 'w') as f:
            f.write(profile)
        
        logging.info(f"Profile generation completed for {self.name}")
        return profile_path

if __name__ == "__main__":
    # Example usage
    scraper = AgentProfileScraper("Frank McCourt")
    profile_path = scraper.run()
    print(f"Profile generated at: {profile_path}") 