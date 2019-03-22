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
STYLE = "style"
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

def get_at_pos(layout, x, y):
    """Get the topmost element covering the given position."""
    assert(COMPUTED in layout)
    def check(node):
        if ELEMENTS in node:
            for e in node[ELEMENTS]:
                hit = check(e)
                if hit:
                    return hit
        nx = node[C_X]
        ny = node[C_Y]
        nw = node[C_W]
        nh = node[C_H]
        if x >= nx and y >= ny and x < nx+nw and y < ny+nh:
            return node
        return None
    return check(layout[ROOT])

def get_by_name(layout, name):
    """Get element by name."""
    assert(COMPUTED in layout)
    def find(node):
        if ELEMENTS in node:
            for e in node[ELEMENTS]:
                found = find(e)
                if found:
                    return found
        if "name" in node and node["name"] == name:
            return node
        return None
    return find(layout[ROOT])

def _merge(source, target):
    result = target.copy()
    for k, v in source.items():
        result[k] = v
    return result

STYLE_DEFAULTS = {
    "bg": Color.rgb(0.2,0.2,0.2),
    "fg": Color.rgb(0.8,0.8,0.8),
    "h-align": "left",
    "v-align": "top"
    }

def _parse_style(style):
    s = style.copy()
    if "fg" in s:
        s["fg"] = Color(s["fg"])
    if "bg" in s:
        s["bg"] = Color(s["bg"])
    return s

def _render_box(node, screen, style):
    col = 30

    # background
    screen.fill(node[C_X], node[C_Y], node[C_W], node[C_H], bg=style["bg"])
    
    # bottom/right
    screen.fill(node[C_X] + node[C_W] - 1, node[C_Y] + 1, 1, node[C_H] - 1, char="│", fg=style["bg"] - col)
    screen.fill(node[C_X] + 1, node[C_Y] + node[C_H] - 1, node[C_W] - 1, 1, char="─", fg=style["bg"] - col)

    # top/left
    screen.fill(node[C_X], node[C_Y], 1, node[C_H] - 1, char="│", fg=style["bg"] + col)
    screen.fill(node[C_X], node[C_Y], node[C_W] - 1, 1, char="─", fg=style["bg"] + col)

    screen.print("┘", node[C_X] + node[C_W] - 1, node[C_Y] + node[C_H] - 1, fg=style["bg"] - col)
    screen.print("┌", node[C_X], node[C_Y], fg=style["bg"] + col)

    if TEXT in node:
        lines = str(node[TEXT]).splitlines()
        th = len(lines)
        halign = style["h-align"]
        valign = style["v-align"]
        def start_pos(align, size, max_size):
            if align == "left" or align == "top":
                return 0
            if align == "right" or align == "bottom":
                return max_size - size - 1
            if align == "center":
                return floor(max_size / 2 - size / 2)
            raise Exception("invalid alignment specifier: {}".format(align))
        y0 = start_pos(valign, th, node[C_H] - 1) + node[C_Y] + 1
        for i, line in enumerate(lines):
            screen.print(line, start_pos(halign, len(line), node[C_W] - 1) + node[C_X] + 1, y0+i, fg=style["fg"])

def render(layout, screen, stylizer=lambda _, __: {}):
    assert(COMPUTED in layout)
    def render_fn(node, base_style):
        style = base_style
        if STYLE in node:
            style = _merge(_parse_style(node[STYLE]), style)
        style = _merge(stylizer(node, style), style)
        if node[TYPE] == "box":
            _render_box(node, screen, style)
        if ELEMENTS in node:
            for e in node[ELEMENTS]:
                render_fn(e, style.copy())
    render_fn(layout[ROOT], STYLE_DEFAULTS.copy())
