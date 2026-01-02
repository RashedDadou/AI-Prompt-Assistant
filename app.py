from flask import Flask, request, jsonify, send_from_directory
from AIPromptAssistant import AIPromptAssistant
import asyncio
import os
import numpy as np    # للـ numpy
import cv2            # للـ OpenCV (تحليل الصور)

app = Flask(__name__, static_folder='.', template_folder='.')

class MockEngine:
    def analyze_prompt(self, prompt):
        return {"errors": {}}
    default_settings = {"deep_search": False, "think_mode": False}

assistant = AIPromptAssistant(MockEngine())

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/preview', methods=['POST'])
def preview():
    prompt = request.json.get('prompt', '')
    analysis = assistant.analyze_initial_input(prompt)
    
    enhanced = prompt
    if analysis.get("actual_enhancements"):
        enhanced += ", " + ", ".join(analysis["actual_enhancements"])
    
    enhanced += ", highly detailed, 8k resolution, cinematic lighting"
    
    return jsonify({
        "enhanced_prompt": enhanced,
        "display_suggestions": analysis.get("display_suggestions", [])
    })
    
@app.route('/enhance', methods=['POST'])
def enhance():
    prompt = request.json.get('prompt', '')
    try:
        enhanced = asyncio.run(assistant.interact(prompt))
        return jsonify({"enhanced_prompt": enhanced})
    except Exception:
        # fallback آمن لو حصل أي خطأ
        fallback = prompt + ", military helicopter on desert airbase, dramatic golden hour lighting, highly detailed, 8k, photorealistic"
        return jsonify({"enhanced_prompt": fallback})

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # تحويل لـ numpy array
    filestr = file.read()
    npimg = np.frombuffer(filestr, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    # تحليل بسيط (مثال: كشف ألوان، حجم، كائنات رئيسية)
    height, width, channels = img.shape
    avg_color = cv2.mean(img)[:3]
    
    # يمكن تضيف YOLO أو CLIP لاحقًا، بس دلوقتي نبدأ بسيط
    notes = f"""
    الصورة: {width}x{height}
    الألوان الغالبة: أحمر {avg_color[0]:.0f}, أخضر {avg_color[1]:.0f}, أزرق {avg_color[2]:.0f}
    """
    
    # لو في مروحية مثلاً (تحليل بسيط باللون الرمادي العسكري)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if np.mean(gray) < 120 and "helicopter" in assistant.conversation[-1].lower():
        notes += "\nيُحتمل وجود كائنات عسكرية (ظلام وتفاصيل معدنية)"

    return jsonify({"notes": notes.strip()})

@app.route('/history')
def history():
    try:
        hist = assistant.get_history()
        return jsonify(hist)
    except Exception as e:
        return jsonify([])
    
@app.route('/generate_image', methods=['POST'])
def generate_image():
    return jsonify({"notes": "توليد الصورة جاهز عند تشغيل Stable Diffusion"})

if __name__ == '__main__':
    os.makedirs("static", exist_ok=True)
    app.run(port=5000, debug=True)