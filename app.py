import io
import os
import streamlit as st
from PIL import Image, ImageOps, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════════════════════
# 🔐 SECURITY SETTINGS — Edit these values to customize your app
# ═══════════════════════════════════════════════════════════════════
APP_PASSWORD = "KDPCOVER2026"
BRAND_NAME = "KDPEasy Studio"
WELCOME_MESSAGE = "Welcome, VIP Customer!"
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="KDPEasy Cover Builder",
    page_icon="📕",
    layout="wide",
)

CUSTOM_CSS = """
<style>
    .main > div { padding-top: 2rem; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf3 100%); }
    .block-container { max-width: 1200px; }
    h1 { color: #1f2937; font-weight: 700; }
    .stButton>button {
        background-color: #4f46e5; color: white; border: none;
        border-radius: 8px; padding: 0.6rem 1.2rem; font-weight: 600;
    }
    .stButton>button:hover { background-color: #4338ca; color: white; }
    .stDownloadButton>button {
        background-color: #10b981; color: white; border: none;
        border-radius: 8px; padding: 0.6rem 1.2rem; font-weight: 600;
    }
    .stDownloadButton>button:hover { background-color: #059669; color: white; }
    .info-card {
        background: white; padding: 1rem 1.2rem; border-radius: 10px;
        border-left: 4px solid #4f46e5; margin-bottom: 1rem;
    }
    .warn-card {
        background: #fffbeb; padding: 1rem 1.2rem; border-radius: 10px;
        border-left: 4px solid #f59e0b; margin-bottom: 1rem; color: #92400e;
    }
    .login-card {
        background: white; padding: 2.5rem 2rem; border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08); max-width: 480px;
        margin: 3rem auto; text-align: center;
    }
    .login-card h2 { color: #1f2937; margin-bottom: 0.5rem; }
    .login-card .brand { color: #4f46e5; font-weight: 700; font-size: 1.1rem; margin-bottom: 1.5rem; }
    .login-card .desc { color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# 🔐 PASSWORD GATE
# ═══════════════════════════════════════════════════════════════════
def check_password():
    if st.session_state.get("password_correct", False):
        return True

    st.markdown(
        f"""
        <div class='login-card'>
            <h2>🔐 {WELCOME_MESSAGE}</h2>
            <div class='brand'>✨ {BRAND_NAME} ✨</div>
            <div class='desc'>
                This is an exclusive tool for our valued customers.<br>
                Please enter your access password to continue.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input(
            "🔑 Access Password", type="password",
            placeholder="Enter your password here...", key="password_input",
        )
        if st.button("🚀 Unlock App", width="stretch"):
            if password == APP_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please contact support if you need access.")
    return False


if not check_password():
    st.stop()


# ═══════════════════════════════════════════════════════════════════
# 📚 KDP TRIM SIZES (width, height in inches)
# ═══════════════════════════════════════════════════════════════════
BOOK_SIZES = {
    "6 × 9 in — Most popular": (6.0, 9.0),
    "8.5 × 11 in — Letter / large coloring book": (8.5, 11.0),
    "8 × 10 in": (8.0, 10.0),
    "5.5 × 8.5 in — Digest": (5.5, 8.5),
    "5 × 8 in — Compact gift size": (5.0, 8.0),
}

# KDP spine width factor = inches of spine per page
PAPER_TYPES = {
    "White (B&W interior)": 0.002252,
    "Cream (B&W interior)": 0.0025,
}

BLEED_IN = 0.125
DPI = 300
MIN_PAGES = 24

# Approximate barcode safe-zone (KDP guidance): keep this area free of
# important text/art on the back cover — KDP stamps the real barcode here
# automatically after upload. Always double-check on KDP's own proof previewer.
BARCODE_W_IN = 2.0
BARCODE_H_IN = 1.2
BARCODE_INSET_IN = 0.25

# General safe zone: keep titles/text/important art this far inside the
# trim line (industry-standard guidance) so nothing looks accidentally
# cropped, even if the physical cutter is slightly off.
SAFE_ZONE_IN = 0.25

FONTS_DIR = os.path.dirname(os.path.abspath(__file__))

# label -> (font file, bold variation name for variable fonts, or None for static fonts)
FONTS = {
    "Playful, rounded (kids' coloring books)": ("Baloo2-Bold.ttf", "Bold"),
    "Playful, bouncy (kids' coloring books)": ("Fredoka-Bold.ttf", "Bold"),
    "Elegant, high-contrast (adult coloring / affirmation)": ("PlayfairDisplay-Bold.ttf", "Bold"),
    "Elegant, soft (adult coloring / affirmation)": ("CormorantGaramond-Bold.ttf", "Bold"),
    "Modern, clean (planner / journal)": ("Montserrat-Bold.ttf", "Bold"),
    "Modern, rounded (planner / journal)": ("Poppins-Bold.ttf", None),
    "Formal script (quote book)": ("GreatVibes-Regular.ttf", None),
    "Casual script (quote book)": ("DancingScript-Bold.ttf", "Bold"),
    "Bold, sturdy (versatile)": ("Anton-Regular.ttf", None),
    "Bold, tall & narrow (versatile)": ("BebasNeue-Regular.ttf", None),
}


def load_font(font_file, variation, size_px):
    path = os.path.join(FONTS_DIR, font_file)
    font = ImageFont.truetype(path, size_px)
    if variation:
        try:
            font.set_variation_by_name(variation.encode())
        except Exception:
            pass
    return font


def _wrap_text(draw, text, font, max_width_px):
    words = text.split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        trial = current + " " + word
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width_px:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_centered_block(draw, lines, font, center_x, top_y, fill_color, line_spacing=1.15):
    y = top_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        draw.text((center_x - line_w / 2, y - bbox[1]), line, font=font, fill=fill_color)
        y += line_h * line_spacing
    return y


def add_cover_text(
    canvas, panel_w_px, full_h_px, full_w_px, font_file, font_variation,
    title, title_size_pt, title_color_hex,
    subtitle, subtitle_size_pt, subtitle_color_hex,
    author, author_size_pt, author_color_hex,
):
    """Draw title/subtitle/author onto the front cover panel (mutates canvas in place)."""
    draw = ImageDraw.Draw(canvas)

    title_px = round(title_size_pt * DPI / 72)
    subtitle_px = round(subtitle_size_pt * DPI / 72)
    author_px = round(author_size_pt * DPI / 72)

    front_left = full_w_px - panel_w_px
    safe_px = round(BLEED_IN * DPI) + round(SAFE_ZONE_IN * DPI)
    text_left = front_left + safe_px
    text_right = full_w_px - safe_px
    max_width_px = text_right - text_left
    center_x = (text_left + text_right) / 2

    top_y = round(full_h_px * 0.08)

    if title.strip():
        font = load_font(font_file, font_variation, title_px)
        lines = _wrap_text(draw, title.strip(), font, max_width_px)
        top_y = _draw_centered_block(draw, lines, font, center_x, top_y, title_color_hex)
        top_y += title_px * 0.25

    if subtitle.strip():
        font = load_font(font_file, font_variation, subtitle_px)
        lines = _wrap_text(draw, subtitle.strip(), font, max_width_px)
        _draw_centered_block(draw, lines, font, center_x, top_y, subtitle_color_hex)

    if author.strip():
        font = load_font(font_file, font_variation, author_px)
        bbox = draw.textbbox((0, 0), author.strip(), font=font)
        author_h = bbox[3] - bbox[1]
        author_y = full_h_px - safe_px - author_h * 1.3
        _draw_centered_block(draw, [author.strip()], font, center_x, author_y, author_color_hex)


def calc_dimensions(trim_w, trim_h, page_count, spine_factor):
    spine_w_in = page_count * spine_factor
    panel_w_in = trim_w + BLEED_IN
    full_w_in = trim_w * 2 + spine_w_in + BLEED_IN * 2
    full_h_in = trim_h + BLEED_IN * 2
    return spine_w_in, panel_w_in, full_w_in, full_h_in


def build_cover(front_img, back_img, trim_w, trim_h, page_count, spine_factor, spine_color_hex):
    spine_w_in, panel_w_in, full_w_in, full_h_in = calc_dimensions(
        trim_w, trim_h, page_count, spine_factor
    )

    full_w_px = round(full_w_in * DPI)
    full_h_px = round(full_h_in * DPI)
    panel_w_px = round(panel_w_in * DPI)
    spine_w_px = full_w_px - panel_w_px * 2

    canvas = Image.new("RGB", (full_w_px, full_h_px), spine_color_hex)

    back_fit = ImageOps.fit(
        back_img.convert("RGB"), (panel_w_px, full_h_px), method=Image.LANCZOS
    )
    front_fit = ImageOps.fit(
        front_img.convert("RGB"), (panel_w_px, full_h_px), method=Image.LANCZOS
    )

    canvas.paste(back_fit, (0, 0))
    canvas.paste(front_fit, (full_w_px - panel_w_px, 0))

    return canvas, full_w_px, full_h_px, spine_w_px, panel_w_px


def _dashed_rect(draw, x0, y0, x1, y1, color, dash=14, width=4):
    for x in range(x0, x1, dash * 2):
        draw.line([(x, y0), (min(x + dash, x1), y0)], fill=color, width=width)
        draw.line([(x, y1), (min(x + dash, x1), y1)], fill=color, width=width)
    for y in range(y0, y1, dash * 2):
        draw.line([(x0, y), (x0, min(y + dash, y1))], fill=color, width=width)
        draw.line([(x1, y), (x1, min(y + dash, y1))], fill=color, width=width)


def add_preview_guides(canvas, panel_w_px, full_h_px):
    """Draw guide lines for preview only — NOT included in the final download."""
    preview = canvas.copy()
    draw = ImageDraw.Draw(preview)
    full_w_px = preview.width

    bleed_px = round(BLEED_IN * DPI)

    # Trim line (blue) — everything OUTSIDE this rectangle is bleed and
    # gets physically cut off by the printer. Marks top/bottom/outer-left/
    # outer-right; the spine's own edges never get bleed since they're
    # folded, not cut, so a single rectangle across the full width is correct.
    _dashed_rect(
        draw,
        bleed_px, bleed_px,
        full_w_px - bleed_px, full_h_px - bleed_px,
        color="#3b82f6",
    )

    # General safe zone (amber) — keep titles/text/important art inside this
    # line, 0.25in further in from the trim line, on all outer trim edges.
    safe_px = bleed_px + round(SAFE_ZONE_IN * DPI)
    _dashed_rect(
        draw,
        safe_px, safe_px,
        full_w_px - safe_px, full_h_px - safe_px,
        color="#f59e0b",
    )

    # Barcode safe zone (red) — bottom-right corner of the back cover panel
    inset_px = round(BARCODE_INSET_IN * DPI)
    bw_px = round(BARCODE_W_IN * DPI)
    bh_px = round(BARCODE_H_IN * DPI)
    right_x = panel_w_px - inset_px
    left_x = right_x - bw_px
    bottom_y = (full_h_px - bleed_px) - inset_px
    top_y = bottom_y - bh_px
    _dashed_rect(draw, left_x, top_y, right_x, bottom_y, color="#ef4444")

    return preview


def sample_edge_color(front_img, panel_w_px, full_h_px):
    """Suggest a spine color by averaging a strip near the front cover's spine-side edge."""
    fit = ImageOps.fit(front_img.convert("RGB"), (panel_w_px, full_h_px), method=Image.LANCZOS)
    strip_w = max(1, panel_w_px // 20)
    strip = fit.crop((0, 0, strip_w, full_h_px))
    r, g, b = 0, 0, 0
    pixels = list(strip.getdata())
    for pr, pg, pb in pixels:
        r += pr
        g += pg
        b += pb
    n = len(pixels)
    return "#%02x%02x%02x" % (r // n, g // n, b // n)


# ═══════════════════════════════════════════════════════════════════
# 🎨 MAIN APP
# ═══════════════════════════════════════════════════════════════════
header_col1, header_col2 = st.columns([5, 1])
with header_col1:
    st.title("📕 KDPEasy Cover Builder")
with header_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔒 Logout", width="stretch"):
        st.session_state["password_correct"] = False
        st.rerun()

st.markdown(
    f"<p style='color:#64748b;font-size:1.05rem;'>"
    f"Upload your front and back cover art, enter your page count, and get a "
    f"print-ready full-wrap cover PDF sized exactly to KDP's spec — bleed and "
    f"barcode-safe zone included.<br>"
    f"<span style='color:#4f46e5;font-weight:600;'>✨ Exclusive tool by {BRAND_NAME}</span>"
    f"</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("🖼️ Upload your cover art")
    front_file = st.file_uploader(
        "Front cover image", type=["png", "jpg", "jpeg"], key="front_upl"
    )
    back_file = st.file_uploader(
        "Back cover image", type=["png", "jpg", "jpeg"], key="back_upl"
    )
    st.caption(
        "Tip: use square-ish or portrait images close to your trim size's aspect "
        "ratio — the tool crops to fill each panel exactly, like a photo frame."
    )

with col_right:
    st.subheader("⚙️ Book settings")
    size_label = st.selectbox("Trim size", options=list(BOOK_SIZES.keys()), index=0)
    trim_w, trim_h = BOOK_SIZES[size_label]

    page_count = st.number_input(
        "Interior page count", min_value=MIN_PAGES, value=100, step=2,
        help="KDP requires a minimum of 24 pages for a paperback.",
    )

    paper_label = st.selectbox("Interior paper color", options=list(PAPER_TYPES.keys()))
    spine_factor = PAPER_TYPES[paper_label]

    spine_w_in, panel_w_in, full_w_in, full_h_in = calc_dimensions(
        trim_w, trim_h, page_count, spine_factor
    )

    st.markdown(
        f"<div class='info-card'>"
        f"<b>Spine width:</b> {spine_w_in:.3f} in<br>"
        f"<b>Full wrap size:</b> {full_w_in:.3f} × {full_h_in:.3f} in "
        f"(includes {BLEED_IN}in bleed on all outer edges)"
        f"</div>",
        unsafe_allow_html=True,
    )

    default_spine_color = "#2d2d2d"
    if front_file is not None:
        try:
            _front_preview = Image.open(front_file)
            default_spine_color = sample_edge_color(
                _front_preview, round(panel_w_in * DPI), round(full_h_in * DPI)
            )
            front_file.seek(0)
        except Exception:
            pass

    spine_color = st.color_picker(
        "Spine color", value=default_spine_color,
        help="Auto-suggested from your front cover's edge — feel free to change it.",
    )

st.markdown("---")
st.subheader("✏️ Add Title Text (Optional)")
add_text = st.checkbox(
    "Add title / subtitle / author text to the front cover",
    value=False,
    help="Turn this OFF if your uploaded front cover image already has text on it — "
         "otherwise the text will overlap.",
)

title_text = subtitle_text = author_text = ""
font_label = list(FONTS.keys())[0]
title_size_pt, subtitle_size_pt, author_size_pt = 60, 26, 22
title_color = subtitle_color = author_color = "#ffffff"

if add_text:
    font_label = st.selectbox("Font style (used for title, subtitle, and author)", options=list(FONTS.keys()))

    st.markdown("**Title**")
    t_text, t_size, t_color = st.columns([2, 1, 1])
    with t_text:
        title_text = st.text_input("Book title", placeholder="e.g. Hazel's Garden Friends", label_visibility="collapsed")
    with t_size:
        title_size_pt = st.number_input("Size (pt)", min_value=20, max_value=150, value=60, step=2, key="title_size")
    with t_color:
        title_color = st.color_picker("Color", value="#ffffff", key="title_color")

    st.markdown("**Subtitle (optional)**")
    s_text, s_size, s_color = st.columns([2, 1, 1])
    with s_text:
        subtitle_text = st.text_input("Subtitle", placeholder="e.g. A Cozy Coloring Book", label_visibility="collapsed")
    with s_size:
        subtitle_size_pt = st.number_input("Size (pt)", min_value=12, max_value=100, value=26, step=2, key="subtitle_size")
    with s_color:
        subtitle_color = st.color_picker("Color", value="#ffffff", key="subtitle_color")

    st.markdown("**Author name (optional)**")
    a_text, a_size, a_color = st.columns([2, 1, 1])
    with a_text:
        author_text = st.text_input("Author name", placeholder="e.g. Jane Doe", label_visibility="collapsed")
    with a_size:
        author_size_pt = st.number_input("Size (pt)", min_value=12, max_value=100, value=22, step=2, key="author_size")
    with a_color:
        author_color = st.color_picker("Color", value="#ffffff", key="author_color")

if not front_file or not back_file:
    st.markdown(
        "<div class='info-card'>"
        "<b>How it works</b><br>"
        "1. Upload your front cover art and back cover art (from Canva, your own AI tool, etc.)<br>"
        "2. Enter your page count and paper color — the spine width updates automatically<br>"
        "3. Pick a spine color (or use the auto-suggested one)<br>"
        "4. Preview, then download your print-ready full-wrap PDF"
        "</div>",
        unsafe_allow_html=True,
    )
else:
    front_img = Image.open(front_file)
    back_img = Image.open(back_file)

    if st.button("🔍 Preview Cover", width="stretch"):
        with st.spinner("Building your cover..."):
            canvas, full_w_px, full_h_px, spine_w_px, panel_w_px = build_cover(
                front_img, back_img, trim_w, trim_h, page_count, spine_factor, spine_color
            )
            if add_text:
                font_file, font_variation = FONTS[font_label]
                add_cover_text(
                    canvas, panel_w_px, full_h_px, full_w_px, font_file, font_variation,
                    title_text, title_size_pt, title_color,
                    subtitle_text, subtitle_size_pt, subtitle_color,
                    author_text, author_size_pt, author_color,
                )
            preview_img = add_preview_guides(canvas, panel_w_px, full_h_px)

        st.session_state["cover_result"] = {
            "canvas": canvas,
            "preview": preview_img,
            "full_w_in": full_w_in,
            "full_h_in": full_h_in,
        }

if "cover_result" in st.session_state:
    st.markdown("---")
    st.subheader("👀 Preview")
    result = st.session_state["cover_result"]
    st.image(result["preview"], width="stretch")
    st.markdown(
        "<div class='warn-card'>"
        "🔵 <b>Blue dashed line</b> = the trim line. Everything OUTSIDE this line is "
        "bleed — it gets physically cut off when your book is printed.<br>"
        "🟡 <b>Yellow dashed line</b> = safe zone. Keep titles, text, and important art "
        "inside this line so nothing looks accidentally cropped, even if the printer's "
        "cutter is slightly off.<br>"
        "🔴 <b>Red dashed box</b> = approximate barcode safe zone. KDP stamps the real "
        "ISBN barcode there automatically after you publish — keep that corner of your "
        "back cover free of important text or images.<br>"
        "All three guides are for preview only and will NOT appear in your downloaded "
        "file. Always confirm the final placement in KDP's own cover previewer before "
        "publishing."
        "</div>",
        unsafe_allow_html=True,
    )

    buf = io.BytesIO()
    result["canvas"].save(buf, format="PDF", resolution=float(DPI))
    buf.seek(0)

    st.download_button(
        "⬇️ Download Print-Ready Cover PDF",
        data=buf,
        file_name="kdp_full_wrap_cover.pdf",
        mime="application/pdf",
        width="stretch",
    )

st.markdown("---")
st.markdown(
    f"<p style='text-align:center;color:#94a3b8;font-size:0.85rem;'>"
    f"✨ Exclusive tool by <b>{BRAND_NAME}</b> • Made for self-publishers"
    f"</p>",
    unsafe_allow_html=True,
)
