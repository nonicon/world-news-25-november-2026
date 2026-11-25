# World News in One Image - 25 November 2026
#
# Draws a newspaper front page summing up the world news of Wednesday
# 25 November 2026, using only the Python standard library. A small
# framebuffer class paints every pixel; a 5x7 bitmap font stored as
# integer bit-rows renders the text; a hand-rolled PNG writer (zlib +
# CRC chunks, no external code) saves the finished page.
#
# Nothing is read from disk and nothing touches the network, so two
# runs always write identical bytes.
#
# The six stories were checked against news reported on 25 November 2026:
#   1. Zelenskiy confirms Ukraine hit a Russian cargo ship in the Gulf of
#      Finland and sank a Russian warship off Benghazi, Libya.
#   2. Houthi drone hits Riyadh's PIF Tower, the tallest tower in the
#      Saudi capital, for the second time in a week; 11 people wounded.
#   3. French judges order ex-president Sarkozy and his wife Carla Bruni
#      to trial over witness tampering in the Libya funding case.
#   4. NATO plans early-warning aircraft over Poland after missiles
#      landed there during an attack on Ukraine.
#   5. Iran says three oil tankers were hit by naval mines in the
#      Strait of Hormuz.
#   6. Real Madrid beat PSV 5-1 (Bellingham, Mbappe brace); England
#      level the T20 series in Australia.
# Ticker: Nvidia up 31.5% as Huang returns as CEO; Trump pardons the
# Thanksgiving turkeys; Iraq orders Kurdish oilfields seized; Senegal
# get their AFCON title back; Indonesia VP successor names due today.

import math
import os
import struct
import zlib

W = 1024
H = 1024

# --- palette ------------------------------------------------------------
PAPER = (247, 244, 235)
WHITE = (255, 255, 255)
INK = (20, 22, 28)
NAVY = (13, 27, 62)
NAVY_SOFT = (28, 48, 96)
GOLD = (198, 154, 42)
GOLD_SOFT = (232, 205, 120)
RED = (176, 32, 32)
BLUE = (24, 84, 160)
TEAL = (14, 110, 95)
ORANGE = (206, 92, 20)
GREEN = (34, 110, 60)
PURPLE = (96, 56, 140)
GREY = (120, 118, 112)
LIGHT_GREY = (222, 218, 208)
SKY = (168, 205, 235)
SEA = (36, 98, 150)

# --- 5x7 bitmap font ----------------------------------------------------
# One glyph = seven rows, each row an integer whose five bits are the
# pixels left to right (bit 4 = leftmost pixel). Only the characters
# the page needs are defined; anything else renders as a blank.
def _g(*rows):
    return rows

GLYPHS = {
    'A': _g(0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'B': _g(0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    'C': _g(0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    'D': _g(0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    'E': _g(0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    'F': _g(0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    'G': _g(0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    'H': _g(0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'I': _g(0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'J': _g(0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    'K': _g(0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    'L': _g(0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    'M': _g(0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    'N': _g(0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    'O': _g(0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'P': _g(0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    'Q': _g(0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    'R': _g(0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    'S': _g(0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    'T': _g(0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    'U': _g(0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'V': _g(0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'W': _g(0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    'X': _g(0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    'Y': _g(0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    'Z': _g(0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    '0': _g(0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    '1': _g(0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    '2': _g(0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    '3': _g(0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    '4': _g(0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    '5': _g(0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    '6': _g(0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    '7': _g(0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    '8': _g(0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    '9': _g(0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    ' ': _g(0, 0, 0, 0, 0, 0, 0),
    '.': _g(0, 0, 0, 0, 0, 0b01100, 0b01100),
    ',': _g(0, 0, 0, 0, 0b01100, 0b00100, 0b01000),
    ':': _g(0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    ';': _g(0, 0b01100, 0b01100, 0, 0b01100, 0b00100, 0b01000),
    "'": _g(0b00100, 0b00100, 0b01000, 0, 0, 0, 0),
    '-': _g(0, 0, 0, 0b01110, 0, 0, 0),
    '!': _g(0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0, 0b00100),
    '?': _g(0b01110, 0b10001, 0b00001, 0b00110, 0b00100, 0, 0b00100),
    '(': _g(0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ')': _g(0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    '/': _g(0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    '%': _g(0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    '&': _g(0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    '+': _g(0, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0),
    '=': _g(0, 0, 0b11111, 0, 0b11111, 0, 0),
    '"': _g(0b01010, 0b01010, 0, 0, 0, 0, 0),
    '*': _g(0, 0b10101, 0b01110, 0b10101, 0, 0, 0),
}

# --- framebuffer ---------------------------------------------------------
class Page:
    """An RGB canvas backed by one flat bytearray."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill(bg)

    def fill(self, color):
        r, g, b = color
        self.buf[:] = bytes((r, g, b)) * (self.w * self.h)

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = color
        row = bytes((r, g, b)) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, length, color, thick=1):
        self.rect(x, y, length, thick, color)

    def vline(self, x, y, length, color, thick=1):
        self.rect(x, y, thick, length, color)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line, inclusive of both ends."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.px(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r - 1, cy + r + 2):
            for xx in range(cx - r - 1, cx + r + 2):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - thick < d <= r:
                    self.px(xx, yy, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        """Filled triangle via scanline fill between its edges."""
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        def edge_x(p, q, y):
            if q[1] == p[1]:
                return float(p[0])
            return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])
        for y in range(ay, cy + 1):
            if y < by:
                xa, xb = edge_x((ax, ay), (bx, by), y), edge_x((ax, ay), (cx, cy), y)
            else:
                xa, xb = edge_x((bx, by), (cx, cy), y), edge_x((ax, ay), (cx, cy), y)
            if xa > xb:
                xa, xb = xb, xa
            self.rect(int(xa), y, int(xb) - int(xa) + 1, 1, color)

    # -- text -------------------------------------------------------------
    def glyph_w(self, scale):
        return 6 * scale

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, s, x, y, scale, color):
        """Draw uppercase-friendly text; unknown glyphs become blanks."""
        cx = x
        for ch in s:
            rows = GLYPHS.get(ch, GLYPHS.get(ch.upper(), (0,) * 7))
            for ry, bits in enumerate(rows):
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + ry * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, s, cx, y, scale, color):
        self.text(s, cx - self.text_w(s, scale) // 2, y, scale, color)

    def wrap(self, s, max_w, scale):
        """Greedy word wrap into lines that fit max_w pixels."""
        words = s.split(' ')
        lines = []
        cur = ''
        for word in words:
            trial = word if not cur else cur + ' ' + word
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# --- PNG writer ----------------------------------------------------------
def _chunk(kind, data):
    out = struct.pack('>I', len(data)) + kind + data
    out += struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def save_png(page, path):
    raw = bytearray()
    stride = page.w * 3
    for y in range(page.h):
        raw.append(0)  # filter: none
        raw += page.buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack('>IIBBBBB', page.w, page.h, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n'
    png += _chunk(b'IHDR', ihdr)
    png += _chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += _chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)

# --- pictograms ----------------------------------------------------------
# Each draws a small scene inside a box (x, y, w, h). Simple shapes only:
# rectangles, discs, lines and triangles, in flat colours.

def icon_ship(p, x, y, w, h):
    p.rect(x, y, w, h, SKY)
    p.rect(x, y + h - 26, w, 26, SEA)
    # waves
    for i in range(4):
        wx = x + 6 + i * 26
        p.line(wx, y + h - 14, wx + 12, y + h - 20, WHITE)
        p.line(wx + 12, y + h - 20, wx + 24, y + h - 14, WHITE)
    # hull
    p.rect(x + 14, y + h - 44, w - 28, 16, INK)
    p.triangle(x + 14, y + h - 44, x + 14, y + h - 28, x + 30, y + h - 28, INK)
    p.triangle(x + w - 14, y + h - 44, x + w - 14, y + h - 28,
               x + w - 30, y + h - 28, INK)
    # bridge + mast
    p.rect(x + w // 2 - 4, y + h - 62, 8, 18, WHITE)
    p.vline(x + w // 2, y + h - 78, 18, INK, 2)
    # drone above
    dx, dy = x + w - 34, y + 16
    p.rect(dx - 8, dy - 2, 16, 4, INK)
    p.disc(dx - 10, dy - 2, 3, INK)
    p.disc(dx + 10, dy - 2, 3, INK)
    p.disc(dx, dy + 4, 3, RED)


def icon_tower(p, x, y, w, h):
    p.rect(x, y, w, h, NAVY_SOFT)
    # tapered tower
    top_w = w // 3
    p.triangle(x + w // 2 - top_w // 2, y + 4,
               x + w // 2 + top_w // 2, y + 4,
               x + w // 2 + w // 2 - 6, y + h - 8, GOLD)
    p.triangle(x + w // 2 - top_w // 2, y + 4,
               x + w // 2 + w // 2 - 6, y + h - 8,
               x + w // 2 - w // 2 + 6, y + h - 8, GOLD)
    # windows
    for row in range(4):
        wy = y + 16 + row * 16
        p.rect(x + w // 2 - 8, wy, 16, 5, WHITE)
    # impact burst halfway up
    bx, by = x + w // 2 + w // 4, y + h // 2
    for ang in range(0, 360, 45):
        dx = int(14 * math.cos(math.radians(ang)))
        dy = int(14 * math.sin(math.radians(ang)))
        p.line(bx, by, bx + dx, by + dy, RED, )
        p.line(bx, by, bx + dx, by + dy, (255, 120, 40))
    p.disc(bx, by, 6, RED)
    p.disc(bx, by, 3, (255, 200, 60))


def icon_court(p, x, y, w, h):
    p.rect(x, y, w, h, (232, 226, 214))
    # pediment
    p.triangle(x + 6, y + 22, x + w - 6, y + 22, x + w // 2, y + 4, NAVY)
    p.disc(x + w // 2, y + 14, 4, GOLD)
    # columns
    for i in range(3):
        cx = x + 16 + i * (w - 32) // 2
        p.rect(cx - 4, y + 26, 8, h - 44, NAVY)
    # base
    p.rect(x + 8, y + h - 18, w - 16, 6, NAVY)
    p.rect(x + 4, y + h - 10, w - 8, 4, NAVY)
    # gavel
    p.rect(x + w - 30, y + h - 30, 18, 6, INK)
    p.line(x + w - 21, y + h - 24, x + w - 12, y + h - 12, INK)


def icon_radar(p, x, y, w, h):
    p.rect(x, y, w, h, SKY)
    cx, cy = x + w // 2, y + h - 14
    # dish arc
    p.ring(cx, cy, 34, NAVY, 3)
    p.ring(cx, cy, 22, NAVY, 2)
    p.disc(cx, cy, 4, RED)
    # sweep
    p.line(cx, cy, cx + 26, cy - 22, RED)
    p.line(cx, cy, cx + 30, cy - 8, (255, 120, 40))
    # plane
    px, py = x + w - 26, y + 14
    p.triangle(px, py, px - 16, py + 6, px - 2, py + 6, INK)
    p.triangle(px - 2, py + 6, px - 16, py + 6, px - 8, py + 12, INK)


def icon_tanker(p, x, y, w, h):
    p.rect(x, y, w, h, SKY)
    p.rect(x, y + h - 22, w, 22, SEA)
    # hull
    p.rect(x + 10, y + h - 40, w - 20, 14, ORANGE)
    p.triangle(x + 10, y + h - 40, x + 10, y + h - 26, x + 24, y + h - 26, ORANGE)
    # containers
    p.rect(x + 16, y + h - 56, 16, 16, RED)
    p.rect(x + 34, y + h - 56, 16, 16, TEAL)
    p.rect(x + 52, y + h - 56, 16, 16, BLUE)
    # funnel
    p.rect(x + w - 26, y + h - 58, 10, 18, INK)
    # spiky mine
    mx, my = x + w - 24, y + 18
    for ang in range(0, 360, 30):
        dx = int(11 * math.cos(math.radians(ang)))
        dy = int(11 * math.sin(math.radians(ang)))
        p.line(mx, my, mx + dx, my + dy, INK)
    p.disc(mx, my, 7, INK)
    p.disc(mx - 2, my - 2, 2, GREY)


def icon_ball(p, x, y, w, h):
    p.rect(x, y, w, h, GREEN)
    # pitch lines
    p.rect(x, y + h - 12, w, 2, WHITE)
    p.ring(x + w // 2, y + h // 2 + 6, 26, WHITE, 2)
    # ball
    bx, by = x + w // 2, y + h // 2 + 4
    p.disc(bx, by, 18, WHITE)
    p.disc(bx, by, 6, INK)
    p.line(bx, by - 18, bx, by - 6, INK)
    p.line(bx - 17, by + 6, bx - 6, by + 2, INK)
    p.line(bx + 17, by + 6, bx + 6, by + 2, INK)
    p.line(bx - 11, by + 15, bx - 4, by + 6, INK)
    p.line(bx + 11, by + 15, bx + 4, by + 6, INK)
    # score
    p.text('5-1', x + 6, y + 6, 2, WHITE)


# --- page furniture ------------------------------------------------------
def masthead(p):
    p.rect(0, 0, W, 140, NAVY)
    p.text_center('THE WORLD IN ONE IMAGE', W // 2, 24, 5, WHITE)
    p.text_center('WEDNESDAY 25 NOVEMBER 2026', W // 2, 76, 3, GOLD_SOFT)
    p.hline(0, 132, W, GOLD, 4)
    p.text_center("ONE DAY'S NEWS, FROM EVERY CORNER OF THE GLOBE",
                  W // 2, 108, 2, (200, 205, 220))


def panel(p, x, y, w, h, kicker, kcolor, headline, body, icon):
    p.rect(x, y, w, h, WHITE)
    # kicker tag
    tag_w = p.text_w(kicker, 2) + 16
    p.rect(x + 12, y + 12, tag_w, 24, kcolor)
    p.text(kicker, x + 20, y + 18, 2, WHITE)
    # pictogram top right
    icon(p, x + w - 118, y + 10, 106, 66)
    # headline starts below the pictogram so nothing overlaps it
    hy = y + 84
    for line in p.wrap(headline, w - 24, 3):
        p.text(line, x + 12, hy, 3, INK)
        hy += 26
    # rule
    p.hline(x + 12, hy + 4, w - 24, LIGHT_GREY, 2)
    # body
    by = hy + 14
    for line in p.wrap(body, w - 24, 2):
        p.text(line, x + 12, by, 2, (58, 58, 58))
        by += 19
    # border
    p.rect(x, y, w, 2, INK)
    p.rect(x, y + h - 2, w, 2, INK)
    p.rect(x, y, 2, h, INK)
    p.rect(x + w - 2, y, 2, h, INK)


def ticker(p, y, h):
    p.rect(0, y, W, h, NAVY)
    p.text('ALSO TODAY', 16, y + 12, 2, GOLD_SOFT)
    p.vline(150, y + 10, h - 20, GOLD, 2)
    text = ('NVIDIA +31.5% AS HUANG RETURNS AS CEO * '
            'TRUMP PARDONS TURKEYS FREEDOM AND FEATHERS * IRAQ ORDERS '
            'KURDISH OILFIELDS SEIZED * SENEGAL GET AFCON TITLE BACK * '
            'INDONESIA VP SUCCESSOR NAMES DUE')
    lines = p.wrap(text, W - 190, 2)
    ty = y + 12
    for line in lines[:3]:
        p.text(line, 166, ty, 2, WHITE)
        ty += 19


# --- stories -------------------------------------------------------------
STORIES = [
    ('UKRAINE', BLUE,
     'KYIV CONFIRMS SEA STRIKES ON RUSSIAN SHIPS',
     'Zelenskiy says Ukraine hit a Russian cargo ship in the Gulf of '
     'Finland and sank a warship off Benghazi, Libya. Norway urges caution.',
     icon_ship),
    ('SAUDI ARABIA', RED,
     "DRONE HITS RIYADH'S TALLEST TOWER, 11 HURT",
     'Houthis strike the PIF Tower in Riyadh for the second time in a '
     'week. The Saudi-led coalition vows a decisive response.',
     icon_tower),
    ('FRANCE', PURPLE,
     'SARKOZY AND BRUNI ORDERED TO TRIAL',
     'The ex-president and his wife face trial over alleged witness '
     'tampering in the Libya campaign-funding case. First hearing: '
     '1 April 2027.',
     icon_court),
    ('NATO', TEAL,
     "NATO TO WATCH POLAND'S SKIES",
     'The alliance plans early-warning aircraft over Poland after '
     'missiles landed there during an attack on Ukraine.',
     icon_radar),
    ('ENERGY', ORANGE,
     'THREE TANKERS HIT BY MINES IN HORMUZ',
     'Iran says three oil tankers were struck by naval mines in the '
     'Strait of Hormuz, raising fears for shipping in the Gulf.',
     icon_tanker),
    ('SPORT', GREEN,
     'MADRID HIT PSV FOR FIVE',
     'Bellingham and a Mbappe brace power Real Madrid to a 5-1 win. '
     'England level the T20 series in Australia.',
     icon_ball),
]


def build():
    p = Page(W, H, PAPER)
    masthead(p)
    # 2 columns x 3 rows of story panels
    gx, gy = 16, 152
    gw = (W - 2 * gx - 12) // 2
    gh = 250
    for i, (kicker, kcolor, headline, body, icon) in enumerate(STORIES):
        col = i % 2
        row = i // 2
        panel(p, gx + col * (gw + 12), gy + row * (gh + 12),
              gw, gh, kicker, kcolor, headline, body, icon)
    ticker(p, 938, 86)
    return p


def main():
    outdir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(outdir, exist_ok=True)
    page = build()
    path = os.path.join(outdir, 'entry.png')
    size = save_png(page, path)
    print(f'wrote {path} ({page.w}x{page.h}, {size} bytes)')


if __name__ == '__main__':
    main()
