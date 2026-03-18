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
    Calculate screen content area.
    Uses fixed proportions relative to phone bounds for stability during animation.
    """
    px_min, py_min, px_max, py_max = phone_bounds
    pw = px_max - px_min
    ph = py_max - py_min
    
    # Minimal margins - video fills almost entire screen
    margin_h = 0.008      # very small horizontal margin
    margin_top = 0.003    # minimal top
    margin_bottom = 0.003 # minimal bottom
    
    # Calculate screen rect
    sx = px_min + int(pw * margin_h)
    sy = py_min + int(ph * margin_top)
    sw = pw - int(pw * margin_h * 2)
    sh = ph - int(ph * (margin_top + margin_bottom))
    
    return (sx, sy, max(1, sw), max(1, sh))


def apply_perspective(img, angle_y):
    """
    Apply perspective transform to video to match phone rotation.
    Larger coefficient = more pronounced 3D effect.
    """
    if abs(angle_y) < 3:
        return img
    w, h = img.size
    
    # Perspective strength - increased for more realistic 3D look
    # 0.18 gives noticeable but not extreme perspective
    strength = 0.18
    c = abs(math.sin(math.radians(angle_y))) * strength
    v = int(h * c * 0.5)
    
    if angle_y > 0:
        # Phone rotated right - right side of video appears further
        coeffs = find_coeffs([(0,0),(w,0),(w,h),(0,h)], [(0,0),(w,v),(w,h-v),(0,h)])
    else:
        # Phone rotated left - left side of video appears further
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
    Create mask for screen area.
    Uses color analysis: screen has a blue tint (B > R), 
    while side edge is neutral gray (R ≈ G ≈ B).
    """
    sx, sy, sw, sh = rect
    arr = np.array(phone_img)
    r_ch, g_ch, b_ch, alpha = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]
    
    mask = np.zeros((sh, sw), dtype=np.uint8)
    
    for y in range(sh):
        iy = sy + y
        if iy >= arr.shape[0]:
            continue
        for x in range(sw):
            ix = sx + x
            if ix >= arr.shape[1]:
                continue
            
            if alpha[iy, ix] < 15:
                continue
            
            r, g, b = int(r_ch[iy, ix]), int(g_ch[iy, ix]), int(b_ch[iy, ix])
            brightness = r + g + b
            
            # Screen material has:
            # - brightness in range 90-120
            # - blue tint: B > R by at least 5
            # - B > G by at least 5
            is_screen = (
                90 <= brightness <= 120 and
                b > r + 5 and
                b > g + 5
            )
            
            if is_screen:
                mask[y, x] = 255
    
    # Light blur for smooth edges
    return Image.fromarray(mask, 'L').filter(ImageFilter.GaussianBlur(0.8))


def get_base_screen_size():
    """
    Get base screen size from phone at 0 degrees.
    Used to maintain consistent video scaling across all angles.
    """
    phone = load_render_at_angle(0)
    bounds = get_phone_bounds(phone)
    pw = bounds[2] - bounds[0]
    ph = bounds[3] - bounds[1]
    # Use same margins as get_screen_rect
    margin_h = 0.008
    margin_top = 0.003
    margin_bottom = 0.003
    sw = pw - int(pw * margin_h * 2)
    sh = ph - int(ph * (margin_top + margin_bottom))
    return sw, sh

# Cache base screen size
_BASE_SCREEN_SIZE = None

def composite(phone, video, angle):
    """
    Composite video onto phone screen.
    Preserves original video aspect ratio with letterbox/pillarbox (black bars).
    Video size is calculated based on 0-degree screen size to prevent scaling during animation.
    """
    global _BASE_SCREEN_SIZE
    if _BASE_SCREEN_SIZE is None:
        _BASE_SCREEN_SIZE = get_base_screen_size()
    
    result = phone.copy()
    bounds = get_phone_bounds(phone)
    rect = get_screen_rect(bounds, angle)
    sx, sy, sw, sh = rect
    
    if sw <= 10 or sh <= 10:
        return result
    
    # Use BASE screen size for video scaling (prevents size changes during animation)
    base_sw, base_sh = _BASE_SCREEN_SIZE
    
    vw, vh = video.size
    video_ratio = vw / vh
    base_ratio = base_sw / base_sh
    
    # Calculate video size based on BASE screen (not current rotated screen)
    if video_ratio > base_ratio:
        # Video is wider - fit by width
        vid_w = base_sw
        vid_h = int(base_sw / video_ratio)
    else:
        # Video is taller - fit by height
        vid_h = base_sh
        vid_w = int(base_sh * video_ratio)
    
    # Resize video ONCE to fixed size
    vid_resized = video.resize((vid_w, vid_h), Image.Resampling.LANCZOS)
    
    # Create container matching BASE screen size
    vid_container = Image.new('RGBA', (base_sw, base_sh), (0, 0, 0, 255))
    
    # Center video in container
    paste_x = (base_sw - vid_w) // 2
    paste_y = (base_sh - vid_h) // 2
    if vid_resized.mode != 'RGBA':
        vid_resized = vid_resized.convert('RGBA')
    vid_container.paste(vid_resized, (paste_x, paste_y))
    
    # NOW resize container to match current screen rect
    vid = vid_container.resize((sw, sh), Image.Resampling.LANCZOS)
    
    # Apply perspective transform
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


def smooth_position(angle, base_x, width, margin):
    """Calculate smooth phone position based on angle"""
    # Use smooth sine-based offset instead of linear
    offset = math.sin(math.radians(angle)) * width * 0.08
    x = base_x + offset
    return max(margin, min(int(x), width - margin))


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
    
    # Smooth position calculation
    base_x = (ow - fw) // 2
    px = smooth_position(angle, base_x, ow - fw, margin)
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