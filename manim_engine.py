from manim import *
import json
import os

class GeneratedLesson(Scene):
    def construct(self):
        # Load the specification
        spec_path = "lesson_spec.json"
        if not os.path.exists(spec_path):
            title = Text("Error: No spec found", color=RED)
            self.add(title)
            return

        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)

        # 1. Opening Title Sequence
        self.play_title_sequence(spec.get("title", "Untitled"), spec.get("subtitle", ""))

        # 2. Render Sections
        for section in spec.get("sections", []):
            self.render_section(section)
            self.clear_screen()

        # 3. Closing
        self.play_closing()

    def play_title_sequence(self, title_text, subtitle_text):
        title = Text(title_text, font_size=64, color=BLUE).to_edge(UP)
        subtitle = Text(subtitle_text, font_size=32, color=WHITE).next_to(title, DOWN)

        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(2)
        self.play(FadeOut(subtitle), title.animate.scale(0.8).to_corner(UL))
        self.curr_title = title

    def render_section(self, section):
        stype = section.get("type")
        
        if stype == "bullet_list":
            self.render_bullet_list(section)
        elif stype == "statement":
            self.render_statement(section)
        elif stype == "definition":
            self.render_definition(section)
        elif stype == "analogy":
            self.render_analogy(section)
        elif stype == "process":
            self.render_process(section)

    def render_bullet_list(self, section):
        heading = Text(section.get("heading", ""), font_size=40, color=YELLOW).to_edge(LEFT).shift(UP * 2)
        self.play(Write(heading))
        
        items = section.get("items", [])
        mobjects = VGroup()
        
        for item in items:
            bullet = Text("• " + item, font_size=32, color=WHITE)
            mobjects.add(bullet)
            
        mobjects.arrange(DOWN, aligned_edge=LEFT, buff=0.5).next_to(heading, DOWN, aligned_edge=LEFT)
        
        for mob in mobjects:
            self.play(FadeIn(mob, shift=RIGHT * 0.5))
            self.wait(0.5)
            
        self.wait(2)
        self.play(FadeOut(heading, mobjects))

    def render_statement(self, section):
        text = section.get("text", "")
        # Wrap text if too long
        stmt = Text(text, font_size=36, t2c={"important": YELLOW}).width_to_edge(RIGHT * 2)
        self.play(Write(stmt))
        self.wait(3)
        self.play(FadeOut(stmt))

    def render_definition(self, section):
        term = Text(section.get("term", ""), font_size=48, color=GREEN).to_edge(UP).shift(DOWN * 1)
        definition = Text(section.get("text", ""), font_size=32).next_to(term, DOWN)
        
        self.play(Write(term))
        self.wait(0.5)
        self.play(FadeIn(definition))
        self.wait(3)
        self.play(FadeOut(term, definition))

    def render_analogy(self, section):
        # Left side: Concept
        concept = Text(section.get("concept", ""), font_size=32, color=BLUE).to_edge(LEFT).shift(RIGHT)
        
        # Right side: Analogy
        analogy = Text(section.get("analogy", ""), font_size=32, color=ORANGE).to_edge(RIGHT).shift(LEFT)
        
        arrow = Arrow(concept.get_right(), analogy.get_left(), buff=0.5)
        
        self.play(FadeIn(concept))
        self.wait(1)
        self.play(GrowArrow(arrow))
        self.play(FadeIn(analogy))
        self.wait(3)
        self.play(FadeOut(concept, analogy, arrow))

    def render_process(self, section):
        steps_data = section.get("steps", [])
        if not steps_data: return
        
        # Robustly handle if steps are strings or dicts
        steps_text = []
        for s in steps_data:
            if isinstance(s, dict):
                # Try to find a text field, or just convert to string
                steps_text.append(s.get("text", s.get("step", str(s))))
            else:
                steps_text.append(str(s))
        
        mobs = VGroup(*[Text(txt, font_size=28) for txt in steps_text])
        mobs.arrange(RIGHT, buff=1.0)
        
        arrows = VGroup()
        for i in range(len(mobs) - 1):
            arrow = Arrow(mobs[i].get_right(), mobs[i+1].get_left(), buff=0.2)
            arrows.add(arrow)
            
        group = VGroup(mobs, arrows).move_to(ORIGIN)
        
        for i, mob in enumerate(mobs):
            self.play(FadeIn(mob, shift=UP))
            if i < len(arrows):
                self.play(GrowArrow(arrows[i]))
            self.wait(1)
            
        self.wait(2)
        self.play(FadeOut(group))

    def clear_screen(self):
        # Keep title, clear everything else
        mobs = [m for m in self.mobjects if m != self.curr_title]
        if mobs:
            self.play(FadeOut(*mobs))

    def play_closing(self):
        self.play(FadeOut(self.curr_title))
        thanks = Text("Thanks for Watching!", font_size=48, color=BLUE)
        self.play(Write(thanks))
        self.wait(2)
        self.play(FadeOut(thanks))
