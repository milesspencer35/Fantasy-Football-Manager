
import hashlib
from datetime import datetime, timedelta, timezone
from dateutil import parser, tz
from openai import OpenAI

ai_client = OpenAI()

class Article:
    def __init__(self, title: str, url: str, content: str, source: str, date: datetime):
        self.id = self._create_id_from_url(url)
        self.title = title
        self.url = url
        self.content = self._check_content_len(content)
        self.source = source
        self.date = date

    def _create_id_from_url(self, url):
        """Create a valid ID from URL using hash."""
        return hashlib.md5(url.encode()).hexdigest()

    def _check_content_len(self, content: str) -> str:
        if len(content) > 15000:
            return self._summarize_article(content)
        else:
            return content

    def _summarize_article(self, content):
        print("Summarizing article...")
        response = ai_client.responses.create(
            model="gpt-4o",
            input="""
            Provide a detailed and thorough summary of the following article. 
            Make sure to include any key points, statistics, and analysis.
            Make sure to preserve information about players, teams, and specific game details.
            Include the full player names. 
            Article:""" + content,
        )
        print("Article summarized: ", response.output_text)
        return response.output_text

    def is_recent_article(article_date, max_age_days=7):
        # """Check if article is within the specified age limit.""

        try:
            # If string — parse with dateutil (handles timezone abbreviations)
            if isinstance(article_date, str):
                article_datetime = parser.parse(article_date)
            else:
                article_datetime = article_date

            # Convert to UTC (or another fixed timezone)
            article_datetime = article_datetime.astimezone(tz.UTC)

            now = datetime.now(tz.UTC)
            cutoff = now - timedelta(days=max_age_days)

            is_recent = article_datetime >= cutoff
            if not is_recent:
                days_old = (now - article_datetime).days
                print(f"  ✗ Too old ({days_old} days)")
            return is_recent
        except Exception as e:
            print(f"  ✗ Error parsing date: {e}")
            return False