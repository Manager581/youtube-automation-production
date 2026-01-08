"""
WATOP-Style Manim Templates
Python-based motion graphics for educational content

Templates:
1. CountingNumber - Animated number counting up
2. LocationZoom - Map zoom to location
3. DataVisualization - Animated charts
4. ProcessFlow - Show processes/flows
5. ComparisonBars - Compare two values

Usage:
    manim watop_templates.py CountingNumber -ql
"""

from manim import *


class CountingNumber(Scene):
    """
    Animated number counting up with label

    Customize by editing:
    - target_number: The final number to count to
    - label_text: Label below the number
    - color_scheme: Color of text
    """

    def construct(self):
        # Configuration (edit these)
        target_number = 1500000
        label_text = "People Affected"
        color_scheme = BLUE

        # Format large numbers
        if target_number >= 1000000:
            display_num = target_number / 1000000
            suffix = "M"
        elif target_number >= 1000:
            display_num = target_number / 1000
            suffix = "K"
        else:
            display_num = target_number
            suffix = ""

        # Create number
        number = DecimalNumber(
            0,
            num_decimal_places=1 if display_num < 100 else 0,
            color=color_scheme,
            font_size=120
        )

        # Add suffix
        suffix_text = Text(suffix, font_size=80, color=color_scheme)
        suffix_text.next_to(number, RIGHT, buff=0.2)

        # Create label
        label = Text(label_text, font_size=48, color=GRAY)
        label.next_to(number, DOWN, buff=0.8)

        # Group elements
        group = VGroup(number, suffix_text, label)
        group.move_to(ORIGIN)

        # Animate counting
        self.play(
            number.animate.set_value(display_num),
            run_time=2,
            rate_func=smooth
        )

        # Fade in label
        self.play(FadeIn(label), run_time=0.5)

        # Hold
        self.wait(2)


class LocationZoom(Scene):
    """
    Zoom into location on map with marker

    Customize:
    - location_name: Name of location
    - coordinates: (lat, lng) for reference
    - marker_color: Color of location pin
    """

    def construct(self):
        # Configuration
        location_name = "Egypt"
        coordinates = (26.8206, 30.8025)
        marker_color = RED

        # Create "map" background (simplified)
        map_bg = Rectangle(
            width=12,
            height=7,
            fill_color=BLUE_E,
            fill_opacity=0.3,
            stroke_color=WHITE
        )

        # Create location marker
        marker = Dot(color=marker_color, radius=0.3)
        marker.move_to(ORIGIN)

        # Create label
        label = Text(location_name, font_size=42, color=WHITE)
        label.next_to(marker, DOWN, buff=0.5)

        # Create coordinates text
        coord_text = Text(
            f"{coordinates[0]:.2f}°N, {coordinates[1]:.2f}°E",
            font_size=24,
            color=GRAY
        )
        coord_text.next_to(label, DOWN, buff=0.3)

        # Animate zoom
        self.play(FadeIn(map_bg), run_time=0.5)
        self.play(
            map_bg.animate.scale(2),
            run_time=1.5,
            rate_func=smooth
        )

        # Drop marker
        marker.shift(UP * 3)
        self.play(
            marker.animate.shift(DOWN * 3),
            run_time=0.8,
            rate_func=rate_functions.ease_out_bounce
        )

        # Show label
        self.play(
            FadeIn(label),
            FadeIn(coord_text),
            run_time=0.5
        )

        # Pulse marker
        self.play(
            marker.animate.scale(1.5),
            run_time=0.3
        )
        self.play(
            marker.animate.scale(1/1.5),
            run_time=0.3
        )

        self.wait(2)


class DataVisualization(Scene):
    """
    Animated bar chart showing data comparison

    Customize:
    - data: Dictionary of labels and values
    - title: Chart title
    - color_scheme: Color for bars
    """

    def construct(self):
        # Configuration
        data = {
            "2015": 100,
            "2018": 250,
            "2021": 450,
            "2024": 800
        }
        title_text = "Growth Over Time"
        color_scheme = GREEN

        # Create title
        title = Text(title_text, font_size=48, color=WHITE)
        title.to_edge(UP, buff=0.5)

        # Create bars
        max_value = max(data.values())
        bar_width = 0.8
        bar_gap = 0.3
        total_width = len(data) * (bar_width + bar_gap)

        bars = VGroup()
        labels = VGroup()
        values = VGroup()

        for i, (label, value) in enumerate(data.items()):
            # Calculate position
            x = -total_width/2 + i * (bar_width + bar_gap) + bar_width/2

            # Create bar
            bar_height = (value / max_value) * 4
            bar = Rectangle(
                width=bar_width,
                height=bar_height,
                fill_color=color_scheme,
                fill_opacity=0.8,
                stroke_color=WHITE
            )
            bar.move_to([x, bar_height/2 - 2, 0])

            # Create label
            label_text = Text(label, font_size=28, color=WHITE)
            label_text.move_to([x, -2.5, 0])

            # Create value
            value_text = Text(str(value), font_size=32, color=color_scheme)
            value_text.next_to(bar, UP, buff=0.2)

            bars.add(bar)
            labels.add(label_text)
            values.add(value_text)

        # Animate
        self.play(Write(title), run_time=0.5)
        self.play(FadeIn(labels), run_time=0.5)

        # Grow bars one by one
        for bar, value in zip(bars, values):
            self.play(
                GrowFromEdge(bar, DOWN),
                run_time=0.6
            )
            self.play(FadeIn(value), run_time=0.2)

        self.wait(2)


class ProcessFlow(Scene):
    """
    Show a process or flow diagram

    Customize:
    - steps: List of process steps
    - title: Process title
    """

    def construct(self):
        # Configuration
        steps = [
            "Release Rabbits",
            "Rabbits Eat Vegetation",
            "Produce Fertilizer",
            "Plants Grow"
        ]
        title_text = "Ecosystem Process"

        # Create title
        title = Text(title_text, font_size=48, color=WHITE)
        title.to_edge(UP, buff=0.5)

        # Create step boxes
        boxes = VGroup()
        arrows = VGroup()

        for i, step in enumerate(steps):
            # Create box
            box = Rectangle(
                width=3,
                height=1.2,
                fill_color=BLUE_D,
                fill_opacity=0.5,
                stroke_color=BLUE
            )

            # Create text
            text = Text(step, font_size=24, color=WHITE)
            text.move_to(box.get_center())

            # Position
            y_pos = 1.5 - i * 1.8
            box.move_to([0, y_pos, 0])
            text.move_to([0, y_pos, 0])

            boxes.add(VGroup(box, text))

            # Create arrow to next step
            if i < len(steps) - 1:
                arrow = Arrow(
                    start=[0, y_pos - 0.6, 0],
                    end=[0, y_pos - 1.2, 0],
                    color=YELLOW,
                    buff=0
                )
                arrows.add(arrow)

        # Animate
        self.play(Write(title), run_time=0.5)

        # Show steps one by one
        for i, (box_group, arrow) in enumerate(zip(boxes, list(arrows) + [None])):
            self.play(FadeIn(box_group), run_time=0.5)
            if arrow is not None:
                self.play(GrowArrow(arrow), run_time=0.3)

        self.wait(2)


class ComparisonBars(Scene):
    """
    Side-by-side comparison of two values

    Customize:
    - value1, value2: Values to compare
    - label1, label2: Labels for each value
    - title: Comparison title
    """

    def construct(self):
        # Configuration
        value1 = 150
        value2 = 800
        label1 = "Before"
        label2 = "After"
        title_text = "Impact Comparison"

        # Create title
        title = Text(title_text, font_size=48, color=WHITE)
        title.to_edge(UP, buff=0.5)

        # Calculate heights
        max_val = max(value1, value2)
        height1 = (value1 / max_val) * 4
        height2 = (value2 / max_val) * 4

        # Create bars
        bar1 = Rectangle(
            width=2,
            height=height1,
            fill_color=RED,
            fill_opacity=0.7,
            stroke_color=WHITE
        )
        bar1.move_to([-2, height1/2 - 2, 0])

        bar2 = Rectangle(
            width=2,
            height=height2,
            fill_color=GREEN,
            fill_opacity=0.7,
            stroke_color=WHITE
        )
        bar2.move_to([2, height2/2 - 2, 0])

        # Create labels
        label1_text = Text(label1, font_size=36, color=RED)
        label1_text.move_to([-2, -2.8, 0])

        label2_text = Text(label2, font_size=36, color=GREEN)
        label2_text.move_to([2, -2.8, 0])

        # Create values
        value1_text = Text(str(value1), font_size=42, color=RED)
        value1_text.next_to(bar1, UP, buff=0.2)

        value2_text = Text(str(value2), font_size=42, color=GREEN)
        value2_text.next_to(bar2, UP, buff=0.2)

        # Animate
        self.play(Write(title), run_time=0.5)
        self.play(
            FadeIn(label1_text),
            FadeIn(label2_text),
            run_time=0.5
        )

        # Grow bars
        self.play(
            GrowFromEdge(bar1, DOWN),
            GrowFromEdge(bar2, DOWN),
            run_time=1.5
        )

        # Show values
        self.play(
            FadeIn(value1_text),
            FadeIn(value2_text),
            run_time=0.5
        )

        # Highlight difference
        if value2 > value1:
            self.play(
                bar2.animate.set_fill(GREEN, opacity=1),
                run_time=0.5
            )

        self.wait(2)


# Example usage in CLI:
# manim watop_templates.py CountingNumber -ql -o counting_output.mp4
# manim watop_templates.py LocationZoom -qm -o location_output.mp4
# manim watop_templates.py DataVisualization -qh -o chart_output.mp4
