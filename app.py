"""Analisador de Perfil - Método Rivas Pilar 1."""

from flask import Flask, render_template, request, jsonify
from scraper import scrape_profile, extract_username
from analyzer import analyze_profile

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analisar", methods=["POST"])
def analisar():
    data = request.get_json()
    url_or_username = data.get("perfil", "").strip()

    if not url_or_username:
        return jsonify({"error": "Por favor, insira um link ou @username do Instagram."}), 400

    try:
        username = extract_username(url_or_username)
        profile = scrape_profile(username)
        results = analyze_profile(profile)
        return jsonify({
            "success": True,
            "profile": {
                "username": profile["username"],
                "full_name": profile["full_name"],
                "profile_pic_url": profile["profile_pic_url"],
                "followers": profile["followers"],
                "following": profile["following"],
                "posts_count": profile["posts_count"],
                "biography": profile["biography"],
                "external_url": profile["external_url"],
                "category": profile["category"],
            },
            "analysis": results,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Erro inesperado: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
