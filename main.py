# main.py  ――― パチンコ計算機 V2 ―――
import os
from datetime import timedelta
from flask import (
    Flask, render_template, request,
    redirect, url_for, jsonify, session
)

app = Flask(__name__)
app.secret_key = "your-secret-key"
app.permanent_session_lifetime = timedelta(days=1)

# ----------------------------------------
# 1～3. 「貯玉・現金・新1250」計算機ページ
# ----------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    # --- セッションで貯玉データだけ保持 ---
    if "saved_tama" not in session:
        session["saved_tama"] = {"init": "", "now": "", "used": ""}

    # POSTは貯玉計算 or リセットのみ扱う
    if request.method == "POST":
        if "reset_tama" in request.form:
            session["saved_tama"] = {"init": "", "now": "", "used": ""}
        else:
            init_tama = int(request.form["initial_tama"])
            now_tama  = int(request.form["current_tama"])
            session["saved_tama"] = {
                "init": init_tama,
                "now": now_tama,
                "used": init_tama - now_tama
            }
        return redirect(url_for("index"))

    return render_template("index.html",
                           data=session["saved_tama"],
                           tab="top")

# ----------------------------------------
# 4. 終了計算機（/end）
# ----------------------------------------
@app.route("/end", methods=["GET", "POST"])
def end_page():
    if request.method == "POST":
        # 送信フォームを受け取り終了報告を生成
        form = request.form
        name       = form["final_name"]
        start_cash = int(form.get("start_cash", 0))
        used_cash  = int(form.get("used_cash", 0))
        salary_sel = form.get("salary")
        salary     = int(form["custom_salary"]) if salary_sel == "custom" else int(salary_sel)
        expenses   = int(form.get("expenses", 0))
        exchange   = int(form.get("exchange", 0))
        details    = form.get("details", "").strip()
        comments   = form.get("comments", "").strip()

        total_plus  = start_cash + exchange
        total_minus = used_cash + salary + expenses
        balance     = total_plus - total_minus

        # 簡易ロジック：balance が + なら持出、- なら持込の例示
        money_line = ""
        if balance >= 0:
            money_line = f"\n持出現金 {name} #{balance}"
        else:
            money_line = f"\n持込現金 {name} #{abs(balance)}"

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

# ----------------------------------------
# 5. 箱＋回転数 計算機（/box）
# ----------------------------------------
@app.route("/box", methods=["GET", "POST"])
def box_page():
    if request.method == "POST":
        # ===== 入力値取得 =====
        boxes     = int(request.form["boxes"])
        levels    = int(request.form["levels"])
        base_spin = request.form.get("base_spin")  # 空文字可
        now_spin  = request.form.get("now_spin")   # 空文字可

        # ===== 箱1つあたりの玉数計算 =====
        # 例：箱容量1450玉を段数で分割（上段= floor/ 下段=余り）
        BOX_CAP = 1450
        base_per_level = BOX_CAP // levels
        extra          = BOX_CAP % levels
        last_level_cap = base_per_level + extra
        one_box_balls  = (levels - 1) * base_per_level + last_level_cap

        # ===== トータル玉数 =====
        total_balls = boxes * one_box_balls

        # ===== 回転率計算 =====
        spin_diff = None
        rotation_rate = None
        if base_spin and now_spin:
            try:
                base = int(base_spin)
                now  = int(now_spin)
                spin_diff = now - (base or now)  # 0ならそのまま
                rotation_rate = round(spin_diff / total_balls * 250, 2) if total_balls else None
            except ValueError:
                pass  # 無効入力は無視

        return jsonify({
            "total_balls": total_balls,
            "spin_diff": spin_diff,
            "rotation_rate": rotation_rate
        })

    return render_template("box.html", tab="box")

# ----------------------------------------
# アプリ起動
# ----------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
