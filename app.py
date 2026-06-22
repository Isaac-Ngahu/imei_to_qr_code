from flask import Flask, request, render_template, send_file, jsonify
from flask_cors import CORS
import pandas as pd
import qrcode
from io import BytesIO
import base64
import random

from playwright.sync_api import sync_playwright

app = Flask(__name__)
CORS(app)

BOTTOM_TEXT = "FOR RETAILER RECORD"


# =========================
# HOME
# =========================
@app.route('/')
def home():
    return render_template('index.html')


# =========================
# QR GENERATION
# =========================
def generate_transparent_qr(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=1
    )

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color="black",
        back_color="white"
    ).convert("RGBA")

    datas = img.getdata()

    new_data = []
    for item in datas:
        # Make white pixels transparent
        if item[:3] == (255, 255, 255):
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


# =========================
# TEMPLATE DOWNLOAD
# =========================
@app.route('/download_template')
def download_template():
    df = pd.DataFrame({
        "imei": [""],
        "model": [""],
        "storage": [""]
    })

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="imei_template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =========================
# MAIN GENERATION
# =========================
@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "Excel file required"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400

        df = pd.read_excel(file)

        labels = []

        for _, row in df.iterrows():

            model = str(row.get('model', 'Unknown')).strip()
            storage = str(row.get('storage', '')).strip()

            if 'imei1' in df.columns:
                imei1 = str(row.get('imei1', '')).strip()
                imei2 = str(row.get('imei2', '')).strip()

            elif 'imei' in df.columns:
                imei1 = str(row.get('imei', '')).strip()
                base = imei1[:-4] if len(imei1) > 4 else imei1
                imei2 = base + ''.join([str(random.randint(0, 9)) for _ in range(4)])
            else:
                return jsonify({"status": "error", "message": "Excel must contain imei or imei1/imei2"}), 400

            if not imei1 or imei1.lower() == "nan":
                continue

            qr_buffer = generate_transparent_qr(imei1)
            qr_base64 = base64.b64encode(qr_buffer.read()).decode("utf-8")

            labels.append({
                "model": model,
                "storage": storage,
                "imei1": imei1,
                "imei2": imei2,
                "qr": f"data:image/png;base64,{qr_base64}"
            })

        if not labels:
            return jsonify({"status": "error", "message": "No valid IMEIs found"}), 400

        # =========================
        # RENDER HTML
        # =========================
        html = render_template(
            "labels.html",
            labels=labels,
            bottom=BOTTOM_TEXT
        )

        # =========================
        # PLAYWRIGHT PDF (KEY PART)
        # =========================
        pdf_buffer = BytesIO()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )

            page = browser.new_page()

            page.set_content(html, wait_until="networkidle")

            pdf_bytes = page.pdf(
                format="A4",
                print_background=True
            )

            browser.close()

        pdf_buffer.write(pdf_bytes)
        pdf_buffer.seek(0)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name="imei_labels.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )