import asyncio
from AIPromptAssistant import AIPromptAssistant  # استيراد من الملف التاني
from collections import defaultdict

# Mock Engine بسيط للاختبار
class MockEngine:
    def __init__(self):
        self.default_settings = {
            "deep_search": False,
            "think_mode": False
        }
        self.grok_instance = None

    def analyze_prompt(self, prompt: str) -> dict:
        errors = {}
        if len(prompt.split()) < 5:
            errors["low_detail"] = True
        if "helicopter" in prompt.lower() and "runway" not in prompt.lower():
            errors["missing_elements"] = ["runway"]
        return {"errors": errors}

# البرنامج الرئيسي
async def main():
    engine = MockEngine()
    assistant = AIPromptAssistant(engine)

    print("🧠 AI Prompt Assistant Demo")
    print("اكتب promptك، اضغط Enter عشان يحسنه ليك")
    print("اكتب 'exit' عشان تخرج\n")

    while True:
        prompt = input("Prompt: ").strip()
        
        if prompt.lower() == "exit":
            print("باي باي! 👋")
            break
        if not prompt:
            continue

        print("جاري التحسين...\n")
        enhanced = await assistant.interact(prompt)  # أو on_enter_press لو عايز الـ prediction
        
        print(f"✅ الـ Prompt المحسن:\n{enhanced}\n")
        print("-" * 60)
        print("المحادثة الكاملة:")
        print(assistant.get_conversation())
        print("-" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())