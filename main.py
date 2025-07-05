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
    if request.method == "POST":
        try:
            hold    = int(request.form.get("hold", 0))
            box_cap = int(request.form.get("box_cap", 1450))
            levels  = int(request.form.get("levels", 5))

            # 玉数計算（段ごとの偏り対処）
            per_lvl = box_cap // levels
            extra   = box_cap % levels
            one_box = (levels - 1) * per_lvl + (per_lvl + extra)

            # 計算処理：何箱何段までか
            rows = []
            remain = hold
            idx = 0
            while remain >= one_box:
                idx += 1
                remain -= one_box
                rows.append({
                    "clip": f"{idx}箱",
                    "desc": f"{one_box * idx:,}玉",
                    "calc": ""
                })

            if remain > 0:
                dan = (remain // per_lvl) + (1 if remain % per_lvl else 0)
                total = idx + (dan / levels)
                rows.append({
                    "clip": f"{idx}箱{dan}段",
                    "desc": f"{hold:,}玉 → {total:.2f}箱",
                    "calc": f"1箱{levels}段 = {one_box:,}玉"
                })

            return jsonify(rows)

        except Exception as e:
            return jsonify({"error": str(e)}), 400

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
