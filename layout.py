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

def _compute_linear(node, context, horizontal=False):
    _compute_box(node, context)
    key_dim = WIDTH if horizontal else HEIGHT
    
    # compute available flex size and total flex weight
    flex_size = context.w if horizontal else context.h
    flex_weight = 0
    for e in node[ELEMENTS]:
        s = _dget(e, key_dim, {})
        s_fixed = _dget(s, U_FIXED)
        if s_fixed is not None:
            flex_size -= s_fixed         # remove from available flex size
        else:
            s_flex = _dget(s, U_FLEX, 1) # default to flex 1 if no size specified
            assert(s_flex != 0)
            flex_weight += s_flex
    assert(flex_size >= 0)

    # assign dimensions and compute children
    pos = context.x if horizontal else context.y
    for e in node[ELEMENTS]:
        size = None
        
        # assign sizes
        s_obj = _dget(e, key_dim, {})
        s_fixed = _dget(s_obj, U_FIXED)
        s_flex = _dget(s_obj, U_FLEX, 1)
        if s_fixed is not None:
            size = s_fixed
        else:
            size = floor(float(s_flex) / flex_weight * flex_size)

        # compute child
        ctx_x = pos if horizontal else context.x
        ctx_y = pos if not horizontal else context.y
        ctx_w = size if horizontal else context.w
        ctx_h = size if not horizontal else context.h
        new_context = Context(ctx_x, ctx_y, ctx_w, ctx_h, context.compute)
        context.compute(e, new_context)
        pos += size

def _compute_rows(node, context):
    _compute_linear(node, context, horizontal=False)

def _compute_cols(node, context):
    _compute_linear(node, context, horizontal=True)

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
            "cols": _compute_cols,
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
            screen.print(str(node[TEXT]), node[C_X], node[C_Y], fg=Color.rgb(0,0,0))
        if ELEMENTS in node:
            for e in node[ELEMENTS]:
                render_fn(e)
    render_fn(layout[ROOT])

class LayoutTest(App):
    def __init__(self):
        super().__init__()
        self.layout = None
        with open("layout.json") as f:
            self.layout = load_layout(f)
        self._dirty = True  
    
    def update_layout(self):
        if self._dirty:
            self._dirty = False
            self.screen.clear()
            compute_layout(self.layout, self.screen)
            render(self.layout, self.screen)
            self.screen.update()
    
    def on_resize(self):
        self._dirty = True

    def on_frame(self):
        self.update_layout()

if __name__ == "__main__":
    LayoutTest().start()
