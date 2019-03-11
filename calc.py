from termpixels.screen import Color
from termpixels.app import App
from layout import load_layout, compute_layout, render, get_at_pos, get_by_name

class CalcApp(App):
    def __init__(self):
        super().__init__(mouse=True)
        self.layout = None
        with open("layout.json") as f:
            self.layout = load_layout(f)
        self._dirty = True
        self._layout_dirty = True
        self._last_hit = None
    
    def update_layout(self):
        def stylizer(node, style):
            if node == self._last_hit and not ("name" in node and node["name"].startswith("text")):
                style["bg"] -= 30
                style["fg"] -= 30
            return style
        
        if self._dirty:
            self._dirty = False
            self.screen.clear()
            if self._layout_dirty:
                compute_layout(self.layout, self.screen)
            render(self.layout, self.screen, stylizer)
            self.screen.update()

    def on_mouse(self, m):
        hit = get_at_pos(self.layout, m.x, m.y)

        if hit != self._last_hit:
            # Mouse over detection
            self._last_hit = hit
            self._dirty = True

        if m.left and m.down:
            # click detection
            if hit and "name" in hit:
                num = int(hit["name"][4:])
                out = get_by_name(self.layout, "text_output")
                out["text"] += str(num)
                self._dirty = True

    def on_resize(self):
        self._dirty = True
        self._layout_dirty = True

    def on_frame(self):
        self.update_layout()

if __name__ == "__main__":
    CalcApp().start()
