## AI-Prompt-Assistant ##

🧠 AI Prompt Assistant Pro
An Intelligent Tool for Enhancing AI Image Generation Prompts
📖 Overview
AI Prompt Assistant Pro is a full-featured, local application designed to intelligently enhance text prompts for AI image generators such as Stable Diffusion, Midjourney, Flux, and others.
Key Features:

✅ Smart Prompt Enhancement with interactive suggestions
✅ Generated Image Analysis using OpenCV
✅ SQLite Database for storing prompt history
✅ Integration with xAI API (Grok) for advanced contextual enhancement
✅ Modern Web Interface (Flask + HTML + JavaScript)
✅ Automated Unit Tests with pytest
✅ Optional Image Generation via Stable Diffusion WebUI

🚀 How to Run (Step-by-Step)
1. Install Required Libraries
Bashpip install flask opencv-python pillow numpy requests
2. Start the Server
Bashcd AIPromptAssistant
python app.py
3. Open the Application
Open your browser and navigate to:
texthttp://127.0.0.1:5000
4. Usage

Type your prompt in the text area (e.g., helicopter in desert)
Watch the live preview update instantly with enhancements
Click "Generate Enhanced Prompt" to get the final version
Use "Copy Result" to copy the optimized prompt
Upload a generated image and click "Analyze Image" for feedback
View full history including prompts, results, and notes

🛠 Project Structure
textAIPromptAssistant/
├── AIPromptAssistant.py      # Core backend logic
├── app.py                    # Flask web server & API endpoints
├── index.html                # Main user interface
├── demo_terminal.py          # Simple terminal demo (optional)
├── test_AIPromptAssistant.py # Unit tests (pytest)
├── prompt_history.db         # SQLite database (auto-created)
└── static/                   # Generated images
    └── generated.png
📚 Required Libraries

LibraryPurposeInstallation CommandflaskWeb server and routingpip install flaskopencv-pythonImage analysis (cv2)pip install opencv-pythonpillowImage processingpip install pillownumpyNumerical operationspip install numpyrequestsAPI calls (xAI / Stable Diffusion)pip install requestssqlite3Built-in databaseIncluded with PythonpytestUnit testing (optional)pip install pytest
🔧 Optional Requirements (for Automatic Image Generation)
Stable Diffusion WebUI

Download from GitHub
Launch the WebUI on http://127.0.0.1:7860
The app will automatically send prompts and retrieve generated images

🎯 How It Works
textUser enters prompt
        ↓
Intelligent analysis (keyword detection, environment validation)
        ↓
Interactive suggestions displayed
        ↓
Prompt enhanced with professional descriptors
        ↓
Optional: Image generated via Stable Diffusion
        ↓
Optional: Generated image analyzed (edges, brightness, element detection)
        ↓
Everything saved to SQLite history (prompt, enhanced prompt, image, notes)
🧪 Running Tests
Bashpytest test_AIPromptAssistant.py -v
🙏 Acknowledgments

Built with passion by Rashed Dadou
Powered by Grok (xAI), OpenCV, Flask, and open-source AI tools


Enjoy creating stunning AI art with perfectly optimized prompts! 🚀✨

This system was designed to be the ultimate personal assistant for creating images. It's not just a tool, but a creative companion that helps you bring your ideas to life with the highest quality and in the shortest time.

This design was unprecedented at a time when most instant image engineering systems relied on a single integrated engine (instant generation → direct creation).

(Designed July 10, 2025)
