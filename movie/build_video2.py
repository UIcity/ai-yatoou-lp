# -*- coding: utf-8 -*-
"""
40秒サービス動画 v2 — 完全連続モーション版ビルダー
anim.html を Playwright で 1200フレーム(30fps)撮影 → ニューラルナレーション(+25%)
→ 明るいグルーヴBGM(BPM116)+モーション同期SE → ffmpeg組立
"""
import os, sys, subprocess, shutil, wave, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = r"C:\Users\hmimu\Documents\会社のすべて\ai-yatoou-lp"
BUILD = os.path.join(HERE, "build")
FRAMES = os.path.join(BUILD, "frames")
FPS = 30
DUR = 40.0
SR = 44100
os.makedirs(FRAMES, exist_ok=True)

def ffmpeg_exe():
    p = shutil.which("ffmpeg")
    if p: return p
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

# ================= 1. フレーム描画 =================
def render_frames():
    shutil.copy(os.path.join(REPO, "assets", "uicity-logo.svg"), os.path.join(HERE, "uicity-logo.svg"))
    from playwright.sync_api import sync_playwright
    n = int(DUR * FPS)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        pg.goto("file:///" + os.path.join(HERE, "anim.html").replace("\\", "/"))
        pg.wait_for_function("window.SEEK_READY === true")
        pg.evaluate("document.fonts.ready.then(()=>window.__f=1)")
        pg.wait_for_function("window.__f === 1", timeout=30000)
        pg.wait_for_timeout(800)
        for i in range(n):
            t = i / FPS
            try:
                pg.evaluate("seek(%.4f)" % t)
            except Exception as ex:
                print("JS ERROR at t=%.2f: %s" % (t, str(ex)[:500])); b.close(); sys.exit(2)
            pg.screenshot(path=os.path.join(FRAMES, "f%04d.jpg" % i), type="jpeg", quality=92)
            if i % 150 == 0: print("frame %d/%d" % (i, n), flush=True)
        b.close()
    cnt = len([f for f in os.listdir(FRAMES) if f.endswith(".jpg")])
    if cnt < n:
        print("ERROR: frames incomplete %d/%d" % (cnt, n)); sys.exit(2)
    print("frames done:", cnt)

# ================= 2. ナレーション(ニューラル・軽快) =================
NARR = [
    ("n1",  "経営者の、みなさん。こんな悩みは、ありませんか。",             0.9,  4.2),
    ("n2a", "AIを、何に使えばいいか、分からない。",                        5.35, 2.45),
    ("n2b", "契約したのに、使われていない。",                              7.85, 2.3),
    ("n2c", "かえって、仕事が増えないか、不安。",                          10.3, 2.45),
    ("n3",  "大切なのは、任せる仕事を、決めることです。",                   13.8, 4.6),
    ("n4",  "AI社員採用設計は、御社の仕事を分析し、専用のAI社員を設計します。", 19.4, 6.6),
    ("n5",  "雇わない方がよければ、そうお伝えします。",                    28.35, 3.0),
    ("n6",  "審査制、無料です。",                                        32.0, 2.2),
    ("n7",  "AIを、雇おう。",                                            35.6, 2.2),
]
VOICE = "ja-JP-NanamiNeural"

def tts_line(text, out_wav, rate_pct):
    import asyncio, edge_tts
    mp3 = out_wav.replace(".wav", ".mp3")
    rate = ("+%d%%" % rate_pct) if rate_pct >= 0 else ("%d%%" % rate_pct)
    async def _run():
        await edge_tts.Communicate(text, VOICE, rate=rate, pitch="-2Hz").save(mp3)
    asyncio.run(_run())
    ff = ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", mp3, "-ar", str(SR), "-ac", "1", out_wav],
                   capture_output=True, text=True, timeout=60)
    with wave.open(out_wav, "rb") as w:
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    idx = np.where(np.abs(d) > 10 ** (-45 / 20.0))[0]
    if len(idx):
        a = max(int(idx[0] - 0.06 * SR), 0); b = min(int(idx[-1] + 0.06 * SR), len(d))
        d = d[a:b]
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((d * 32767).astype(np.int16).tobytes())

def wav_dur(p):
    with wave.open(p, "rb") as w: return w.getnframes() / float(w.getframerate())

def synth_narration():
    infos = []
    for nid, text, start, mx in NARR:
        out = os.path.join(BUILD, nid + ".wav")
        for r in (20, 27, 34):
            tts_line(text, out, r)
            d = wav_dur(out)
            if d <= mx: break
        print("%s rate=+%d%% dur=%.2fs (max %.1f) %s" % (nid, r, d, mx, "OK" if d <= mx else "OVER"))
        infos.append((out, start, d))
    return infos

def load_mono(p):
    with wave.open(p, "rb") as w:
        sr = w.getframerate(); d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
        if w.getnchannels() > 1: d = d.reshape(-1, w.getnchannels()).mean(axis=1)
    if sr != SR:
        d = np.interp(np.linspace(0, 1, int(len(d) * SR / sr)), np.linspace(0, 1, len(d)), d)
    return d

# ================= 3. BGM(BPM116グルーヴ)+SE =================
BPM = 116.0
BEAT = 60.0 / BPM
NOTE = {"C2":65.41,"G2":98.0,"A2":110.0,"F2":87.31,"C3":130.81,"E3":164.81,"G3":196.0,"A3":220.0,
        "B3":246.94,"C4":261.63,"D4":293.66,"E4":329.63,"F4":349.23,"G4":392.0,"A4":440.0,
        "F3":174.61,"D3":146.83,"E2":82.41,"C5":523.25,"E5":659.26,"G5":783.99}

def env_exp(n, k): return np.exp(-np.arange(n) / SR * k)
def sine(f, n): return np.sin(2 * np.pi * f * np.arange(n) / SR)

def kick(vol=0.5):
    n = int(0.20 * SR); t = np.arange(n) / SR
    f = 110 * np.exp(-t * 26) + 42
    ph = np.cumsum(2 * np.pi * f / SR)
    return np.sin(ph) * env_exp(n, 22) * vol

def hat(vol=0.12):
    n = int(0.05 * SR)
    no = np.random.default_rng(3).standard_normal(n)
    hp = no - np.convolve(no, np.ones(8) / 8, mode="same")
    return hp * env_exp(n, 90) * vol

def snare(vol=0.2):
    n = int(0.13 * SR)
    no = np.random.default_rng(5).standard_normal(n) * env_exp(n, 34)
    return (no * 0.7 + sine(190, n) * env_exp(n, 30) * 0.5) * vol

def bassn(f, vol=0.22):
    n = int(BEAT / 2 * SR * 0.92)
    s = sine(f, n) + 0.28 * sine(f * 2, n) + 0.12 * sine(f * 3, n)
    return s * env_exp(n, 9) * np.minimum(np.arange(n) / (0.004 * SR), 1) * vol

def pluck(f, dur=0.5, vol=0.14):
    n = int(dur * SR)
    s = sine(f, n) + 0.34 * sine(f * 2, n) + 0.12 * sine(f * 3, n)
    return s * env_exp(n, 7.5) * np.minimum(np.arange(n) / (0.004 * SR), 1) * vol

def padc(freqs, dur, vol=0.1, atk=0.4):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs: s += np.sin(2 * np.pi * f * t) + 0.1 * np.sin(2 * np.pi * f * 2 * t)
    env = np.minimum(t / atk, 1) * np.clip((dur - t) / 0.9, 0, 1)
    return s * env * (1 + 0.05 * np.sin(2 * np.pi * 0.5 * t)) * vol / len(freqs)

def blip(f0, f1, dur=0.08, vol=0.14):
    n = int(dur * SR)
    f = np.linspace(f0, f1, n)
    return np.sin(np.cumsum(2 * np.pi * f / SR)) * env_exp(n, 30) * vol

def whooshn(dur=0.5, vol=0.16, seed=9):
    n = int(dur * SR)
    no = np.random.default_rng(seed).standard_normal(n)
    lp = np.convolve(no, np.ones(24) / 24, mode="same")
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return lp * env * vol

def stampse(vol=1.0, seed=7):
    n = int(0.3 * SR); t = np.arange(n) / SR
    no = np.random.default_rng(seed).standard_normal(n)
    lp = np.copy(no)
    for i in range(1, n): lp[i] = lp[i - 1] + 0.13 * (no[i] - lp[i - 1])
    return (lp * 0.5 * env_exp(n, 26) + np.sin(2 * np.pi * 52 * t) * env_exp(n, 15) * 1.0) * vol

def riser(dur=0.9, vol=0.15):
    n = int(dur * SR); t = np.arange(n) / SR
    f = np.linspace(300, 950, n)
    tone = np.sin(np.cumsum(2 * np.pi * f / SR))
    no = np.random.default_rng(11).standard_normal(n) * 0.5
    env = (t / dur) ** 2
    return (tone * 0.5 + no) * env * vol

def place(buf, sig, at):
    i = int(at * SR); j = min(i + len(sig), len(buf))
    if 0 <= i < len(buf): buf[i:j] += sig[:j - i]

def synth_bgm():
    buf = np.zeros(int(DUR * SR))
    WIPE1 = 13.24; WIPE2 = 35.05; STAMP1 = 28.05; STAMP2 = 37.2
    # --- セクションA (0〜13.24) 抑えたAmグルーヴ ---
    barsA = np.arange(0, WIPE1 - 0.6, BEAT * 4)
    place(buf, padc([NOTE["A2"], NOTE["C3"], NOTE["E3"]], 6.6, 0.10, 1.6), 0)
    place(buf, padc([NOTE["F2"], NOTE["A3"], NOTE["C3"]], 6.8, 0.11, 0.8), 6.6)
    for bar in barsA:
        place(buf, kick(0.42), bar)
        place(buf, kick(0.3), bar + BEAT * 2)
        if bar > 3:
            place(buf, snare(0.13), bar + BEAT * 2)
        root = NOTE["A2"] if bar < 6.6 else NOTE["F2"]
        for k in range(8):
            if k % 2 == 0: place(buf, bassn(root, 0.16), bar + k * BEAT / 2)
        if bar > 6.5:
            for k in range(4): place(buf, hat(0.07), bar + k * BEAT + BEAT / 2)
    for i, at in enumerate(np.arange(1.0, 12.0, BEAT * 2)):
        place(buf, pluck([NOTE["A3"], NOTE["C4"], NOTE["E4"]][i % 3], 0.5, 0.07), at)
    # フィル→ワイプ
    for k in range(8):
        place(buf, snare(0.05 + k * 0.03), 12.6 + k * BEAT / 4)
    place(buf, whooshn(0.6, 0.2, 9), 12.85)
    # --- セクションB (13.24〜35.05) 明るいフルグルーヴ C-G-Am-F ---
    prog = [["C2", ["C3","E3","G3"],  ["C4","E4","G4","C5"]],
            ["G2", ["B3","D4","G3"],  ["G4","B3","D4","G5"]],
            ["A2", ["A3","C4","E4"],  ["A4","C4","E4","E5"]],
            ["F2", ["F3","A3","C4"],  ["F4","A4","C4","C5"]]]
    t0 = WIPE1
    barlen = BEAT * 4
    bi = 0
    while t0 < WIPE2 - 0.2:
        root, chord, arp = prog[bi % 4]
        place(buf, padc([NOTE[c] for c in chord], barlen + 0.4, 0.12, 0.25), t0)
        for k in range(4):
            place(buf, kick(0.5), t0 + k * BEAT)
            place(buf, hat(0.1), t0 + k * BEAT + BEAT / 2)
        place(buf, snare(0.16), t0 + BEAT)
        place(buf, snare(0.16), t0 + BEAT * 3)
        for k in range(8):
            place(buf, bassn(NOTE[root], 0.2 if k % 2 == 0 else 0.12), t0 + k * BEAT / 2)
        for k in range(16):
            if k % 2 == 0:
                place(buf, pluck(NOTE[arp[(k // 2) % 4]], 0.28, 0.075), t0 + k * BEAT / 4)
        place(buf, pluck(NOTE[arp[3]], 0.7, 0.06), t0)
        t0 += barlen; bi += 1
    # ライザー→黒ワイプ
    place(buf, riser(0.95, 0.16), 34.15)
    place(buf, whooshn(0.6, 0.2, 13), 34.7)
    # --- セクションC (35.05〜40) ---
    for k in range(4):
        place(buf, kick(0.5), 35.05 + k * BEAT)
        place(buf, hat(0.09), 35.05 + k * BEAT + BEAT / 2)
    # 37.2 の朱印で一瞬ブレイク→最終コード
    place(buf, padc([NOTE["C3"], NOTE["E3"], NOTE["G3"], NOTE["C4"]], 3.0, 0.13, 0.15), 37.45)
    n0 = int(38.8 * SR)
    buf[n0:] *= np.linspace(1, 0, len(buf) - n0)
    # ブレイク(37.15〜37.45 のBGMを絞る)
    a, b = int(37.12 * SR), int(37.45 * SR)
    buf[a:b] *= np.linspace(1, 0.15, b - a)
    buf[:int(0.5 * SR)] *= np.linspace(0.3, 1, int(0.5 * SR))
    return buf

def synth_se():
    buf = np.zeros(int(DUR * SR))
    # ？マーク
    for i, at in enumerate([1.3, 2.2, 3.1]):
        place(buf, blip(500 + i * 80, 760 + i * 80, 0.07, 0.09), at)
    # 吹き出しポップ
    for i, at in enumerate([5.2, 7.7, 10.15]):
        place(buf, blip(420, 700, 0.09, 0.14), at)
    # AI社員くん着地
    place(buf, stampse(0.35, 15), 19.5)
    # カード入場
    place(buf, whooshn(0.4, 0.13, 21), 19.95)
    # ロールフリップ
    for at in (22.6, 24.6):
        place(buf, blip(650, 420, 0.08, 0.1), at)
    # 朱印1
    place(buf, stampse(0.85, 7), 28.02)
    # バッジ+紙吹雪
    place(buf, blip(380, 820, 0.12, 0.18), 31.78)
    sh = np.random.default_rng(19).standard_normal(int(0.5 * SR)) * env_exp(int(0.5 * SR), 14) * 0.08
    place(buf, sh, 31.9)
    # スローガン文字ポップ
    for i in range(5):
        place(buf, blip(500 + i * 90, 640 + i * 90, 0.06, 0.09), 35.45 + i * 0.17)
    # 朱印2(大)
    place(buf, stampse(1.2, 7), 37.17)
    return buf

# ================= 4. ミックス =================
def mix_master(narr_infos):
    bgm = synth_bgm() * 2.2
    se = synth_se() * 1.6
    narr = np.zeros(int(DUR * SR)); duck = np.ones(int(DUR * SR))
    for path, start, d in narr_infos:
        place(narr, load_mono(path) * 1.3, start)
        i, j = int(max(start - 0.12, 0) * SR), int(min(start + d + 0.2, DUR) * SR)
        duck[i:j] = 10 ** (-10 / 20.0)
    k = int(0.05 * SR)
    duck = np.convolve(duck, np.ones(k) / k, mode="same")
    mix = bgm * duck + se + narr
    peak = np.abs(mix).max()
    if peak > 0: mix = mix / peak * (10 ** (-1.2 / 20.0))
    st = np.repeat(mix[:, None], 2, axis=1)
    out = os.path.join(BUILD, "master.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    print("master.wav done")
    return out

# ================= 5. 組立 =================
def assemble(master):
    ff = ffmpeg_exe()
    out = os.path.join(REPO, "movie", "movie_ai_yatoou_40s.mp4")
    cmd = [ff, "-y", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "f%04d.jpg"),
           "-i", master, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", "40.0",
           "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        print("FFMPEG ERR:\n", r.stderr[-2000:]); sys.exit(2)
    probe = subprocess.run([ff, "-i", out], capture_output=True, text=True)
    for ln in probe.stderr.splitlines():
        if "Duration" in ln or "Stream" in ln: print(ln.strip())
    for sec in (2, 6, 9, 11, 15, 21, 28, 32, 36, 38):
        subprocess.run([ff, "-y", "-ss", str(sec), "-i", out, "-frames:v", "1",
                        os.path.join(BUILD, "pv_%02d.png" % sec)], capture_output=True)
    print("done:", out)

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("all", "frames"): render_frames()
    if step in ("all", "audio"):
        infos = synth_narration()
        master = mix_master(infos)
    if step == "video":
        infos = synth_narration()
        master = mix_master(infos)
        assemble(master)
    if step == "all":
        assemble(os.path.join(BUILD, "master.wav"))
    if step == "assemble":
        assemble(os.path.join(BUILD, "master.wav"))
