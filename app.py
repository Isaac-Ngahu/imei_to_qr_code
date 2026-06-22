from flask import Flask, request, render_template, send_file, jsonify
from flask_cors import CORS
from weasyprint import HTML
import pandas as pd
import qrcode
from io import BytesIO
import base64
import random
# from app import app

app = Flask(__name__)
CORS(app)

BOTTOM_TEXT = "FOR RETAILER RECORD"


@app.route('/')
def home():
    return render_template('index.html')


# ✅ Generate QR in memory (no files)
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
        back_color="transparent"
    ).convert("RGBA")

    pixels = img.getdata()
    new_pixels = []

    for pixel in pixels:
        if pixel[:3] == (255, 255, 255):
            new_pixels.append((255, 255, 255, 0))
        else:
            new_pixels.append(pixel)

    img.putdata(new_pixels)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer



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


@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    try:

        # ✅ Validate file
        if 'file' not in request.files:
            return jsonify({
                "status": "error",
                "message": "Excel file required"
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                "status": "error",
                "message": "No file selected"
            }), 400

        # ✅ Read Excel directly (no saving)
        df = pd.read_excel(file)

        labels = []

        for _, row in df.iterrows():

            model = str(row.get('model', 'Unknown Model')).strip()
            storage = str(row.get('storage', '')).strip()

            # ✅ Handle IMEI columns
            if 'imei1' in df.columns:
                imei1 = str(row.get('imei1', '')).strip()
                imei2 = str(row.get('imei2', '')).strip()

            elif 'imei' in df.columns:
                imei1 = str(row.get('imei', '')).strip()

                base = imei1[:-4] if len(imei1) > 4 else imei1

                # generate random last 4 digits
                random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(4)])

                imei2 = base + random_suffix
                
            else:
                return jsonify({
                    "status": "error",
                    "message": "Excel must contain 'imei' or 'imei1/imei2'"
                }), 400

            if not imei1 or imei1.lower() == "nan":
                continue

            # ✅ Generate QR (memory)
            qr_buffer = generate_transparent_qr(imei1)

            # ✅ Convert to base64 for HTML embedding
            qr_base64 = base64.b64encode(qr_buffer.read()).decode("utf-8")
            qr_src = f"data:image/png;base64,{qr_base64}"

            labels.append({
                "model": model,
                "storage": storage,
                "imei1": imei1,
                "imei2": imei2,
                "qr": qr_src
            })

        if not labels:
            return jsonify({
                "status": "error",
                "message": "No valid IMEIs found"
            }), 400

        # ✅ Generate HTML
        html = render_template(
            "labels.html",
            labels=labels,
            bottom=BOTTOM_TEXT
        )

        # ✅ Generate PDF in memory
        pdf_buffer = BytesIO()

        HTML(string=html).write_pdf(pdf_buffer)

        pdf_buffer.seek(0)

        # ✅ Send directly (no saving)
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


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
