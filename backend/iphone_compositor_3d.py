"""
iPhone 16 3D Compositor v11 - CORRECT edge handling
Based on pixel analysis: at 40°, edge is 43px out of 373px = 11.5%
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
import os

RENDER_DIR = "/app/backend/iphone_16_renders_final"
FALLBACK_DIR = "/app/backend/iphone_16_renders_ultra"
FALLBACK_DIR2 = "/app/backend/iphone_16_renders_hd"

AVAILABLE_ANGLES = list(range(-45, 46, 1))


def get_render_path(angle):
    nearest = min(AVAILABLE_ANGLES, key=lambda x: abs(x - angle))
    sign = '+' if nearest >= 0 else ''
    for d in [RENDER_DIR, FALLBACK_DIR, FALLBACK_DIR2]:
        p = os.path.join(d, f"iphone_{sign}{nearest:03d}.png")
        if os.path.exists(p):
            return p
        for o in [0, 1, -1, 2, -2, 3, -3]:
            t = nearest + o
            s = '+' if t >= 0 else ''
            p2 = os.path.join(d, f"iphone_{s}{t:03d}.png")
            if os.path.exists(p2):
                return p2
    return None


def load_render_at_angle(angle):
    p = get_render_path(angle)
    if p:
        return Image.open(p).convert('RGBA')
    for d in [RENDER_DIR, FALLBACK_DIR, FALLBACK_DIR2]:
        for t in [0, 10, -10]:
            s = '+' if t >= 0 else ''
            p = os.path.join(d, f"iphone_{s}{t:03d}.png")
            if os.path.exists(p):
                return Image.open(p).convert('RGBA')
    raise FileNotFoundError("No renders")


def interpolate_renders(angle):
    angle = max(-45, min(45, angle))
    lower = max((a for a in AVAILABLE_ANGLES if a <= angle), default=-45)
    upper = min((a for a in AVAILABLE_ANGLES if a >= angle), default=45)
    if lower == upper:
        return load_render_at_angle(lower)
    try:
        li, ui = load_render_at_angle(lower), load_render_at_angle(upper)
        return Image.blend(li, ui, (angle - lower) / (upper - lower))
    except:
        return load_render_at_angle(round(angle))


def get_phone_bounds(img):
    arr = np.array(img)
    m = arr[:,:,3] > 10
    if not m.any():
        return (0, 0, img.width, img.height)
    rows, cols = m.any(1), m.any(0)
    return (int(np.where(cols)[0][0]), int(np.where(rows)[0][0]),
            int(np.where(cols)[0][-1]), int(np.where(rows)[0][-1]))


def get_screen_rect(phone_bounds, angle_y):
    """
    Calculate screen content area based on phone rotation angle.
    
    At sharp angles (±40-45°), a significant portion of the phone width
    is the visible side edge that must NOT be covered by content.
    
    Pixel analysis at -45°:
    - Phone width: 313 px
    - Side edge + bezel gap: ~44 px = ~14%
    - Safe content should end at ~452 px (from 496 edge)
    
    We use a dynamic margin that scales with angle:
    - 0°: minimal margin (just bezel ~3%)
    - 45°: maximum margin (~15% for side edge + bezel)
    """
    px_min, py_min, px_max, py_max = phone_bounds
    pw = px_max - px_min
    ph = py_max - py_min
    
    # Base margin (just bezel, for front view)
    base = 0.032
    top = 0.025
    bottom = 0.02
    
    # Additional margin for side edge at rotated angles
    # Linear interpolation: 0% at 0°, 15% at 45°
    abs_angle = abs(angle_y)
    angle_factor = min(abs_angle / 45.0, 1.0)
    
    # Edge margin: 0% at 0°, ~15% at 45°
    edge_margin = 0.15 * angle_factor
    
    if angle_y > 0:
        # Positive angle (phone rotated right): LEFT side edge is visible
        left = base + edge_margin
        right = base
    elif angle_y < 0:
        # Negative angle (phone rotated left): RIGHT side edge is visible
        left = base
        right = base + edge_margin
    else:
        left = base
        right = base
    
    sx = px_min + int(pw * left)
    sy = py_min + int(ph * top)
    sw = px_max - sx - int(pw * right)
    sh = py_max - sy - int(ph * bottom)
    
    return (sx, sy, max(1, sw), max(1, sh))


def apply_perspective(img, angle_y):
    if abs(angle_y) < 3:
        return img
    w, h = img.size
    c = abs(math.sin(math.radians(angle_y))) * 0.12
    v = int(h * c * 0.5)
    if angle_y > 0:
        coeffs = find_coeffs([(0,0),(w,0),(w,h),(0,h)], [(0,0),(w,v),(w,h-v),(0,h)])
    else:
        coeffs = find_coeffs([(0,0),(w,0),(w,h),(0,h)], [(0,v),(w,0),(w,h),(0,h-v)])
    return img.transform((w, h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)


def find_coeffs(src, dst):
    m = []
    for s, d in zip(src, dst):
        m.append([d[0], d[1], 1, 0, 0, 0, -s[0]*d[0], -s[0]*d[1]])
        m.append([0, 0, 0, d[0], d[1], 1, -s[1]*d[0], -s[1]*d[1]])
    return tuple(np.linalg.lstsq(np.array(m, dtype=np.float64), 
                np.array([p for pair in src for p in pair], dtype=np.float64), rcond=None)[0])


def create_mask(phone_img, rect, angle_y=0):
    """
    Create mask for screen area using geometric approach.
    
    At rotated angles, the visible side edge has a varying width.
    We use more aggressive margins to ensure content stays well inside
    the visible screen area.
    
    Key insight: The screen rect already has margins from get_screen_rect(),
    but additional masking is needed to follow the curved/tapered edge shape.
    """
    sx, sy, sw, sh = rect
    arr = np.array(phone_img)
    alpha = arr[:,:,3]
    
    # Start with full white mask
    mask = np.ones((sh, sw), dtype=np.uint8) * 255
    
    abs_angle = abs(angle_y)
    
    # Calculate side edge exclusion with more aggressive margins
    # The visible side edge is wider at the top and narrower at the bottom
    if abs_angle > 3:
        # Scale with angle: 0% at 0°, max at 45°
        angle_factor = min(abs_angle / 45.0, 1.0)
        
        # More aggressive margins: 25% at top, 8% at bottom at 45°
        top_edge_pct = 0.25 * angle_factor
        bottom_edge_pct = 0.08 * angle_factor
        
        for y in range(sh):
            # Linear interpolation of edge width from top to bottom
            y_factor = y / max(sh - 1, 1)  # 0 at top, 1 at bottom
            edge_pct = top_edge_pct * (1 - y_factor) + bottom_edge_pct * y_factor
            edge_width = int(sw * edge_pct)
            
            if angle_y < 0:
                # Negative angle: right side edge visible, mask RIGHT side
                for x in range(max(0, sw - edge_width), sw):
                    mask[y, x] = 0
            else:
                # Positive angle: left side edge visible, mask LEFT side
                for x in range(min(edge_width, sw)):
                    mask[y, x] = 0
    
    # Exclude Dynamic Island (top center area)
    # DI is about 6% height, centered
    di_height = int(sh * 0.06)
    di_margin = int(sw * 0.15)
    for y in range(min(di_height, sh)):
        iy = sy + y
        if iy >= arr.shape[0]:
            continue
        for x in range(di_margin, sw - di_margin):
            ix = sx + x
            if ix >= arr.shape[1]:
                continue
            if alpha[iy, ix] < 15:
                mask[y, x] = 0
                continue
            r, g, b = arr[iy, ix, 0], arr[iy, ix, 1], arr[iy, ix, 2]
            brightness = int(r) + int(g) + int(b)
            if brightness < 30:
                mask[y, x] = 0
    
    # Mask any transparent areas
    for y in range(sh):
        iy = sy + y
        if iy >= arr.shape[0]:
            continue
        for x in range(sw):
            ix = sx + x
            if ix >= arr.shape[1]:
                continue
            if alpha[iy, ix] < 15:
                mask[y, x] = 0
    
    return Image.fromarray(mask, 'L').filter(ImageFilter.GaussianBlur(1.5))


def composite(phone, video, angle):
    result = phone.copy()
    bounds = get_phone_bounds(phone)
    rect = get_screen_rect(bounds, angle)
    sx, sy, sw, sh = rect
    
    if sw <= 10 or sh <= 10:
        return result
    
    vid = video.resize((sw, sh), Image.Resampling.LANCZOS)
    vid = apply_perspective(vid, angle)
    if vid.mode != 'RGBA':
        vid = vid.convert('RGBA')
    
    mask = create_mask(phone, rect, angle)
    result.paste(vid, (sx, sy), mask)
    return result


def gradient(w, h, c1, c2):
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt((x-w/2)**2 + (y-h/2)**2)
    t = np.clip(d / (math.sqrt(w*w+h*h)/2), 0, 1) ** 0.6
    return Image.fromarray(np.stack([
        (c1[0]*(1-t)+c2[0]*t).astype(np.uint8),
        (c1[1]*(1-t)+c2[1]*t).astype(np.uint8),
        (c1[2]*(1-t)+c2[2]*t).astype(np.uint8)
    ], -1), 'RGB')


def shadow(pw, ph, px, py, size, angle):
    s = Image.new('RGBA', size, (0,0,0,0))
    d = ImageDraw.Draw(s)
    sw, sh = int(pw*0.4), int(pw*0.04)
    sx = px + (pw-sw)//2 + int(angle*0.5)
    sy = min(py + ph + 12, size[1] - sh - 8)
    for i in range(20, 0, -1):
        d.ellipse([sx-(20-i)*3, sy-(20-i)//4*3, sx+sw+(20-i)*3, sy+sh+(20-i)//4*3], 
                  fill=(0,0,0,int(18*i/20)))
    return s.filter(ImageFilter.GaussianBlur(10))


def ease(t):
    return t*t*t*(t*(t*6-15)+10)

def ease_in_out(t):
    return -(math.cos(math.pi*t)-1)/2


def render_3d_phone_frame(video, time_progress, output_size=(1080,1920),
                          bg1=(90,15,15), bg2=(15,5,5), animation_style="camera"):
    ow, oh = output_size
    
    if animation_style == "camera":
        if time_progress < 0.5:
            t = ease(time_progress / 0.5)
            angle = 40 - 35*t
            zoom = 1.0 + 0.12*t
        else:
            t = ease((time_progress-0.5)/0.5)
            angle = 5 - 18*t
            zoom = 1.12 + 0.08*t
    elif animation_style == "float":
        angle = 12 * math.sin(time_progress * math.pi * 1.5)
        zoom = 1.0
    else:
        angle, zoom = 8, 1.0
    
    phone = interpolate_renders(angle)
    phone = composite(phone, video, angle)
    
    arr = np.array(phone)
    m = arr[:,:,3] > 10
    if m.any():
        rows, cols = m.any(1), m.any(0)
        phone = phone.crop((np.where(cols)[0][0], np.where(rows)[0][0],
                           np.where(cols)[0][-1]+1, np.where(rows)[0][-1]+1))
    
    scale = oh * 0.60 / phone.height * zoom
    fw, fh = int(phone.width*scale), int(phone.height*scale)
    margin = int(ow*0.05)
    if fw > ow-2*margin:
        r = (ow-2*margin)/fw
        fw, fh = int(fw*r), int(fh*r)
    if fh > oh-2*margin:
        r = (oh-2*margin)/fh
        fw, fh = int(fw*r), int(fh*r)
    
    phone = phone.resize((fw, fh), Image.Resampling.LANCZOS)
    
    px = max(margin, min((ow-fw)//2 + int(angle*1.2), ow-fw-margin))
    py = (oh-fh)//2
    
    bg = gradient(ow, oh, bg1, bg2).convert('RGBA')
    bg = Image.alpha_composite(bg, shadow(fw, fh, px, py, output_size, angle))
    bg.paste(phone, (px, py), phone)
    
    return bg.convert('RGB')


# Compat
def render_phone_frame(v,t,s=(1080,1920),c1=(90,15,15),c2=(15,5,5),p="c",a="camera"):
    return render_3d_phone_frame(v,t,s,c1,c2,a)
def render_dynamic_phone(video_frame=None, time_progress=0, output_size=(1080,1920), bg_color=(90,15,15), 
                         bg_color2=None, phone_scale=0.55, animation_style="camera", position="center",
                         v=None, t=None, s=None, c=None, c2=None, ps=None, a=None, p=None):
    # Support both old positional style and new named arguments
    vf = video_frame if video_frame is not None else v
    tp = time_progress if time_progress != 0 else (t if t is not None else 0)
    os = output_size if output_size != (1080,1920) else (s if s is not None else (1080,1920))
    bc = bg_color if bg_color != (90,15,15) else (c if c is not None else (90,15,15))
    bc2 = bg_color2 or c2 or tuple(max(0,x-70) for x in bc)
    astyle = animation_style if animation_style != "camera" else (a if a is not None else "camera")
    return render_3d_phone_frame(vf, tp, os, bc, bc2, astyle)
def render_camera_animation(v,t,s=(1080,1920),c1=(90,15,15),c2=(15,5,5),**k):
    return render_3d_phone_frame(v,t,s,c1,c2,"camera")
def render_simple_float(v,t,s=(1080,1920),c1=(90,15,15),c2=(15,5,5),**k):
    return render_3d_phone_frame(v,t,s,c1,c2,"float")
def render_full_phone_animation(v,t,s=(1080,1920),c1=(90,15,15),c2=(15,5,5),**k):
    return render_3d_phone_frame(v,t,s,c1,c2,"camera")
def get_base_iphone():
    i=load_render_at_angle(0); return i,Image.new('L',i.size,255)
def create_3d_iphone_mockup(c,r=25,w=400,h=820):
    return composite(load_render_at_angle(r),c,r)
def load_render(a): return load_render_at_angle(a)
def load_base_render(): return load_render_at_angle(0)
def apply_perspective_transform(i,a,x=0): return apply_perspective(i,a)
def find_screen_region(p): return get_screen_rect(get_phone_bounds(p),0)
def composite_screen_content(p,v,a=0): return composite(p,v,a)
def composite_screen_locked(p,v): return composite(p,v,0)


# Compatibility aliases
def create_gradient_bg(w, h, c1, c2): return gradient(w, h, c1, c2)
def create_shadow(pw, ph, px, py, size, angle): return shadow(pw, ph, px, py, size, angle)