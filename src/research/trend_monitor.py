"""
Trending Space Topics Monitor
Detects hot topics from multiple sources for timely content creation
"""

import requests
from datetime import datetime, timedelta
from pathlib import Path
import json


class TrendMonitor:
    """Monitors trending space topics across multiple platforms"""

    def __init__(self):
        self.output_dir = Path("research/trends")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def check_reddit_trends(self, subreddits=['space', 'astronomy', 'NASA', 'Astrophysics']):
        """Check trending posts on space-related subreddits"""

        print("\n🔴 REDDIT TRENDING TOPICS")
        print("=" * 60)

        trends = []

        for subreddit in subreddits:
            try:
                # Reddit JSON API (no auth needed for public data)
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                headers = {'User-Agent': 'Mozilla/5.0 (compatible; TrendBot/1.0)'}

                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    posts = data['data']['children']

                    print(f"\n📱 r/{subreddit}:")

                    for post in posts[:5]:  # Top 5
                        post_data = post['data']

                        trend = {
                            'source': f'r/{subreddit}',
                            'title': post_data['title'],
                            'upvotes': post_data['ups'],
                            'comments': post_data['num_comments'],
                            'url': f"https://reddit.com{post_data['permalink']}",
                            'created': post_data['created_utc']
                        }

                        trends.append(trend)

                        print(f"   ⬆️  {trend['upvotes']:,} | 💬 {trend['comments']:,} | {trend['title'][:60]}...")

                else:
                    print(f"   ❌ Failed to fetch r/{subreddit}")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        return trends

    def check_nasa_news(self):
        """Check latest NASA news and announcements"""

        print("\n🚀 NASA LATEST NEWS")
        print("=" * 60)

        news_items = []

        try:
            # NASA RSS feed (public)
            url = "https://www.nasa.gov/rss/dyn/breaking_news.rss"
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; TrendBot/1.0)'}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                # Parse RSS (basic parsing)
                import re

                # Extract items from RSS
                items = re.findall(r'<item>(.*?)</item>', response.text, re.DOTALL)

                for item in items[:10]:  # Top 10
                    title_match = re.search(r'<title>(.*?)</title>', item)
                    link_match = re.search(r'<link>(.*?)</link>', item)
                    pubdate_match = re.search(r'<pubDate>(.*?)</pubDate>', item)

                    if title_match:
                        news_item = {
                            'source': 'NASA',
                            'title': title_match.group(1),
                            'url': link_match.group(1) if link_match else '',
                            'date': pubdate_match.group(1) if pubdate_match else ''
                        }

                        news_items.append(news_item)
                        print(f"   📰 {news_item['title']}")
            else:
                print(f"   ❌ Failed to fetch NASA news")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        return news_items

    def check_google_news(self, query="space astronomy"):
        """Check Google News for space stories"""

        print(f"\n📰 GOOGLE NEWS: '{query}'")
        print("=" * 60)

        # Note: Google News RSS is public
        news_items = []

        try:
            url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; TrendBot/1.0)'}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                import re

                # Extract items from RSS
                items = re.findall(r'<item>(.*?)</item>', response.text, re.DOTALL)

                for item in items[:10]:  # Top 10
                    title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
                    link_match = re.search(r'<link>(.*?)</link>', item)

                    if title_match:
                        news_item = {
                            'source': 'Google News',
                            'title': title_match.group(1),
                            'url': link_match.group(1) if link_match else ''
                        }

                        news_items.append(news_item)
                        print(f"   📰 {news_item['title']}")
            else:
                print(f"   ❌ Failed to fetch Google News")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        return news_items

    def analyze_trends(self, reddit_trends, nasa_news, google_news):
        """Analyze all trends and extract common themes"""

        print("\n🔍 TREND ANALYSIS")
        print("=" * 60)

        # Combine all titles
        all_titles = []
        all_titles.extend([t['title'] for t in reddit_trends])
        all_titles.extend([n['title'] for n in nasa_news])
        all_titles.extend([n['title'] for n in google_news])

        # Extract keywords
        text = ' '.join(all_titles).lower()

        # Common space keywords to track
        keywords = {
            'black hole': text.count('black hole'),
            'mars': text.count('mars'),
            'moon': text.count('moon'),
            'asteroid': text.count('asteroid'),
            'exoplanet': text.count('exoplanet'),
            'james webb': text.count('james webb') + text.count('jwst'),
            'spacex': text.count('spacex'),
            'nasa': text.count('nasa'),
            'supernova': text.count('supernova'),
            'galaxy': text.count('galaxy') + text.count('galaxies'),
            'dark matter': text.count('dark matter'),
            'dark energy': text.count('dark energy'),
            'neutron star': text.count('neutron star'),
            'jupiter': text.count('jupiter'),
            'saturn': text.count('saturn'),
            'discovery': text.count('discover') + text.count('found'),
            'mystery': text.count('mystery') + text.count('mysterious'),
        }

        # Sort by frequency
        trending_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)

        print("\n🔥 HOT KEYWORDS (mentions in trending content):")
        for keyword, count in trending_keywords[:10]:
            if count > 0:
                print(f"   {keyword.title()}: {count} mentions")

        return trending_keywords

    def generate_timely_topics(self, trending_keywords, watop_patterns=None):
        """Generate topics based on current trends"""

        print("\n💡 TIMELY TOPIC SUGGESTIONS")
        print("=" * 60)

        topics = []

        # Get top trending keywords
        hot_topics = [kw[0] for kw in trending_keywords[:5] if kw[1] > 0]

        if not hot_topics:
            print("   ⚠️  No strong trends detected. Using evergreen topics.")
            return []

        # WATOP-style templates for trending topics
        templates = [
            "What Scientists Just Discovered About {topic}",
            "The Truth About {topic} That NASA Doesn't Want You To Know",
            "{topic}: What They're Not Telling You",
            "Why {topic} Is More Dangerous Than You Think",
            "The Mystery of {topic} Finally Solved",
            "{topic} Just Did Something Impossible",
            "Scientists Are Terrified of This New {topic} Discovery",
            "What Happened When {topic} Was Finally Captured",
            "The Real Story Behind {topic}",
            "{topic}: Everything You've Been Told Is Wrong"
        ]

        for topic in hot_topics:
            for template in templates[:2]:  # 2 templates per hot topic
                title = template.format(topic=topic.title())
                topics.append(title)
                print(f"   • {title}")

        return topics

    def save_report(self, data):
        """Save trend report to file"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"trend_report_{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n💾 Full report saved: {report_file}")

    def run_full_scan(self):
        """Run complete trend monitoring scan"""

        print("\n🌐 SPACE TRENDS MONITOR - LIVE SCAN")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Gather data
        reddit_trends = self.check_reddit_trends()
        nasa_news = self.check_nasa_news()
        google_news = self.check_google_news("space astronomy discovery")

        # Analyze
        trending_keywords = self.analyze_trends(reddit_trends, nasa_news, google_news)

        # Generate topics
        timely_topics = self.generate_timely_topics(trending_keywords)

        # Save report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'reddit_trends': reddit_trends,
            'nasa_news': nasa_news,
            'google_news': google_news,
            'trending_keywords': [{'keyword': k, 'count': c} for k, c in trending_keywords],
            'suggested_topics': timely_topics
        }

        self.save_report(report_data)

        print("\n✅ TREND SCAN COMPLETE!")
        print("=" * 60)
        print("\n💡 NEXT STEPS:")
        print("1. Review suggested topics above")
        print("2. Cross-reference with WATOP title patterns")
        print("3. Create video on hottest trending topic")
        print("4. Post within 24-48 hours to catch the trend wave\n")

        return report_data


def main():
    """CLI interface"""
    monitor = TrendMonitor()
    monitor.run_full_scan()


if __name__ == "__main__":
    main()
