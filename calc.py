from termpixels.screen import Color
from termpixels.app import App
from layout import load_layout, compute_layout, render, get_at_pos, get_by_name
import operator

def node_name(node):
    if "name" not in node:
        return ""
    return node["name"]

class CalcApp(App):
    def __init__(self):
        super().__init__(mouse=True)
        self.layout = None
        with open("layout.json") as f:
            self.layout = load_layout(f)
        self._dirty = True
        self._layout_dirty = True
        self._last_hit = None
        self.clear_all()
    
    def clear_all(self):
        self.display_register = 0
        self.operand_register = 0
        self.operator = None
        self._dirty = True
    
    def set_operator(self, op):
        if self.operator is not None:
            self.apply_operator()
        self.operator = op
        self.operand_register = self.display_register
        self.display_register = 0
        self._dirty = True
    
    def apply_operator(self):
        if self.operator is None:
            return
        self.display_register = self.operator(self.operand_register, self.display_register)
        self.operand_register = 0
        self.operator = None
        self._dirty = True
    
    def update_layout(self):
        def stylizer(node, style):
            if node == self._last_hit and (node_name(node).startswith("btn") or node_name(node).startswith("num")):
                style["bg"] -= 30
                style["fg"] -= 30
            return style
        
        if self._dirty:
            self._dirty = False
            self.screen.clear()
            if self._layout_dirty:
                compute_layout(self.layout, self.screen)
            out = get_by_name(self.layout, "text_output")
            out["text"] = "{:,}".format(self.display_register)
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
            if hit:
                name = node_name(hit)
                if name == "btn_ac":
                    self.clear_all()
                elif name == "btn_+":
                    self.set_operator(operator.add)
                elif name == "btn_-":
                    self.set_operator(operator.sub)
                elif name == "btn_*":
                    self.set_operator(operator.mul)
                elif name == "btn_/":
                    self.set_operator(operator.floordiv)
                elif name == "btn_=":
                    self.apply_operator()
                elif name.startswith("num"):
                    num = int(hit["name"][4:])
                    self.display_register = self.display_register * 10 + num
                    self._dirty = True

    def on_resize(self):
        self._dirty = True
        self._layout_dirty = True

    def on_frame(self):
        self.update_layout()

if __name__ == "__main__":
    CalcApp().start()
