from flask import Flask, render_template, request, redirect, url_for, session
import math

app = Flask(__name__, template_folder="template")
app.secret_key = "supersecretkey"

# -------------------
# 工具函数
# -------------------
def calculate_rer(weight):
    return 70 * (weight ** 0.75)

def calculate_mer(rer, activity_factor):
    return rer * activity_factor

def convert_lb_to_kg(lb):
    return lb * 0.4536

def estimate_activity_factor(age, neutered, activity_level):
    """
    基于 NRC/WSAVA 建议的 MER 系数
    """
    if age == "puppy":
        return 2.0
    elif age == "senior":
        return 1.2
    elif age == "adult":
        if activity_level == "low":
            return 1.3
        elif activity_level == "normal":
            return 1.6 if neutered == "yes" else 1.8
        elif activity_level == "high":
            return 2.5
        elif activity_level == "working":
            return 4.0
    return 1.6  # fallback 默认值

# -------------------
# Step1
# -------------------
@app.route("/", methods=["GET", "POST"])
def step1():
    if request.method == "POST":
        session["dog_name"] = request.form["dog_name"]
        return redirect(url_for("step2"))
    return render_template("step1.html")

# -------------------
# Step2
# -------------------
@app.route("/step2", methods=["GET", "POST"])
def step2():
    if request.method == "POST":
        session["gender"] = request.form["gender"]
        return redirect(url_for("step3"))
    return render_template("step2.html", dog=session.get("dog_name"))

# -------------------
# Step3
# -------------------
@app.route("/step3", methods=["GET", "POST"])
def step3():
    if request.method == "POST":
        # 年龄
        session["age"] = request.form.get("age")

        # 体重
        weight = float(request.form.get("weight"))
        unit = request.form.get("unit")
        if unit == "lb":
            weight = convert_lb_to_kg(weight)
        session["weight"] = weight

        # 品种
        breed = request.form.get("breed")
        if breed == "Other":
            breed = request.form.get("other_breed")
        session["breed"] = breed

        return redirect(url_for("step4"))
    return render_template("step3.html", dog=session.get("dog_name"))

# -------------------
# Step4
# -------------------
@app.route("/step4", methods=["GET", "POST"])
def step4():
    if request.method == "POST":
        age = session.get("age")
        neutered = request.form.get("neutered")
        activity_level = request.form.get("activity_level")

        af = estimate_activity_factor(age, neutered, activity_level)
        session["activity_factor"] = af
        session["neutered"] = neutered
        session["activity_level"] = activity_level

        return redirect(url_for("step5"))
    return render_template("step4.html", dog=session.get("dog_name"))

# -------------------
# Step5
# -------------------
@app.route("/step5", methods=["GET", "POST"])
def step5():
    if request.method == "POST":
        fresh_ratio = float(request.form.get("fresh_ratio"))
        cycle_days = int(request.form.get("cycle_days"))
        flavor = request.form.get("flavor")

        chicken_ratio = 0.0
        beef_ratio = 0.0
        if flavor == "both":
            chicken_ratio = float(request.form.get("chicken_ratio"))
            beef_ratio = 1 - chicken_ratio
        elif flavor == "chicken":
            chicken_ratio = 1.0
        elif flavor == "beef":
            beef_ratio = 1.0

        session["fresh_ratio"] = fresh_ratio
        session["cycle_days"] = cycle_days
        session["chicken_ratio"] = chicken_ratio
        session["beef_ratio"] = beef_ratio

        return redirect(url_for("result"))

    return render_template("step5.html", dog=session.get("dog_name"))

# -------------------
# Result
# -------------------
@app.route("/result")
def result():
    dog = session.get("dog_name")
    gender = session.get("gender")
    age = session.get("age")
    neutered = session.get("neutered")
    breed = session.get("breed")
    weight = session.get("weight")
    activity_factor = session.get("activity_factor")
    fresh_ratio = session.get("fresh_ratio")
    cycle_days = session.get("cycle_days")
    chicken_ratio = session.get("chicken_ratio")
    beef_ratio = session.get("beef_ratio")

    # 计算
    rer = round(calculate_rer(weight))
    mer = round(calculate_mer(rer, activity_factor))
    fresh_kcal = round(mer * fresh_ratio)

    # ⚡ 正确的能量密度（平均生鲜肉 ≈ 1.5 kcal/g）
    MEAT_KCAL_PER_GRAM = 1.5
    fresh_g = round(fresh_kcal / MEAT_KCAL_PER_GRAM)

    total_g = fresh_g * cycle_days
    pack_size = 454
    total_packs = math.ceil(total_g / pack_size)

    recipes = {}
    if chicken_ratio > 0:
        grams = round(total_g * chicken_ratio)
        recipes["Chicken"] = {
            "grams": grams,
            "packs_1lb": round(grams / pack_size, 1),
            "percent": round(chicken_ratio * 100),
        }
    if beef_ratio > 0:
        grams = round(total_g * beef_ratio)
        recipes["Beef"] = {
            "grams": grams,
            "packs_1lb": round(grams / pack_size, 1),
            "percent": round(beef_ratio * 100),
        }

    return render_template(
        "result.html",
        dog=dog,
        gender=gender,
        age=age,
        neutered=neutered,
        breed=breed,
        weight=round(weight, 1),
        activity_factor=activity_factor,
        rer=rer,
        mer=mer,
        fresh_kcal=fresh_kcal,
        fresh_g=fresh_g,
        cycle_days=cycle_days,
        total_g=total_g,
        recipes=recipes,
        total_packs=total_packs,
    )

if __name__ == "__main__":
    app.run(debug=True)

