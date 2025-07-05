# main.py ――― パチンコ計算機 V2 ―――
import os
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, session

app = Flask(__name__)
app.secret_key = "your-secret-key"
app.permanent_session_lifetime = timedelta(days=1)

@app.route("/", methods=["GET", "POST"])
def index():
    if "saved_tama" not in session:
        session["saved_tama"] = {"init": "", "now": "", "used": ""}
    if request.method == "POST":
        if "reset_tama" in request.form:
            session["saved_tama"] = {"init": "", "now": "", "used": ""}
        else:
            init_tama = int(request.form["initial_tama"])
            now_tama  = int(request.form["current_tama"])
            session["saved_tama"] = {
                "init": init_tama,
                "now":  now_tama,
                "used": init_tama - now_tama
            }
        return redirect(url_for("index"))
    return render_template("index.html", data=session["saved_tama"], tab="top")


@app.route("/end", methods=["GET", "POST"])
def end_page():
    if request.method == "POST":
        f = request.form
        name       = f["final_name"]
        start_cash = int(f.get("start_cash", 0))
        used_cash  = int(f.get("used_cash", 0))
        salary_sel = f.get("salary")
        salary     = int(f["custom_salary"]) if salary_sel == "custom" else int(salary_sel)
        expenses   = int(f.get("expenses", 0))
        exchange   = int(f.get("exchange", 0))
        details    = f.get("details", "").strip()
        comments   = f.get("comments", "").strip()

        plus = start_cash + exchange
        minus = used_cash + salary + expenses
        balance = plus - minus
        money_line = f"\n持出現金 {name} #{balance}" if balance >= 0 else f"\n持込現金 {name} #{abs(balance)}"

        result = (
            f"■{name} 終了報告\n"
            f"稼働開始前持金：{start_cash}\n"
            f"稼働使用金額：{used_cash}\n\n"
            f"{details}\n"
            f"{money_line}\n\n"
            f"給与：{salary}\n"
            f"経費：{expenses}\n"
            f"景品交換：{exchange}\n"
            f"稼働終了持金：{balance}"
        )
        if comments:
            result += "\n\n" + comments

        return jsonify({"result": result})
    return render_template("end.html", tab="end")


@app.route("/box", methods=["GET", "POST"])
def box_page():
    """
    POST:
      hold     : 持ち玉
      box_cap  : 1箱の総玉数（入力値）
      levels   : 段数（入力値）
    返り値:
      [{clip, desc, calc}, …] 1250 ごとの位置 + 余り行
    """
    if request.method == "POST":
        try:
            hold     = int(request.form.get("hold", 0))
            box_cap  = max(int(request.form.get("box_cap", 1)), 1)
            levels   = max(int(request.form.get("levels", 1)), 1)

            # 1箱内の段構成（この部分は既存ロジックを維持）
            per_lvl  = box_cap // levels
            extra    = box_cap % levels
            last_lvl = per_lvl + extra
            one_box  = box_cap                          # わかりやすく名前を保持

            rows = []
            remaining = hold
            k = 1                                       # 1250 倍数カウンタ

            while True:
                target = 1250 * k                      # 今回消費する玉数
                if remaining < target:                 # もう 1250 消費できない
                    rows.append({
                        "clip": "",
                        "desc": f"余り {remaining} 玉",
                        "calc": ""
                    })
                    break

                remaining_after = remaining - target   # 1250 消費後の残り玉
                # ───────── どの箱・段・余りに到達するか ─────────
                boxes = remaining_after // one_box
                pos   = remaining_after % one_box      # 箱内位置

                if pos == 0:                           # 箱境界ジャスト
                    desc = f"{boxes}箱 0段 余り0玉"
                else:
                    if pos <= per_lvl * (levels - 1):  # 上段側
                        level = (pos + per_lvl - 1) // per_lvl
                        rest  = pos - per_lvl * (level - 1)
                    else:                              # 最下段
                        level = levels
                        rest  = pos - per_lvl * (levels - 1)
                    desc = f"{boxes}箱 {level}段 余り{rest}玉"
                # ────────────────────────────────────────

                rows.append({
                    "clip": f"{target}#",
                    "desc": desc,
                    "calc": ""                         # 計算式は不要なら空で
                })
                remaining = remaining_after
                k += 1

            return jsonify(rows)

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # GET
    return render_template("box.html", tab="box")


@app.route("/spin", methods=["GET", "POST"])
def spin_page():
    if request.method == "POST":
        base = int(request.form.get("base", 0))
        now  = int(request.form.get("now", 0))
        diff = now - base
        return jsonify({"diff": diff})
    return render_template("spin.html", tab="spin")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
