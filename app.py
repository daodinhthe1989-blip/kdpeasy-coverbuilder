import io
import streamlit as st
from PIL import Image, ImageOps, ImageDraw

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
    "Trắng — White (B&W interior)": 0.002252,
    "Ngà — Cream (B&W interior)": 0.0025,
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
        "ratio — the tool crops
