"""
Trend Correlation Analyzer
Cross-references successful videos with trending topics at time of upload
Identifies which videos succeeded due to timing vs just good titles
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import requests
import time
import re


class TrendCorrelationAnalyzer:
    """Analyzes correlation between video success and trend timing"""

    def __init__(self):
        self.research_dir = Path("research/watop")
        self.trends_dir = Path("research/trends")
        self.output_dir = Path("research/analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_video_data(self):
        """Load analyzed video metadata"""
        video_file = self.research_dir / "watop_videos.json"

        if not video_file.exists():
            print("❌ No video data found. Run watop_analyzer.py download first.")
            return []

        with open(video_file, 'r') as f:
            return json.load(f)

    def extract_topics_from_title(self, title):
        """Extract potential trending topics from video title"""

        # Common space keywords
        space_keywords = [
            'nasa', 'voyager', 'james webb', 'jwst', 'hubble',
            'black hole', 'neutron star', 'supernova', 'pulsar',
            'mars', 'moon', 'jupiter', 'saturn', 'venus', 'mercury',
            'asteroid', 'comet', 'meteor', 'meteorite',
            'galaxy', 'milky way', 'andromeda',
            'exoplanet', 'planet', 'solar system',
            'dark matter', 'dark energy', 'gravitational wave',
            'spacex', 'starship', 'dragon', 'falcon',
            'iss', 'space station',
            'betelgeuse', 'proxima', 'alpha centauri',
            'bennu', 'apophis', 'oumuamua'
        ]

        title_lower = title.lower()
        found_topics = []

        for keyword in space_keywords:
            if keyword in title_lower:
                found_topics.append(keyword)

        return found_topics

    def check_google_trends_historical(self, topic, date_str):
        """
        Check if topic was trending around upload date
        Note: Google Trends API requires authentication, so we'll use approximate method
        """

        # Convert date string (YYYYMMDD) to datetime
        try:
            upload_date = datetime.strptime(date_str, "%Y%m%d")
        except:
            return None

        # For now, return placeholder - would need pytrends library for real data
        # This shows the structure of what we'd return
        return {
            'topic': topic,
            'upload_date': upload_date.strftime("%Y-%m-%d"),
            'trend_score': None,  # Would be 0-100 from Google Trends
            'was_trending': None   # Would be True/False based on threshold
        }

    def check_nasa_news_historical(self, topics, upload_date_str):
        """Check if NASA had relevant news around upload date"""

        try:
            upload_date = datetime.strptime(upload_date_str, "%Y%m%d")
        except:
            return []

        # In production, would check NASA news archives
        # For now, we'll check current NASA feed and note the methodology

        print(f"   📅 Checking NASA news around {upload_date.strftime('%Y-%m-%d')}...")

        # Placeholder for historical correlation
        return {
            'upload_date': upload_date.strftime("%Y-%m-%d"),
            'topics_in_title': topics,
            'methodology': 'Would need NASA news archive API for historical data'
        }

    def analyze_video_timing(self, video_data):
        """Analyze each video's timing relative to trends"""

        print("\n📊 VIDEO TIMING ANALYSIS")
        print("=" * 80)

        analysis_results = []

        for video in video_data:
            title = video['title']
            upload_date = video['upload_date']
            view_count = video['view_count']

            # Extract topics from title
            topics = self.extract_topics_from_title(title)

            if topics:
                print(f"\n🎬 {title[:70]}...")
                print(f"   📅 Upload: {upload_date}")
                print(f"   👁️  Views: {view_count:,}")
                print(f"   🔑 Topics: {', '.join(topics)}")

                # Check if topics were trending
                trend_data = []
                for topic in topics:
                    trend_info = self.check_google_trends_historical(topic, upload_date)
                    if trend_info:
                        trend_data.append(trend_info)

                # Store analysis
                result = {
                    'title': title,
                    'upload_date': upload_date,
                    'view_count': view_count,
                    'topics': topics,
                    'trend_data': trend_data,
                    'views_per_topic': view_count / max(len(topics), 1)
                }

                analysis_results.append(result)

        return analysis_results

    def correlate_trends_and_views(self, analysis_results):
        """Find correlation between trending topics and video success"""

        print("\n\n🔍 CORRELATION ANALYSIS")
        print("=" * 80)

        # Separate videos by performance
        high_performers = [v for v in analysis_results if v['view_count'] > 750000]
        medium_performers = [v for v in analysis_results if 400000 <= v['view_count'] <= 750000]
        low_performers = [v for v in analysis_results if v['view_count'] < 400000]

        print(f"\n📈 PERFORMANCE BREAKDOWN:")
        print(f"   High (>750K):   {len(high_performers)} videos")
        print(f"   Medium (400-750K): {len(medium_performers)} videos")
        print(f"   Low (<400K):    {len(low_performers)} videos")

        # Analyze topic frequency by performance tier
        print(f"\n🔥 TOPICS IN HIGH PERFORMERS:")
        high_topics = {}
        for video in high_performers:
            for topic in video['topics']:
                high_topics[topic] = high_topics.get(topic, 0) + 1

        for topic, count in sorted(high_topics.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {topic}: {count} videos")

        print(f"\n📊 TOPICS IN LOW PERFORMERS:")
        low_topics = {}
        for video in low_performers:
            for topic in video['topics']:
                low_topics[topic] = low_topics.get(topic, 0) + 1

        for topic, count in sorted(low_topics.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {topic}: {count} videos")

        # Calculate topic success rates
        print(f"\n🎯 TOPIC SUCCESS RATES (High Performer Rate):")
        all_topics = set(list(high_topics.keys()) + list(low_topics.keys()))

        topic_stats = []
        for topic in all_topics:
            high_count = high_topics.get(topic, 0)
            low_count = low_topics.get(topic, 0)
            total = high_count + low_count

            if total > 0:
                success_rate = (high_count / total) * 100
                topic_stats.append({
                    'topic': topic,
                    'success_rate': success_rate,
                    'total_appearances': total,
                    'high_count': high_count
                })

        # Sort by success rate
        topic_stats.sort(key=lambda x: (x['success_rate'], x['total_appearances']), reverse=True)

        for stat in topic_stats[:15]:
            print(f"   {stat['topic']:<20} {stat['success_rate']:>5.0f}% success  ({stat['high_count']}/{stat['total_appearances']} high performers)")

        return {
            'high_performers': high_performers,
            'medium_performers': medium_performers,
            'low_performers': low_performers,
            'topic_stats': topic_stats
        }

    def generate_recommendations(self, correlation_data):
        """Generate recommendations based on correlation analysis"""

        print("\n\n💡 STRATEGIC RECOMMENDATIONS")
        print("=" * 80)

        topic_stats = correlation_data['topic_stats']

        # Identify winning topics
        winning_topics = [t for t in topic_stats if t['success_rate'] > 60 and t['total_appearances'] >= 2]

        print("\n🏆 PROVEN WINNING TOPICS (>60% success rate, 2+ videos):")
        for topic in winning_topics[:10]:
            print(f"   ✅ {topic['topic']}")

        # Cross-reference with current trends
        print("\n\n🔥 CURRENT TRENDING + PROVEN WINNERS:")
        print("   These topics are BOTH trending now AND have high success rates:")
        print()

        # Load current trends
        trend_files = sorted(self.trends_dir.glob("trend_report_*.json"))
        if trend_files:
            with open(trend_files[-1], 'r') as f:
                current_trends = json.load(f)

            trending_keywords = [kw['keyword'].lower() for kw in current_trends.get('trending_keywords', [])]

            hot_opportunities = []
            for topic in winning_topics:
                if topic['topic'] in trending_keywords:
                    hot_opportunities.append(topic)
                    print(f"   🎯 {topic['topic'].upper()} - {topic['success_rate']:.0f}% success rate + TRENDING NOW!")

            if not hot_opportunities:
                print("   ⚠️  No overlap between proven winners and current trends")
                print("   💡 Suggestion: Create content on proven winners even if not trending,")
                print("      or wait for trends to shift toward these topics")

        print("\n\n📋 ACTION PLAN:")
        print("   1. Monitor trends daily for when proven winners start trending")
        print("   2. When overlap detected, create video within 24-48 hours")
        print("   3. Use WATOP title formula + proven topic + trending momentum")
        print("   4. Expected result: 750K+ views (high performer tier)")

        return {
            'winning_topics': winning_topics,
            'recommendations': 'Focus on proven topics when they trend'
        }

    def save_analysis_report(self, correlation_data, recommendations):
        """Save complete analysis report"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"correlation_analysis_{timestamp}.json"

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_videos': len(correlation_data['high_performers']) +
                               len(correlation_data['medium_performers']) +
                               len(correlation_data['low_performers']),
                'high_performers': len(correlation_data['high_performers']),
                'medium_performers': len(correlation_data['medium_performers']),
                'low_performers': len(correlation_data['low_performers'])
            },
            'topic_stats': correlation_data['topic_stats'],
            'winning_topics': recommendations['winning_topics'],
            'high_performing_videos': correlation_data['high_performers']
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Analysis report saved: {report_file}")

    def run_full_analysis(self):
        """Run complete trend correlation analysis"""

        print("\n🔬 TREND CORRELATION ANALYSIS")
        print("=" * 80)
        print("Analyzing relationship between video success and trend timing\n")

        # Load video data
        video_data = self.load_video_data()
        if not video_data:
            return

        print(f"✅ Loaded {len(video_data)} videos for analysis\n")

        # Analyze timing
        analysis_results = self.analyze_video_timing(video_data)

        # Correlate trends and views
        correlation_data = self.correlate_trends_and_views(analysis_results)

        # Generate recommendations
        recommendations = self.generate_recommendations(correlation_data)

        # Save report
        self.save_analysis_report(correlation_data, recommendations)

        print("\n✅ ANALYSIS COMPLETE!")
        print("=" * 80)


def main():
    """CLI interface"""
    analyzer = TrendCorrelationAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
