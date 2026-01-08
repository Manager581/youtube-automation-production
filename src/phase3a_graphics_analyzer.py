"""
Phase 3A: Graphics Pattern Analyzer
Identifies what types of motion graphics and CGI are used

Analyzes:
- What graphic types appear (maps, charts, statistics, 3D renders)
- When they appear (during explanations, reveals, intros)
- What data they show (numbers, locations, processes)
- Animation style (fade in, zoom, rotate, particle effects)

This feeds into auto-generation templates.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter


class GraphicsPatternAnalyzer:
    """Analyzes motion graphics usage patterns"""

    def __init__(self, analysis_dir: str = "analysis"):
        self.analysis_dir = Path(analysis_dir)

        # Graphic type categories
        self.graphic_keywords = {
            'map': ['map', 'location', 'geographic', 'satellite', 'terrain', 'region'],
            'chart': ['chart', 'graph', 'data', 'statistics', 'percentage', 'bar', 'pie'],
            'text_overlay': ['text', 'title', 'subtitle', 'caption', 'label'],
            'diagram': ['diagram', 'schematic', 'blueprint', 'cross-section', 'cutaway'],
            '3d_render': ['3d', 'render', 'model', 'cgi', 'animation', 'simulation'],
            'infographic': ['infographic', 'visualization', 'data viz', 'timeline'],
            'logo_branding': ['logo', 'watermark', 'branding', 'channel'],
            'transition': ['transition', 'wipe', 'fade', 'dissolve']
        }

    def analyze_graphics(self, creator_name: str, video_analyses: List[Dict]) -> Dict:
        """
        Analyze graphics patterns across multiple videos

        Args:
            creator_name: Creator name
            video_analyses: List of video analysis dicts (from Manus or Phase 1C)

        Returns:
            Dict with graphics analysis
        """

        print(f"\n🎨 Analyzing motion graphics patterns for {creator_name}...")

        all_graphics = []

        # Extract graphics from video analyses
        for video in video_analyses:
            video_id = video.get('id') or video.get('video_id')

            # Check for visual classifications (Phase 1C output)
            visual_classifications = video.get('visual_breakdown') or video.get('visual_classifications', [])

            if isinstance(visual_classifications, dict):
                # From Manus analysis
                graphics_percent = visual_classifications.get('cgi_animations_percent', 0)
                graphics_percent += visual_classifications.get('graphics_percent', 0)

                all_graphics.append({
                    'video_id': video_id,
                    'total_graphics_percent': graphics_percent,
                    'types': self._infer_graphic_types(video)
                })
            elif isinstance(visual_classifications, list):
                # From Phase 1C
                graphics_segments = [
                    c for c in visual_classifications
                    if c.get('content_type') in ['cgi_animation', 'chart_graphic', 'text_overlay']
                ]

                for segment in graphics_segments:
                    all_graphics.append({
                        'video_id': video_id,
                        'segment_time': segment.get('segment_id'),
                        'type': segment.get('content_type'),
                        'description': segment.get('subject', ''),
                        'script_context': segment.get('script_context', '')
                    })

        # Analyze patterns
        patterns = self._extract_graphic_patterns(all_graphics)

        # Identify templateable graphics
        templates = self._identify_templateable_graphics(patterns)

        result = {
            'creator_name': creator_name,
            'total_graphics': len(all_graphics),
            'patterns': patterns,
            'template_opportunities': templates
        }

        print(f"   ✅ Found {len(all_graphics)} graphic segments")
        print(f"   🎯 Identified {len(templates)} template opportunities")

        return result

    def _infer_graphic_types(self, video: Dict) -> List[str]:
        """Infer graphic types from video description/title"""

        text = f"{video.get('title', '')} {video.get('description', '')}".lower()

        types = []
        for graphic_type, keywords in self.graphic_keywords.items():
            if any(keyword in text for keyword in keywords):
                types.append(graphic_type)

        return types

    def _extract_graphic_patterns(self, all_graphics: List[Dict]) -> Dict:
        """Extract common patterns in graphics usage"""

        # Count graphic types
        type_counts = Counter()
        for graphic in all_graphics:
            if isinstance(graphic.get('types'), list):
                type_counts.update(graphic['types'])
            elif graphic.get('type'):
                type_counts[graphic['type']] += 1

        # Find common descriptions (for templating)
        descriptions = [g.get('description', '') for g in all_graphics if g.get('description')]

        # Look for numerical data mentions
        numerical_graphics = [
            g for g in all_graphics
            if any(word in g.get('description', '').lower() for word in ['percent', 'number', 'million', 'billion', 'degrees'])
        ]

        # Look for location mentions
        location_graphics = [
            g for g in all_graphics
            if any(word in g.get('description', '').lower() for word in ['map', 'location', 'country', 'city', 'region'])
        ]

        return {
            'type_distribution': dict(type_counts),
            'most_common_type': type_counts.most_common(1)[0][0] if type_counts else 'unknown',
            'numerical_graphics_count': len(numerical_graphics),
            'location_graphics_count': len(location_graphics),
            'total_unique_types': len(type_counts)
        }

    def _identify_templateable_graphics(self, patterns: Dict) -> List[Dict]:
        """Identify graphics that can be auto-generated with templates"""

        templates = []

        type_dist = patterns.get('type_distribution', {})

        # Template 1: Statistics/Numbers
        if 'chart_graphic' in type_dist or patterns.get('numerical_graphics_count', 0) > 0:
            templates.append({
                'name': 'statistic_display',
                'type': 'number_animation',
                'use_case': 'Show statistics, percentages, large numbers',
                'input_needed': 'number, unit, label',
                'tools': ['Remotion', 'After Effects', 'Manim'],
                'estimated_frequency': type_dist.get('chart_graphic', 0)
            })

        # Template 2: Maps/Locations
        if patterns.get('location_graphics_count', 0) > 0 or 'map' in type_dist:
            templates.append({
                'name': 'location_marker',
                'type': 'map_animation',
                'use_case': 'Show locations on map, zoom to region',
                'input_needed': 'coordinates, location name',
                'tools': ['Remotion + Mapbox', 'After Effects'],
                'estimated_frequency': patterns.get('location_graphics_count', 0)
            })

        # Template 3: Text Overlays
        if 'text_overlay' in type_dist:
            templates.append({
                'name': 'text_overlay',
                'type': 'text_animation',
                'use_case': 'Display key facts, quotes, definitions',
                'input_needed': 'text content, duration',
                'tools': ['Remotion', 'After Effects'],
                'estimated_frequency': type_dist.get('text_overlay', 0)
            })

        # Template 4: 3D Visualizations
        if '3d_render' in type_dist or 'cgi_animation' in type_dist:
            templates.append({
                'name': '3d_visualization',
                'type': '3d_animation',
                'use_case': 'Visualize processes, structures, flows',
                'input_needed': 'concept description, duration',
                'tools': ['Blender', 'Manim'],
                'estimated_frequency': type_dist.get('cgi_animation', 0) + type_dist.get('3d_render', 0)
            })

        # Template 5: Data Charts
        if any(t in type_dist for t in ['chart', 'chart_graphic', 'infographic']):
            templates.append({
                'name': 'data_chart',
                'type': 'chart_animation',
                'use_case': 'Show data trends, comparisons, distributions',
                'input_needed': 'data points, chart type (bar, line, pie)',
                'tools': ['Remotion + D3.js', 'Manim'],
                'estimated_frequency': sum(type_dist.get(t, 0) for t in ['chart', 'chart_graphic', 'infographic'])
            })

        return templates


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("\n🎨 Graphics Pattern Analyzer")
        print("\nUsage:")
        print("  python src/phase3a_graphics_analyzer.py <analysis_file.json>")
        print("\nExample:")
        print("  python src/phase3a_graphics_analyzer.py analysis_videos_1_3.json")
        print("\nAnalysis file should contain video data from Manus or Phase 1C")
        return

    analysis_file = Path(sys.argv[1])

    if not analysis_file.exists():
        print(f"❌ Analysis file not found: {analysis_file}")
        return

    with open(analysis_file, 'r') as f:
        data = json.load(f)

    videos = data.get('videos', [])
    creator_name = data.get('creator_name', 'creator')

    analyzer = GraphicsPatternAnalyzer()
    result = analyzer.analyze_graphics(creator_name, videos)

    # Save results
    output_file = Path(f"graphics_patterns_{creator_name}.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

    # Print template opportunities
    print(f"\n🎯 TEMPLATE OPPORTUNITIES:")
    for template in result['template_opportunities']:
        print(f"\n   📦 {template['name'].upper()}")
        print(f"      Type: {template['type']}")
        print(f"      Use: {template['use_case']}")
        print(f"      Input: {template['input_needed']}")
        print(f"      Tools: {', '.join(template['tools'])}")
        print(f"      Frequency: {template['estimated_frequency']} occurrences")


if __name__ == "__main__":
    main()
