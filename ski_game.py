"""ASCIIスキー：リアルタイム入力とスクロールを学ぶ教材。Windows端末用。"""
import os
import random
import shutil
import sys
import time

WIDTH = 29
HEIGHT = 16
START_INTERVAL = 0.32
MIN_INTERVAL = 0.085


def get_key():
    """Windowsの非ブロッキングキー入力。通常のターミナルで動作させる。"""
    import msvcrt
    if not msvcrt.kbhit():
        return None
    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        special = msvcrt.getwch()
        return "left" if special == "K" else "right" if special == "M" else None
    return key.lower()


def start_game(best_score=0):
    return {"player_x": WIDTH // 2, "direction": 1, "distance": 0,
            "speed": START_INTERVAL, "alive": True, "running": False,
            "field": [" " * WIDTH for _ in range(HEIGHT)], "score": 0,
            "best_score": best_score, "game_over_reason": "",
            "shield": False}


def make_row(distance):
    """障害物のある新しい行を作る。A=木、*=崖。"""
    row = [" "] * WIDTH
    chance = min(0.36, 0.10 + distance / 800)
    if random.random() < chance:
        row[random.randrange(WIDTH)] = random.choice(("A", "A", "*"))
    if random.random() < chance / 3:
        pos = random.randrange(WIDTH)
        if row[pos] == " ":
            row[pos] = "A"
        if random.random() < 0.08:
            empty_cells = [i for i, tile in enumerate(row) if tile == " "]
            row[random.choice(empty_cells)] = "S"
    return "".join(row)


def update_game(game):
    if not game["running"] or not game["alive"]:
        return
    # プレイヤーは左右どちらかへ滑り続ける。方向を切り替えて回避する。
    nx = game["player_x"] + game["direction"]
    if nx < 0 or nx >= WIDTH:
        game["alive"] = False
        game["game_over_reason"] = "コースの外に出ました"
        return
    game["player_x"] = nx
    game["field"].pop()
    game["field"].insert(0, make_row(game["distance"]))
    game["distance"] += 1
    game["score"] = game["distance"] * 10
    game["best_score"] = max(game["best_score"], game["score"])
    game["speed"] = max(MIN_INTERVAL, START_INTERVAL - game["distance"] * 0.0005)
    tile = game["field"][HEIGHT - 1][game["player_x"]]
    if tile == "S":
        game["shield"] = True
    elif tile == "A" and game["shield"]:
        game["shield"] = False
    elif tile != " ":
        game["alive"] = False
        game["game_over_reason"] = (
            "木にぶつかりました" if tile == "A" else "崖に落ちました"
        )


def draw_game(game):
    columns, rows = shutil.get_terminal_size()
    shield_status = "ON" if game["shield"] else "OFF"
    lines = [f"=== ASCII SKI ===  Shield: {shield_status}"]

    for y, row in enumerate(game["field"]):
        line = list(row)
        if y == HEIGHT - 1:
            if not game["alive"]:
                player = "X"
            elif game["shield"]:
                player = "Q"
            else:
                player = "O"
            line[game["player_x"]] = player
        lines.append("|" + "".join(line) + "|")

    lines.append("+" + "-" * WIDTH + "+")
    lines.append(
        f"距離 {game['distance']}  得点 {game['score']}  "
        f"最高得点 {game['best_score']}  速度 {1/game['speed']:.1f}行/秒"
    )

    if not game["alive"]:
        status = f"ゲームオーバー：{game['game_over_reason']} [R]でリスタート"
    elif game["running"]:
        status = "滑走中"
    elif game["distance"] > 0:
        status = "一時停止中 [Space]で再開"
    else:
        status = "[Space]でスタート"

    lines.append(status)
    lines.append("← →: 方向変更  Space: 開始/停止  R: リスタート  Q: 終了")

    if columns < 60 or rows < len(lines):
        lines = ["ターミナルを広げてください（横60文字・縦21行以上）"]

    # 指定した行の先頭に書き、右側に残っている古い文字を消す
    for y, line in enumerate(lines, start=1):
        sys.stdout.write(f"\x1b[{y};1H{line}\x1b[K")

    # 最後の行より下に残っている古い表示も消す
    sys.stdout.write("\x1b[J")
    sys.stdout.flush()


def main():
    if os.name != "nt":
        print("この版のスキーゲームはWindowsのVS Codeターミナル用です。")
        return
    # Windows 10/11のVS Code内蔵ターミナルを想定
    os.system("")
    game = start_game()
    sys.stdout.write("\x1b[?1049h\x1b[2J\x1b[?7l\x1b[?25l")
    try:
        while True:
            key = get_key()
            if key in ("q", "\x1b"):
                break
            if key == "r":
                game = start_game(game["best_score"])
            elif key == " ":
                if game["alive"]:
                    game["running"] = not game["running"]
            elif key in ("left", "a"):
                game["direction"] = -1
            elif key in ("right", "d"):
                game["direction"] = 1
            if game["running"]:
                update_game(game)
            draw_game(game)
            time.sleep(game["speed"] if game["running"] else 0.08)
    finally:
        sys.stdout.write("\x1b[?7h\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
