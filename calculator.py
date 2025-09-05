from flask import Flask, render_template, request, redirect, url_for, session
import math

app = Flask(__name__, template_folder="template")
app.secret_key = "supersecretkey"  # session 必须要

# ---------- 计算函数 ----------
def calculate_rer(weight):
    """计算RER"""
    return 70 * (weight ** 0.75)

def calculate_mer(rer, activity_factor):
    """计算MER"""
    return rer * activity_factor

def convert_lb_to_kg(lb):
    return lb * 0.4536


# ---------- 路由 ----------
@app.route("/", methods=["GET", "POST"])
def step1():
    if request.method == "POST":
        session["dog_name"] = request.form["dog_name"]
        return redirect(url_for("step2"))
    return render_template("step1.html")


@app.route("/step2", methods=["GET", "POST"])
def step2():
    if request.method == "POST":
        session["gender"] = request.form["gender"]
        return redirect(url_for("step3"))
    return render_template("step2.html", dog=session.get("dog_name"))


@app.route("/step3", methods=["GET", "POST"])
def step3():
    if request.method == "POST":
        weight = float(request.form.get("weight"))
        unit = request.form.get("unit")
        if unit == "lb":
            weight = convert_lb_to_kg(weight)
        session["weight"] = weight

        breed = request.form.get("breed")
        if breed == "Other":
            breed = request.form.get("other_breed")
        session["breed"] = breed

        return redirect(url_for("step4"))
    return render_template("step3.html", dog=session.get("dog_name"))


@app.route("/step4", methods=["GET", "POST"])
def step4():
    if request.method == "POST":
        activity_factor = float(request.form.get("activity_factor"))
        fresh_ratio = float(request.form.get("fresh_ratio"))
        cycle_days = int(request.form.get("cycle_days"))

        chicken = request.form.get("chicken")
        beef = request.form.get("beef")
        chicken_ratio = 0.0
        beef_ratio = 0.0

        if chicken and beef:
            chicken_ratio = float(request.form.get("chicken_ratio"))
            beef_ratio = 1 - chicken_ratio
        elif chicken:
            chicken_ratio = 1.0
        elif beef:
            beef_ratio = 1.0

        # 存 session
        session["activity_factor"] = activity_factor
        session["fresh_ratio"] = fresh_ratio
        session["cycle_days"] = cycle_days
        session["chicken_ratio"] = chicken_ratio
        session["beef_ratio"] = beef_ratio

        return redirect(url_for("result"))
    return render_template("step4.html", dog=session.get("dog_name"))


@app.route("/result")
def result():
    dog = session.get("dog_name")
    gender = session.get("gender")
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
    fresh_g = round(fresh_kcal / 3)  # 假设 1g ≈ 3kcal

    total_g = fresh_g * cycle_days

    # 包装规格换算
    pack_size = 454  # 1lb
    packs_total = math.ceil(total_g / pack_size)

    recipes = {}
    if chicken_ratio > 0:
        grams = round(total_g * chicken_ratio)
        recipes["Chicken"] = {
            "grams": grams,
            "packs_1lb": math.ceil(grams / pack_size),
        }
    if beef_ratio > 0:
        grams = round(total_g * beef_ratio)
        recipes["Beef"] = {
            "grams": grams,
            "packs_1lb": math.ceil(grams / pack_size),
        }

    return render_template(
        "result.html",
        dog=dog,
        gender=gender,
        breed=breed,
        weight=round(weight, 1),
        rer=rer,
        mer=mer,
        fresh_kcal=fresh_kcal,
        fresh_g=fresh_g,
        cycle_days=cycle_days,
        total_g=total_g,
        recipes=recipes,
        total_packs=packs_total,
    )
