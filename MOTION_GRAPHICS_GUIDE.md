# 🎨 MOTION GRAPHICS AUTO-GENERATION GUIDE

Complete system for automatically generating WATOP-style motion graphics from script data.

---

## 📋 WHAT THIS DOES

Analyzes your video script and **automatically generates motion graphics**:
- ✅ Animated statistics/numbers
- ✅ Location markers on maps
- ✅ Text overlays for key facts
- ✅ Data visualizations (charts, comparisons)
- ✅ Process flows and diagrams

---

## 🚀 QUICK START

### **Step 1: Analyze Script for Graphics Opportunities**

```bash
python src/phase3b_motion_graphics_generator.py VIDEO_ID watop
```

**Output**:
```
🎨 Analyzing script for graphics opportunities...
   ✅ Found 8 graphics opportunities

📋 GRAPHICS TO GENERATE:
   1. STATISTIC at 15.3s
      Data: {'number': 1500000, 'label': 'Rabbits', 'unit': '+'}
      Context: China released 1.5 million rabbits into the Kabuchi Desert...

   2. LOCATION at 42.1s
      Data: {'lat': 35.8617, 'lng': 104.1954, 'label': 'China'}
      Context: in China is located in Inner Mongolia...
```

### **Step 2: Generate the Graphics**

The script automatically generates video files for each graphic:

```
analysis/watop/graphics/VIDEO_ID/
├── statistic_1_15.mp4    (Number counting animation)
├── location_2_42.mp4      (Map with pin drop)
├── text_overlay_3_78.mp4  (Animated text)
└── ...
```

---

## 🛠️ INSTALLATION

### **Required Tools**

#### **Option A: Manim (Python-based) - RECOMMENDED**
```bash
pip install manim
pip install manim-slides  # Optional, for presentations
```

**Pros**: Pure Python, easy to customize, great for educational content
**Cons**: Slower rendering than Remotion

#### **Option B: Remotion (React-based) - MOST PROFESSIONAL**
```bash
npm install -g remotion
cd motion-graphics/remotion-templates
npm install
```

**Pros**: Fastest rendering, most professional output
**Cons**: Requires Node.js, more complex setup

#### **Option C: FFmpeg (Simple text/basic graphics)**
```bash
# Already installed in most systems
ffmpeg -version
```

**Pros**: Simple, no dependencies
**Cons**: Limited to basic text overlays

---

## 📦 AVAILABLE TEMPLATES

### **Manim Templates** (Python)

Located in: `motion-graphics/manim-templates/watop_templates.py`

#### **1. CountingNumber**
Animated number counting up with label

```bash
manim motion-graphics/manim-templates/watop_templates.py CountingNumber -ql
```

**Customize**:
```python
target_number = 1500000  # Number to count to
label_text = "People Affected"  # Label below number
color_scheme = BLUE  # Color
```

#### **2. LocationZoom**
Map zoom with location marker

```bash
manim motion-graphics/manim-templates/watop_templates.py LocationZoom -ql
```

**Customize**:
```python
location_name = "Egypt"
coordinates = (26.8206, 30.8025)
marker_color = RED
```

#### **3. DataVisualization**
Animated bar chart

```bash
manim motion-graphics/manim-templates/watop_templates.py DataVisualization -qm
```

**Customize**:
```python
data = {
    "2015": 100,
    "2018": 250,
    "2021": 450
}
title_text = "Growth Over Time"
```

#### **4. ProcessFlow**
Step-by-step process diagram

```bash
manim motion-graphics/manim-templates/watop_templates.py ProcessFlow -ql
```

#### **5. ComparisonBars**
Side-by-side value comparison

```bash
manim motion-graphics/manim-templates/watop_templates.py ComparisonBars -ql
```

---

### **Remotion Templates** (React)

Located in: `motion-graphics/remotion-templates/`

#### **1. StatisticDisplay.tsx**
Professional counting animation

**Usage**:
```tsx
<StatisticDisplay
  number={1500000}
  label="Views"
  unit="+"
  duration={60}
/>
```

#### **2. LocationMarker.tsx**
Map with animated pin (integrates with Mapbox)

**Usage**:
```tsx
<LocationMarker
  lat={40.7128}
  lng={-74.0060}
  label="New York"
  duration={90}
/>
```

---

## 🎬 RENDERING COMMANDS

### **Manim Quality Levels**

```bash
# Low quality (fast preview)
manim watop_templates.py CountingNumber -ql

# Medium quality (good for testing)
manim watop_templates.py CountingNumber -qm

# High quality (final render)
manim watop_templates.py CountingNumber -qh

# 4K quality (production)
manim watop_templates.py CountingNumber -qk
```

### **Remotion Rendering**

```bash
cd motion-graphics/remotion-templates

# Render single composition
npx remotion render StatisticDisplay output.mp4

# Set duration (frames at 30fps)
npx remotion render StatisticDisplay output.mp4 --frames=90

# High quality
npx remotion render StatisticDisplay output.mp4 --codec=h264 --quality=100
```

---

## 🔧 CUSTOMIZATION

### **Editing Manim Templates**

1. Open `motion-graphics/manim-templates/watop_templates.py`
2. Find the class you want to customize
3. Edit configuration section at top of `construct()`:

```python
class CountingNumber(Scene):
    def construct(self):
        # ===== EDIT THESE =====
        target_number = 1500000
        label_text = "People Affected"
        color_scheme = BLUE
        # ======================
```

4. Render:
```bash
manim watop_templates.py CountingNumber -ql
```

### **Creating New Templates**

Copy an existing template and modify:

```python
class MyCustomAnimation(Scene):
    def construct(self):
        # Your custom animation code here
        text = Text("Hello!", font_size=72)
        self.play(Write(text))
        self.wait(2)
```

---

## 🎯 AUTO-GENERATION WORKFLOW

### **Complete Automation Example**

```bash
# 1. Analyze script
python src/phase3b_motion_graphics_generator.py 6lfV-K7PtII watop

# Output: List of graphics to generate with timestamps

# 2. Graphics are auto-generated in:
# analysis/watop/graphics/6lfV-K7PtII/

# 3. Use in video editor:
# - Import generated .mp4 files
# - Place at timestamps indicated
# - Overlay on top of B-roll footage
```

---

## 📊 INTEGRATION WITH FORMULA EXTRACTOR

The graphics analyzer can run as part of the complete analysis:

```python
from phase3a_graphics_analyzer import GraphicsPatternAnalyzer

analyzer = GraphicsPatternAnalyzer()
patterns = analyzer.analyze_graphics('watop', video_analyses)

print(f"Template opportunities: {patterns['template_opportunities']}")
```

**Output**:
```
Template opportunities:
- statistic_display: 12 occurrences
- location_marker: 5 occurrences
- data_chart: 3 occurrences
```

---

## 🎨 ADVANCED: BLENDER INTEGRATION

For complex 3D renders (water flows, geological structures):

```python
import bpy

# Load WATOP 3D template
bpy.ops.wm.open_mainfile(filepath="templates/water_flow.blend")

# Customize parameters
bpy.data.objects["WaterFlow"].scale = (2, 2, 2)

# Render
bpy.ops.render.render(write_still=True)
```

---

## 💡 TIPS FOR BEST RESULTS

### **1. Numbers/Statistics**
- Use for impressive numbers (> 10,000)
- Format: "1.5M" not "1,500,000"
- Duration: 2-4 seconds

### **2. Locations**
- Always show context (zoom out then in)
- Add coordinates for credibility
- Duration: 3-5 seconds

### **3. Text Overlays**
- Keep text under 100 characters
- Use for shocking facts or quotes
- Duration: 3-4 seconds (reading time)

### **4. Charts**
- Animate bars growing from bottom
- Show one data point at a time
- Duration: 5-8 seconds

---

## 🐛 TROUBLESHOOTING

### **"manim: command not found"**
```bash
pip install manim
# or
pip install manim-ce  # Community edition
```

### **"ModuleNotFoundError: No module named 'remotion'"**
Remotion uses Node.js, not Python:
```bash
npm install -g remotion
```

### **Slow rendering**
- Use `-ql` for preview quality
- Upgrade to `-qm` only for testing
- Use `-qh` or `-qk` only for final render

### **Graphics don't match WATOP style**
- Adjust colors in templates
- Change animation speeds (run_time parameter)
- Modify font sizes

---

## 📚 RESOURCES

- **Manim Docs**: https://docs.manim.community/
- **Remotion Docs**: https://www.remotion.dev/docs
- **WATOP Channel**: https://www.youtube.com/@WATOP (study their graphics)
- **3Blue1Brown**: https://www.3blue1brown.com/ (Manim creator)

---

## 🚀 NEXT STEPS

1. ✅ Run `phase3b_motion_graphics_generator.py` on your videos
2. ✅ Review generated graphics opportunities
3. ✅ Customize templates to match your style
4. ✅ Integrate with your video editing workflow
5. ✅ Iterate and improve based on results

---

**Happy animating! 🎬**
