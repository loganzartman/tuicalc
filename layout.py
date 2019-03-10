import json
from math import floor
from termpixels.screen import Color
from termpixels.app import App

ROOT = "root"
TYPE = "type"
ELEMENTS = "elements"
WIDTH = "width"
HEIGHT = "height"
TEXT = "text"
U_FIXED = "fixed"
U_FLEX = "flex"

COMPUTED = "_computed"
C_W = "_width"
C_H = "_height"
C_X = "_x"
C_Y = "_y"

prop_defaults = {
    "width": {"weight": 1},
    "height": {"weight": 1}
}

class Context:
    def __init__(self, x, y, w, h, compute):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.compute = compute

def load_layout(str_or_file):
    """Read a JSON layout from a string or file-like object."""
    layout = None
    try:
        layout = json.load(str_or_file)
    except AttributeError:
        layout = json.loads(str_or_file)
    assert(ROOT in layout)
    return layout

def _dget(node, key, default=None):
    """Get value associated with key or return default if it doesn't exist."""
    if key not in node:
        return default
    return node[key]

def _compute_rows(node, context):
    _compute_box(node, context)

    # compute available flex size and total flex weight
    flex_height = context.h
    flex_weight = 0
    for e in node[ELEMENTS]:
        h = _dget(e, HEIGHT, {})
        h_fixed = _dget(h, U_FIXED)
        if h_fixed is not None:
            flex_height -= h_fixed       # remove from available flex size
        else:
            h_flex = _dget(h, U_FLEX, 1) # default to flex 1 if no size specified
            assert(h_flex != 0)
            flex_weight += h_flex
    assert(flex_height >= 0)

    # assign dimensions and compute children
    x = context.x
    y = context.y
    for e in node[ELEMENTS]:
        w = context.w
        h = None
        
        # assign sizes
        h_obj = _dget(e, HEIGHT, {})
        h_fixed = _dget(h_obj, U_FIXED)
        h_flex = _dget(h_obj, U_FLEX, 1)
        if h_fixed is not None:
            h = h_fixed
        else:
            h = floor(float(h_flex) / flex_weight * flex_height)

        # compute child
        new_context = Context(x, y, w, h, context.compute)
        context.compute(e, new_context)
        y += h

def _compute_box(node, context):
    node[C_X] = context.x
    node[C_Y] = context.y
    node[C_W] = context.w
    node[C_H] = context.h

def compute_layout(layout, screen):
    """Tag a layout dict with computed values for rendering."""
    def compute(node, context):
        return {
            "rows": _compute_rows,
            "box": _compute_box
        }[node[TYPE]](node, context)
    compute(layout[ROOT], Context(0, 0, screen.w, screen.h, compute))
    layout[COMPUTED] = True

def render(layout, screen):
    assert(COMPUTED in layout)
    def render_fn(node):
        screen.fill(node[C_X], node[C_Y], node[C_W], node[C_H], bg=Color.rgb(0,0,0))
        screen.fill(node[C_X], node[C_Y], node[C_W]-1, node[C_H]-1, bg=Color.rgb(0.5,0.5,0.5))
        if TEXT in node:
            screen.print(node[TEXT], node[C_X], node[C_Y], fg=Color.rgb(0,0,0))
        if ELEMENTS in node:
            for e in node[ELEMENTS]:
                render_fn(e)
    render_fn(layout[ROOT])

class LayoutTest(App):
    def __init__(self):
        super().__init__()
        self.layout = None
        with open("simple_layout.json") as f:
            self.layout = load_layout(f)
        self._dirty = True  
    
    def update_layout(self):
        if self._dirty:
            self._dirty = False
            compute_layout(self.layout, self.screen)
            render(self.layout, self.screen)
            self.screen.update()
    
    def on_resize(self):
        self._dirty = True

    def on_frame(self):
        self.update_layout()

if __name__ == "__main__":
    LayoutTest().start()
