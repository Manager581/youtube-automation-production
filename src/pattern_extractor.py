"""
Pattern Extractor: Identifies winning formulas by comparing top vs bottom performers

Analyzes visual, pacing, and sourcing patterns to find what differentiates
high-performing videos from low-performing ones.
"""

import json
from pathlib import Path
from typing import List, Dict
import statistics


class PatternExtractor:
    """Extracts patterns from video analysis data"""

    def __init__(self, analysis_file: str):
        self.analysis_file = Path(analysis_file)
        self.data = self._load_analysis()

    def _load_analysis(self) -> Dict:
        """Load analysis JSON file"""
        with open(self.analysis_file, 'r') as f:
            return json.load(f)

    def extract_patterns(self) -> Dict:
        """
        Extract key patterns comparing high vs low performers

        Returns dict with:
        - top_video_patterns: Patterns from top videos
        - correlations: What correlates with higher views
        - recommendations: Actionable insights
        """

        videos = self.data['videos']

        # Sort by views
        sorted_videos = sorted(videos, key=lambda x: x['views'], reverse=True)

        print(f"\n📊 PATTERN EXTRACTION - {len(videos)} Videos Analyzed")
        print("=" * 80)

        # Analyze by performance rank
        patterns = {
            'performance_ranking': self._rank_by_views(sorted_videos),
            'visual_patterns': self._extract_visual_patterns(sorted_videos),
            'pacing_patterns': self._extract_pacing_patterns(sorted_videos),
            'sourcing_patterns': self._extract_sourcing_patterns(sorted_videos),
            'intro_patterns': self._extract_intro_patterns(sorted_videos),
            'correlations': self._find_correlations(sorted_videos),
            'recommendations': self._generate_recommendations(sorted_videos)
        }

        return patterns

    def _rank_by_views(self, videos: List[Dict]) -> Dict:
        """Rank videos by performance"""

        print("\n🏆 PERFORMANCE RANKING:")

        ranking = []
        for i, video in enumerate(videos, 1):
            views = video['views']
            print(f"   {i}. {views:,} views - {video['title']}")
            ranking.append({
                'rank': i,
                'views': views,
                'title': video['title'],
                'id': video['id']
            })

        return {
            'rankings': ranking,
            'highest_views': videos[0]['views'],
            'lowest_views': videos[-1]['views'],
            'avg_views': statistics.mean([v['views'] for v in videos]),
            'view_spread': videos[0]['views'] - videos[-1]['views']
        }

    def _extract_visual_patterns(self, videos: List[Dict]) -> Dict:
        """Extract visual composition patterns"""

        print("\n🎬 VISUAL COMPOSITION PATTERNS:")

        # Top performer
        top = videos[0]

        # Averages
        aerial_avg = statistics.mean([v['visual_breakdown']['aerial_footage_percent'] for v in videos])
        doc_avg = statistics.mean([v['visual_breakdown']['documentary_footage_percent'] for v in videos])
        cgi_avg = statistics.mean([v['visual_breakdown']['cgi_animations_percent'] for v in videos])
        graphics_avg = statistics.mean([v['visual_breakdown']['graphics_percent'] for v in videos])
        macro_avg = statistics.mean([v['visual_breakdown']['macro_closeup_percent'] for v in videos])

        print(f"   📊 Average Composition:")
        print(f"      - Aerial footage: {aerial_avg:.1f}%")
        print(f"      - Documentary: {doc_avg:.1f}%")
        print(f"      - CGI animations: {cgi_avg:.1f}%")
        print(f"      - Graphics: {graphics_avg:.1f}%")
        print(f"      - Macro close-ups: {macro_avg:.1f}%")

        print(f"\n   🏆 Top Performer (Video {top['id']} - {top['views']:,} views):")
        print(f"      - Aerial footage: {top['visual_breakdown']['aerial_footage_percent']}%")
        print(f"      - Documentary: {top['visual_breakdown']['documentary_footage_percent']}%")
        print(f"      - CGI animations: {top['visual_breakdown']['cgi_animations_percent']}%")
        print(f"      - Graphics: {top['visual_breakdown']['graphics_percent']}%")

        return {
            'average_composition': {
                'aerial': aerial_avg,
                'documentary': doc_avg,
                'cgi': cgi_avg,
                'graphics': graphics_avg,
                'macro': macro_avg
            },
            'top_performer_composition': top['visual_breakdown'],
            'variance': {
                'aerial': max([v['visual_breakdown']['aerial_footage_percent'] for v in videos]) -
                          min([v['visual_breakdown']['aerial_footage_percent'] for v in videos]),
                'cgi': max([v['visual_breakdown']['cgi_animations_percent'] for v in videos]) -
                       min([v['visual_breakdown']['cgi_animations_percent'] for v in videos])
            }
        }

    def _extract_pacing_patterns(self, videos: List[Dict]) -> Dict:
        """Extract pacing/cut frequency patterns"""

        print("\n⚡ PACING PATTERNS:")

        # Check if all videos have same pacing
        avg_cuts = [v['cut_frequency']['average_seconds_per_shot'] for v in videos]
        intro_cuts = [v['cut_frequency']['intro_seconds_per_shot'] for v in videos]
        explain_cuts = [v['cut_frequency']['explanation_seconds_per_shot'] for v in videos]
        reveal_cuts = [v['cut_frequency']['reveal_seconds_per_shot'] for v in videos]

        print(f"   📊 Pacing Consistency:")
        print(f"      - Average cut: {statistics.mean(avg_cuts):.1f} seconds (σ={statistics.stdev(avg_cuts) if len(avg_cuts) > 1 else 0:.2f})")
        print(f"      - Intro cut: {statistics.mean(intro_cuts):.1f} seconds")
        print(f"      - Explanation cut: {statistics.mean(explain_cuts):.1f} seconds")
        print(f"      - Reveal cut: {statistics.mean(reveal_cuts):.1f} seconds")

        # Check if pacing is consistent
        pacing_consistent = all(c == avg_cuts[0] for c in avg_cuts)

        print(f"\n   ✅ Pacing is {'CONSISTENT' if pacing_consistent else 'VARIABLE'} across all videos")

        return {
            'average_pacing': statistics.mean(avg_cuts),
            'intro_pacing': statistics.mean(intro_cuts),
            'explanation_pacing': statistics.mean(explain_cuts),
            'reveal_pacing': statistics.mean(reveal_cuts),
            'pacing_consistent': pacing_consistent,
            'pacing_variance': statistics.stdev(avg_cuts) if len(avg_cuts) > 1 else 0
        }

    def _extract_sourcing_patterns(self, videos: List[Dict]) -> Dict:
        """Extract sourcing strategy patterns"""

        print("\n🔍 SOURCING PATTERNS:")

        # Check if all use same sources
        all_use_aerial_no_watermark = all(v['sources']['aerial_no_watermark'] for v in videos)
        all_use_custom_cgi = all(v['sources']['custom_cgi'] for v in videos)
        all_use_custom_graphics = all(v['sources']['custom_graphics'] for v in videos)

        print(f"   ✅ All videos use:")
        if all_use_aerial_no_watermark:
            print(f"      - Free aerial/drone footage (no watermarks)")
        if all_use_custom_cgi:
            print(f"      - Custom CGI animations (WATOP branded)")
        if all_use_custom_graphics:
            print(f"      - Custom graphics (WATOP branded)")

        # Get unique documentary sources
        all_doc_sources = []
        for v in videos:
            all_doc_sources.extend(v['sources']['documentary_sources'])

        unique_sources = set(all_doc_sources)

        print(f"\n   📺 Documentary/News sources ({len(unique_sources)} unique):")
        for source in sorted(unique_sources):
            count = all_doc_sources.count(source)
            print(f"      - {source} ({count}/{len(videos)} videos)")

        return {
            'consistent_free_aerial': all_use_aerial_no_watermark,
            'consistent_custom_cgi': all_use_custom_cgi,
            'consistent_custom_graphics': all_use_custom_graphics,
            'unique_documentary_sources': list(unique_sources),
            'documentary_source_count': len(unique_sources),
            'topic_specific_sourcing': len(unique_sources) > len(videos) * 2  # More sources than videos
        }

    def _extract_intro_patterns(self, videos: List[Dict]) -> Dict:
        """Extract intro hook patterns"""

        print("\n🎣 INTRO HOOK PATTERNS:")

        # Group by intro hook type
        intro_types = {}
        for v in videos:
            hook = v['intro_hook']
            if hook not in intro_types:
                intro_types[hook] = []
            intro_types[hook].append(v)

        print(f"   📊 Hook Types:")
        for hook_type, vids in intro_types.items():
            avg_views = statistics.mean([v['views'] for v in vids])
            print(f"      - {hook_type}: {len(vids)} video(s), avg {avg_views:,} views")

        # Find best performing hook
        best_hook = max(intro_types.items(), key=lambda x: statistics.mean([v['views'] for v in x[1]]))

        print(f"\n   🏆 Best performing hook: {best_hook[0]} (avg {statistics.mean([v['views'] for v in best_hook[1]]):,} views)")

        return {
            'hook_types': {k: len(v) for k, v in intro_types.items()},
            'best_hook': best_hook[0],
            'best_hook_avg_views': statistics.mean([v['views'] for v in best_hook[1]]),
            'hook_diversity': len(intro_types) > 1
        }

    def _find_correlations(self, videos: List[Dict]) -> Dict:
        """Find what correlates with higher views"""

        print("\n🔗 VIEW CORRELATIONS:")

        correlations = []

        # Top performer
        top = videos[0]

        # Compare to averages
        aerial_avg = statistics.mean([v['visual_breakdown']['aerial_footage_percent'] for v in videos])
        cgi_avg = statistics.mean([v['visual_breakdown']['cgi_animations_percent'] for v in videos])
        graphics_avg = statistics.mean([v['visual_breakdown']['graphics_percent'] for v in videos])

        # Check what's different about top performer
        if top['visual_breakdown']['cgi_animations_percent'] > cgi_avg:
            diff = top['visual_breakdown']['cgi_animations_percent'] - cgi_avg
            correlations.append({
                'finding': f"More CGI animations (+{diff:.1f}%)",
                'hypothesis': "Higher CGI usage may correlate with higher views"
            })
            print(f"   📈 Top performer has {diff:.1f}% MORE CGI than average")

        if top['visual_breakdown'].get('satellite_maps_percent', 0) > 0:
            correlations.append({
                'finding': f"Uses satellite/map imagery ({top['visual_breakdown']['satellite_maps_percent']}%)",
                'hypothesis': "Satellite imagery adds geographical context and may boost views"
            })
            print(f"   📈 Top performer uses satellite/map imagery")

        if top['focus'] == 'engineering_technical':
            correlations.append({
                'finding': "Engineering/technical focus",
                'hypothesis': "Technical content may resonate more with audience"
            })
            print(f"   📈 Top performer has engineering/technical focus")

        return {
            'correlations': correlations,
            'top_performer_focus': top['focus'],
            'top_performer_hook': top['intro_hook']
        }

    def _generate_recommendations(self, videos: List[Dict]) -> Dict:
        """Generate actionable recommendations"""

        print("\n💡 RECOMMENDATIONS:")

        top = videos[0]

        recommendations = []

        # Pacing recommendation
        avg_cut = statistics.mean([v['cut_frequency']['average_seconds_per_shot'] for v in videos])
        recommendations.append({
            'category': 'Pacing',
            'recommendation': f"Maintain ~{avg_cut:.1f} second average cut frequency",
            'priority': 'CRITICAL',
            'rationale': 'Consistent across all top performers'
        })
        print(f"   ✅ CRITICAL: Maintain ~{avg_cut:.1f} sec cut frequency (consistent across all videos)")

        # Visual composition
        recommendations.append({
            'category': 'Visual Composition',
            'recommendation': f"Use {top['visual_breakdown']['aerial_footage_percent']}% aerial, {top['visual_breakdown']['cgi_animations_percent']}% CGI, {top['visual_breakdown']['documentary_footage_percent']}% documentary",
            'priority': 'HIGH',
            'rationale': f'Top performer formula (Video {top["id"]} with {top["views"]:,} views)'
        })
        print(f"   ✅ HIGH: Use top performer's visual mix (Video {top['id']})")

        # Sourcing
        recommendations.append({
            'category': 'Sourcing',
            'recommendation': 'Use free aerial stock + licensed documentary + custom CGI',
            'priority': 'HIGH',
            'rationale': 'Cost-effective pattern across all videos'
        })
        print(f"   ✅ HIGH: Free aerial + licensed documentary + custom CGI")

        # Hook strategy
        if top['intro_hook'] == 'aerial_location':
            recommendations.append({
                'category': 'Intro Hook',
                'recommendation': 'Open with aerial shot establishing location',
                'priority': 'MEDIUM',
                'rationale': f'Top performer uses {top["intro_hook"]}'
            })
            print(f"   ✅ MEDIUM: Use aerial location hook (top performer strategy)")
        elif top['intro_hook'] == 'macro_shock':
            recommendations.append({
                'category': 'Intro Hook',
                'recommendation': 'Open with macro close-up for shock value',
                'priority': 'MEDIUM',
                'rationale': f'Second-best performer uses {top["intro_hook"]}'
            })
            print(f"   ✅ MEDIUM: Consider macro shock hook (second-best strategy)")

        # Topic focus
        recommendations.append({
            'category': 'Content Focus',
            'recommendation': f'Focus on {top["focus"].replace("_", "/")} topics',
            'priority': 'MEDIUM',
            'rationale': f'Top performer focus'
        })
        print(f"   ✅ MEDIUM: Focus on {top['focus'].replace('_', '/')} topics")

        return {
            'recommendations': recommendations,
            'priority_breakdown': {
                'critical': [r for r in recommendations if r['priority'] == 'CRITICAL'],
                'high': [r for r in recommendations if r['priority'] == 'HIGH'],
                'medium': [r for r in recommendations if r['priority'] == 'MEDIUM']
            }
        }

    def save_patterns(self, output_file: str):
        """Save extracted patterns to JSON file"""

        patterns = self.extract_patterns()

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(patterns, f, indent=2)

        print(f"\n💾 Patterns saved to: {output_path}")

        return patterns


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("\n🔬 Pattern Extractor")
        print("\nUsage:")
        print("  python src/pattern_extractor.py <analysis_file.json> [output_file.json]")
        print("\nExample:")
        print("  python src/pattern_extractor.py analysis_videos_1_3.json patterns_output.json")
        return

    analysis_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "patterns_extracted.json"

    extractor = PatternExtractor(analysis_file)
    extractor.save_patterns(output_file)


if __name__ == "__main__":
    main()
