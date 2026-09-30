#!/usr/bin/env python3
"""Dumortierite Drill — neon shaft-drill arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/DUMORTIERITE_DRILL_ElbowOS.mp4")
TITLE, HANDLE = "DUMORTIERITE DRILL", "x.com/ElbowOS"

INK = (6, 8, 28)
NAVY = (14, 22, 64)
DENIM = (36, 62, 148)
VIO = (148, 92, 255)
GOLD = (255, 196, 64)
CYAN = (72, 230, 255)
MAG = (255, 64, 168)
LILAC = (210, 170, 255)
FOG = (200, 214, 255)
WHITE = (248, 246, 255)
ROSE = (255, 110, 140)

LEFT, RIGHT = 90, W - 90
DRILL_Y = 1380


class Seg:
    __slots__ = ("y", "gap", "gw", "vx", "kind", "orb")

    def __init__(self, y):
        self.y = y
        self.gw = random.randint(210, 310)
        self.gap = random.uniform(LEFT + self.gw, RIGHT - self.gw)
        self.vx = random.choice((-1, 1)) * random.uniform(70, 150)
        self.kind = "fracture" if random.random() < 0.18 else "vein"
        self.orb = random.random() < 0.62


class Game:
    def __init__(self, record=False):
        self.record = record
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY and not record else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            self.screen = pygame.Surface((W, H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("dejavusans", 48, bold=True)
        self.font_md = pygame.font.SysFont("dejavusans", 34, bold=True)
        self.font_sm = pygame.font.SysFont("dejavusans", 26)
        self.reset()

    def reset(self):
        self.score = 0
        self.t = 0.0
        self.x = W / 2
        self.vx = 0.0
        self.spin = 0.0
        self.depth = 0.0
        self.speed = 240.0
        self.streak = 0
        self.hit_flash = 0.0
        self.segs = []
        self.sparks = []
        self.dust = [{"x": random.uniform(0, W), "y": random.uniform(0, H),
                      "s": random.uniform(1.2, 3.4), "v": random.uniform(20, 70)}
                     for _ in range(70)]
        y = 200
        while y < H + 400:
            self.segs.append(Seg(y))
            y += random.randint(170, 230)

    def burst(self, x, y, col, n=14):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            sp = random.uniform(80, 340)
            self.sparks.append({"x": x, "y": y, "vx": math.cos(a) * sp,
                                "vy": math.sin(a) * sp, "life": random.uniform(0.25, 0.7),
                                "col": col})

    def autoplay(self):
        ahead = [s for s in self.segs if DRILL_Y - 40 < s.y < DRILL_Y + 520]
        target = W / 2
        if ahead:
            s0 = min(ahead, key=lambda s: s.y)
            target = s0.gap
            if s0.kind == "fracture":
                target = s0.gap + (90 if self.x >= s0.gap else -90)
        err = target - self.x
        self.vx = max(-520, min(520, err * 4.2))

    def handle(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key == pygame.K_r:
            self.reset()

    def update(self, dt):
        self.t += dt
        self.hit_flash = max(0.0, self.hit_flash - dt)
        keys = pygame.key.get_pressed() if not self.record else None
        if self.record:
            self.autoplay()
        else:
            ax = 0.0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                ax -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                ax += 1
            self.vx += ax * 1800 * dt
            self.vx *= 0.86
        self.x = max(LEFT + 36, min(RIGHT - 36, self.x + self.vx * dt))
        self.spin += (8 + abs(self.vx) * 0.01) * dt
        self.speed = 240 + min(180, self.depth * 0.04)
        dy = self.speed * dt
        self.depth += dy * 0.12
        self.score += int(dy * 0.18)
        for s in self.segs:
            s.y -= dy
            s.gap += s.vx * dt
            if s.gap < LEFT + s.gw * 0.55 or s.gap > RIGHT - s.gw * 0.55:
                s.vx *= -1
                s.gap = max(LEFT + s.gw * 0.55, min(RIGHT - s.gw * 0.55, s.gap))
        self.segs = [s for s in self.segs if s.y > -80]
        while self.segs and self.segs[-1].y < H + 280:
            self.segs.append(Seg(self.segs[-1].y + random.randint(170, 230)))
        for s in self.segs:
            if abs(s.y - DRILL_Y) < 28:
                half = s.gw * 0.5
                inside = abs(self.x - s.gap) < half - 18
                if s.kind == "fracture" and abs(self.x - s.gap) < half * 0.55:
                    self.hit_flash = 0.35
                    self.streak = 0
                    self.score = max(0, self.score - 40)
                    self.burst(self.x, DRILL_Y, MAG, 16)
                    s.y = -200
                elif inside:
                    if s.orb:
                        self.score += 80 + self.streak * 6
                        self.streak += 1
                        self.burst(s.gap, s.y, GOLD if s.kind == "vein" else CYAN, 18)
                        s.orb = False
                else:
                    self.hit_flash = 0.28
                    self.streak = 0
                    self.burst(self.x, DRILL_Y, ROSE, 10)
        for d in self.dust:
            d["y"] -= (d["v"] + self.speed * 0.25) * dt
            if d["y"] < -8:
                d["y"] = H + 8
                d["x"] = random.uniform(0, W)
        for sp in self.sparks:
            sp["x"] += sp["vx"] * dt
            sp["y"] += sp["vy"] * dt
            sp["life"] -= dt
        self.sparks = [sp for sp in self.sparks if sp["life"] > 0]

    def draw(self, s):
        s.fill(INK)
        pulse = 0.5 + 0.5 * math.sin(self.t * 2.1)
        for d in self.dust:
            pygame.draw.circle(s, DENIM, (int(d["x"]), int(d["y"])), int(d["s"]))
        pygame.draw.rect(s, NAVY, (0, 0, LEFT, H))
        pygame.draw.rect(s, NAVY, (RIGHT, 0, W - RIGHT, H))
        for i in range(14):
            y = int((i * 160 - self.depth * 3) % (H + 40)) - 20
            pygame.draw.line(s, DENIM, (0, y), (LEFT, y), 3)
            pygame.draw.line(s, DENIM, (RIGHT, y), (W, y), 3)
        pygame.draw.line(s, VIO, (LEFT, 0), (LEFT, H), 5)
        pygame.draw.line(s, VIO, (RIGHT, 0), (RIGHT, H), 5)
        pygame.draw.line(s, GOLD, (LEFT + 8, 0), (LEFT + 8, H), 2)
        pygame.draw.line(s, GOLD, (RIGHT - 8, 0), (RIGHT - 8, H), 2)
        for seg in self.segs:
            y = int(seg.y)
            col = MAG if seg.kind == "fracture" else VIO
            half = seg.gw * 0.5
            pygame.draw.line(s, col, (LEFT + 6, y), (int(seg.gap - half), y), 10)
            pygame.draw.line(s, col, (int(seg.gap + half), y), (RIGHT - 6, y), 10)
            glow = GOLD if seg.kind == "vein" else ROSE
            pygame.draw.circle(s, glow, (int(seg.gap - half), y), 8)
            pygame.draw.circle(s, glow, (int(seg.gap + half), y), 8)
            if seg.orb:
                r = 14 + int(4 * math.sin(self.t * 8 + seg.y * 0.02))
                pygame.draw.circle(s, CYAN if seg.kind == "vein" else MAG, (int(seg.gap), y), r)
                pygame.draw.circle(s, WHITE, (int(seg.gap), y), max(4, r // 3))
        cx, cy = int(self.x), DRILL_Y
        flash = MAG if self.hit_flash > 0 else GOLD
        for i in range(5):
            a = self.spin + i * (math.pi * 2 / 5)
            px = cx + int(math.cos(a) * 46)
            py = cy + int(math.sin(a) * 18)
            pygame.draw.polygon(s, flash, [(cx, cy - 8), (px, py), (cx, cy + 22)])
        pygame.draw.circle(s, WHITE, (cx, cy), 18)
        pygame.draw.circle(s, CYAN, (cx, cy), 10)
        pygame.draw.circle(s, flash, (cx, cy + 36), 16)
        pygame.draw.rect(s, DENIM, (cx - 8, cy + 36, 16, 90), border_radius=8)
        for sp in self.sparks:
            pygame.draw.circle(s, sp["col"], (int(sp["x"]), int(sp["y"])), max(2, int(sp["life"] * 10)))
        if self.hit_flash > 0:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 40, 90, int(70 * self.hit_flash / 0.35)))
            s.blit(veil, (0, 0))
        title = self.font_lg.render(TITLE, True, LILAC)
        s.blit(title, title.get_rect(center=(W // 2, 62)))
        handle = self.font_sm.render(HANDLE, True, CYAN)
        s.blit(handle, handle.get_rect(center=(W // 2, 114)))
        meta = self.font_md.render(f"SCORE  {self.score}    STREAK  {self.streak}    DEPTH  {int(self.depth)}", True, FOG)
        s.blit(meta, meta.get_rect(center=(W // 2, 172)))
        hint = self.font_sm.render("A / D  steer the bit    R  reset", True, GOLD)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 48)))
        rim = int(10 + 6 * pulse)
        pygame.draw.rect(s, VIO, (18, 18, W - 36, H - 36), rim, border_radius=28)

    def play(self):
        run = True
        while run:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    run = False
                self.handle(ev)
            self.update(dt)
            self.draw(self.screen)
            pygame.display.flip()
        pygame.quit()

    def record_mp4(self, path):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = SECS * FPS
        surf = self.screen
        for _ in range(frames):
            self.update(1.0 / FPS)
            self.draw(surf)
            proc.stdin.write(pygame.image.tostring(surf, "RGB"))
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "ignore")
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", path)
        pygame.quit()


def main():
    g = Game(record=RECORD)
    if PLAY and not RECORD:
        g.play()
    else:
        g.record_mp4(OUT)


if __name__ == "__main__":
    main()
