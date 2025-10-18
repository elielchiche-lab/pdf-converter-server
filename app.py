import os, io, requests
from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename

API_KEY = os.environ.get("API_KEY")  # <-- tu définiras ça sur Railway
STORAGE_DIR = os.environ.get("STORAGE_DIR", "/tmp/uploads")

app = Flask(__name__)
os.makedirs(STORAGE_DIR, exist_ok=True)

def require_api_key(req):
    key = req.headers.get("X-API-Key")
    if not API_KEY or key != API_KEY:
        abort(401, description="Unauthorized: invalid API key")

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/upload", methods=["POST"])
def upload():
    require_api_key(request)
    if "file" not in request.files:
        return jsonify({"error": "No file field 'file'"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(f.filename)
    save_path = os.path.join(STORAGE_DIR, filename)
    f.save(save_path)

    return jsonify({
        "ok": True,
        "filename": filename,
        "path": save_path
    }), 200

@app.route("/upload-from-url", methods=["POST"])
def upload_from_url():
    require_api_key(request)
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    filename = secure_filename(data.get("filename") or "document.pdf")
    return_binary = bool(data.get("return_binary"))

    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        return jsonify({"error": f"Download failed: {r.status_code}"}), 400

    content = r.content

    if return_binary:
        return send_file(
            io.BytesIO(content),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )

    save_path = os.path.join(STORAGE_DIR, filename)
    with open(save_path, "wb") as out:
        out.write(content)

    return jsonify({
        "ok": True,
        "filename": filename,
        "path": save_path,
        "size": len(content)
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
