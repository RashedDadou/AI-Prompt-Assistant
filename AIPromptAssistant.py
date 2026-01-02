from flask import Flask, request, jsonify, send_from_directory
import os
import numpy as np   # ←←←←←←←←←←←←←←←←← أضف السطر ده هنا
import asyncio
import re
import requests
import sqlite3
import cv2
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any

class AIPromptAssistant:
    def __init__(self, engine, generator_config=None):
        """Initialize the AIPromptAssistant with an engine and configuration."""
        self.engine = engine
        self.generator_config = generator_config or {"resolution": "high", "model": "default"}
        self.conversation = []
        self.user_preferences = defaultdict(lambda: {"weight": 0, "timestamp": datetime.now()})
        self.current_prediction = None
        self.is_generating = False
        self.weight_threshold_max = 5
        self.weight_threshold_min = -5
        
        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        # كل الـ self. اللي هنا لازم يكون داخل __init__ فقط
        self.server_url = "https://api.x.ai/v1/chat/completions"  # الصحيح دلوقتي (chat/completions)
        self.api_key = os.getenv("XAI_API_KEY", "xai_dummy_key")
        self.db_path = "prompt_history.db"
        
        # حفظ الاقتراحات للتعلم الذكي
        self.last_displayed_suggestions = []
        self.suggestion_to_enhancement = {}
        
        self._create_history_table()  # ننشئ الجدول مرة واحدة
        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        
    def _get_db_connection(self):
        """فتح اتصال جديد بقاعدة البيانات لكل طلب (يحل مشكلة thread safety)"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return conn

    def _create_history_table(self):
        """إنشاء الجدول إذا لم يكن موجودًا"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT,
                enhanced_prompt TEXT,
                image_path TEXT,
                timestamp DATETIME,
                notes TEXT
            )
        """)
        conn.commit()
        conn.close()

    def get_history(self) -> List[Dict[str, Any]]:
        """استرجاع السجل من قاعدة البيانات بأمان"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, prompt, enhanced_prompt, timestamp, notes FROM prompt_history ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    "id": row[0],
                    "prompt": row[1] or "",
                    "enhanced_prompt": row[2] or "",
                    "timestamp": row[3],
                    "notes": row[4] or "لا ملاحظات"
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error loading history: {e}")
            return []
        
    def analyze_partial_input(self, partial_prompt: str) -> Dict[str, Any]:
            if not partial_prompt.strip():
                return {"details": {"errors": {"empty_input": "Prompt is empty"}}, "display_suggestions": [], "actual_enhancements": []}
            
            details = self.engine.analyze_prompt(partial_prompt)
            display_suggestions = []
            actual_enhancements = []

            lower = partial_prompt.lower()
            if "helicopter" in lower or "مروحية" in lower:
                display_suggestions.append("إضافة مطار عسكري وبيئة صحراوية؟")
                actual_enhancements.append("military helicopter on desert airbase, vast sandy terrain, heat haze, clear sky")

            if "image" in lower or "صورة" in lower:
                display_suggestions.append("تحسين الإضاءة والجودة؟")
                actual_enhancements.append("cinematic golden hour lighting, ultra detailed, 8k resolution, photorealistic")

            if "low_detail" in details.get("errors", {}) and preferences.get("environmental details", {"weight": 0})["weight"] > 0:
                all_display.append("Add professional details?")
                all_actual.append("dramatic lighting, high contrast, ultra realistic")

            return {"details": details, "display_suggestions": display_suggestions, "actual_enhancements": actual_enhancements}
                    
    def prepare_prediction(self, partial_prompt: str):
        """إعداد التنبؤ الحي باستخدام وصف نقي 100%"""
        analysis = self.analyze_partial_input(partial_prompt)
        env_analysis = self.validate_environment(partial_prompt)

        all_display = analysis["display_suggestions"] + env_analysis["display_suggestions"]
        all_actual = analysis["actual_enhancements"] + env_analysis["actual_enhancements"]

        if all_actual:
            enhanced_prompt = partial_prompt + ", " + ", ".join(all_actual)
            
            self.current_prediction = {
                "prompt": partial_prompt,
                "display_suggestions": all_display,        # للعرض في الـ UI
                "actual_enhancements": all_actual,         # للإضافة
                "enhanced_prompt": enhanced_prompt          # نظيف تمامًا
            }
            self.conversation.append(f"Assistant: معاينة حية: {enhanced_prompt}")
        else:
            self.current_prediction = None
                                        
    def validate_environment(self, prompt: str) -> Dict[str, Any]:
        issues = {}
        display_suggestions = []
        actual_enhancements = []

        lower = prompt.lower()
        if "desert" in lower and "wind" not in lower:
            issues["missing_wind"] = "Wind direction missing"
            display_suggestions.append("Add wind effect?")
            actual_enhancements.append("landing into the wind, visible dust clouds from rotor wash")

        if "military airport" in lower and "runway" not in lower:
            issues["missing_runway"] = "Runway missing"
            display_suggestions.append("Add military runway?")
            actual_enhancements.append("on a 3000m asphalt runway with safety markings")

        if "helicopter" in lower and not ("landing" in lower or "hover" in lower):
            issues["missing_position"] = "Helicopter position missing"
            display_suggestions.append("Specify helicopter position?")
            actual_enhancements.append("in low hover position, rotor blades spinning")

        return {"issues": issues, "display_suggestions": display_suggestions, "actual_enhancements": actual_enhancements}

    async def call_server_api(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [{"role": "user", "content": data["prompt"]}],
            "model": "grok-beta",  # أو "grok-2" لو متاح
            "max_tokens": data.get("max_tokens", 100),
            "temperature": data.get("temperature", 0.7)
        }
        try:
            response = requests.post(self.server_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            text = result["choices"][0]["message"]["content"]
            return {"choices": [{"text": text}]}
        except Exception as e:
            return {"error": str(e)}
    
    async def search_and_enhance(self, prompt: str) -> Dict[str, List[str]]:
        search_terms = ["military airport design", "helicopter landing desert"]
        enhanced_data = {}
        try:
            data = {
                "model": "grok-3",
                "prompt": f"Enhance '{prompt}' with details for military airport and helicopter in desert.",
                "max_tokens": 100,
                "temperature": 0.7
            }
            response = await self.call_server_api("completions", data)
            if "error" not in response:
                text = response.get("choices", [{}])[0].get("text", "")
                suggestions = text.split(", ") or ["30x30m runway", "land into wind"]
                for term in search_terms:
                    enhanced_data[term] = suggestions
            else:
                for term in search_terms:
                    enhanced_data[term] = ["default: 30x30m runway"]
        except Exception as e:
            for term in search_terms:
                enhanced_data[term] = [f"default: failed ({str(e)})"]
        return enhanced_data          
                
    async def interact(self, prompt: str, selected_suggestions: List[str] = None) -> str:
        """
        الدالة الرئيسية لتحسين الـ prompt بشكل ذكي وشامل.
        
        Args:
            prompt: الـ prompt الأصلي من المستخدم
            selected_suggestions: 
                - None → قبول تلقائي لكل الاقتراحات (للـ demo أو الاستخدام السريع)
                - [] → رفض كل الاقتراحات
                - list من strings → قبول الاقتراحات المحددة فقط
        
        Returns:
            الـ prompt المحسّن والنهائي
        """
        self.conversation.append(f"User: {prompt}")

        # 1. تحليل شامل للـ prompt
        analysis = self.analyze_initial_input(prompt)
        enhanced_prompt = prompt
        added_phrases = set()  # لتجنب التكرار

        # 2. حفظ الاقتراحات لاستخدامها في analyze_user_feedback لاحقًا
        self.last_displayed_suggestions = analysis["display_suggestions"]
        self.suggestion_to_enhancement = dict(zip(
            analysis["display_suggestions"],
            analysis["actual_enhancements"]
        ))

        # 3. عرض الاقتراحات للمستخدم (بالإنجليزية الآن)
        if analysis["display_suggestions"]:
            suggestions_text = " | ".join(analysis["display_suggestions"])
            self.conversation.append(f"Assistant: {suggestions_text}")

            # تحديد ما إذا كان المستخدم يقبل أم يرفض أم يختار
            accept_all = False
            if selected_suggestions is None:  # قبول تلقائي (مثل الـ demo)
                accept_all = True
                self.conversation.append("User: Auto-accepted all suggestions")
            elif len(selected_suggestions) > 0:  # اختيار محدد
                self.conversation.append(f"User: Selected: {', '.join(selected_suggestions)}")
                # هنضيف بس اللي اختارهم
                for disp_sug in selected_suggestions:
                    if disp_sug in self.suggestion_to_enhancement:
                        enhancement = self.suggestion_to_enhancement[disp_sug]
                        if enhancement.lower() not in enhanced_prompt.lower():
                            enhanced_prompt += ", " + enhancement
                            added_phrases.add(enhancement.lower())
                # لو اختار حاجة، نعتبره قبل جزئيًا ونكمل باقي التحسينات
                accept_all = True
            else:
                # رفض صريح (قائمة فاضية)
                self.conversation.append("User: Rejected all suggestions")
                accept_all = False

            # إذا قبل كليًا أو جزئيًا → نضيف كل التحسينات الفعلية
            if accept_all:
                for enhancement in analysis["actual_enhancements"]:
                    if enhancement.lower() not in enhanced_prompt.lower():
                        enhanced_prompt += ", " + enhancement
                        added_phrases.add(enhancement.lower())

        # 4. بحث إضافي عبر xAI API إذا كان هناك نقص حرج (مثل runway, wind, position)
        critical_missing = any(key in analysis.get("issues", {}) for key in ["missing_runway", "missing_wind", "missing_position"])
        if critical_missing or "helicopter" in prompt.lower():
            search_results = await self.search_and_enhance(prompt)
            extra = []
            if "military airport design" in search_results:
                extra.extend(search_results["military airport design"])
            if "helicopter landing desert" in search_results:
                extra.extend(search_results["helicopter landing desert"])

            for phrase in extra[:5]:
                if phrase and phrase.lower() not in enhanced_prompt.lower():
                    enhanced_prompt += ", " + phrase
                    added_phrases.add(phrase.lower())

        # 5. Deep Search (اختياري)
        if self.engine.default_settings.get("deep_search", False):
            try:
                search_response = await self.call_server_api("completions", {
                    "model": "grok-3",
                    "prompt": f"Provide concise artistic keywords for image generation: {enhanced_prompt}",
                    "max_tokens": 40,
                    "temperature": 0.7
                })
                if "error" not in search_response:
                    context = search_response.get("choices", [{}])[0].get("text", "").strip()
                    if context and context.lower() not in enhanced_prompt.lower():
                        enhanced_prompt += ", " + context
            except Exception as e:
                self.conversation.append(f"Assistant: Deep search warning: {str(e)}")

        # 6. Think Mode (اختياري) - تحسين شامل
        if self.engine.default_settings.get("think_mode", False):
            try:
                think_response = await self.call_server_api("completions", {
                    "model": "grok-3",
                    "prompt": f"Refine this image prompt to be more professional, detailed, and optimized for AI generation:\n{enhanced_prompt}",
                    "max_tokens": 120,
                    "temperature": 0.5
                })
                if "error" not in think_response:
                    refined = think_response.get("choices", [{}])[0].get("text", "").strip()
                    if refined and len(refined.split()) > len(enhanced_prompt.split()) * 0.7:
                        enhanced_prompt = refined
                        self.conversation.append("Assistant: Prompt refined using Think Mode")
            except Exception as e:
                self.conversation.append(f"Assistant: Think mode warning: {str(e)}")

        # 7. لمسات جودة نهائية بطريقة ذكية باستخدام add_if_not_similar
        final_boosters = [
            "highly detailed",
            "8k resolution",
            "photorealistic",
            "cinematic lighting",
            "sharp focus",
            "professional photography",
            "masterpiece",
            "best quality"
        ]

        for booster in final_boosters:
            enhanced_prompt = self.add_if_not_similar(enhanced_prompt, booster)

        # 8. تسجيل النتيجة النهائية
        self.conversation.append(f"Assistant: Enhanced prompt:\n{enhanced_prompt}")

        # 9. تحديث تفضيلات المستخدم بناءً على ردوده (بعد ما خلصنا)
        self.analyze_user_feedback()

        return enhanced_prompt
                           
    def cancel_prediction(self):
        # إلغاء التنبؤ إذا تغير الإدخال
        if self.current_prediction:
            self.conversation.append(f"Assistant: Prediction cancelled for: {self.current_prediction['prompt']}")
            self.current_prediction = None

    def analyze_user_feedback(self) -> Dict[str, Any]:
        """
        تحليل ردود المستخدم (نعم/لا/اختيار جزئي) لتحديث تفضيلاته بشكل ذكي.
        يعتمد بشكل أساسي على ربط رد المستخدم بالاقتراحات التي عُرضت له في الجلسة الحالية.
        يدعم أيضًا التعلم من الكلمات المفتاحية العامة كـ fallback.
        """
        # 1. التأكد من وجود اقتراحات سابقة محفوظة (من interact)
        if not hasattr(self, 'last_displayed_suggestions') or not self.last_displayed_suggestions:
            self._fallback_keyword_learning()
            return self.user_preferences

        # 2. استخراج آخر رد من المستخدم
        last_user_line = None
        for line in reversed(self.conversation):
            if line.startswith("User:"):
                last_user_line = line.replace("User:", "").strip()
                break

        if not last_user_line:
            self._fallback_keyword_learning()  # حتى لو مفيش رد جديد، نتعلم من المحادثة العامة
            return self.user_preferences

        user_response_lower = last_user_line.lower()

        # كلمات دلالية للقبول والرفض (عربي وإنجليزي)
        acceptance_keywords = {"نعم", "ايوه", "أيوه", "yes", "ok", "تمام", "عايز", "أضف", "add", "include", "يلا", "حلو"}
        rejection_keywords = {"لا", "لأ", "no", "مش عايز", "بدون", "remove", "ممنوع", "مش لازم", "delete"}

        # تحديد نوع الرد العام
        is_acceptance = any(word in user_response_lower for word in acceptance_keywords)
        is_rejection = any(word in user_response_lower for word in rejection_keywords)

        # 3. المرور على كل اقتراح عرضناه للمستخدم
        for suggestion in self.last_displayed_suggestions:
            sug_lower = suggestion.lower()
            enhancement = self.suggestion_to_enhancement.get(suggestion, "")

            if not enhancement:
                continue

            key = enhancement.split(",")[0].strip().lower()[:30]

            suggestion_words = set(re.findall(r'\w+', sug_lower))
            user_words = set(re.findall(r'\w+', user_response_lower))
            direct_mention = bool(suggestion_words.intersection(user_words))

            if is_acceptance or (direct_mention and not is_rejection):
                self.user_preferences[key]["weight"] = min(
                    self.user_preferences[key]["weight"] + 3,
                    self.weight_threshold_max
                )
                self.user_preferences[key]["timestamp"] = datetime.now()

            elif is_rejection or (direct_mention and not is_acceptance):
                self.user_preferences[key]["weight"] = max(
                    self.user_preferences[key]["weight"] - 2,
                    self.weight_threshold_min
                )
                self.user_preferences[key]["timestamp"] = datetime.now()

            elif is_acceptance and not direct_mention:
                self.user_preferences[key]["weight"] = min(
                    self.user_preferences[key]["weight"] + 1,
                    self.weight_threshold_max
                )
                self.user_preferences[key]["timestamp"] = datetime.now()

            elif is_rejection and not direct_mention:
                self.user_preferences[key]["weight"] = max(
                    self.user_preferences[key]["weight"] - 1,
                    self.weight_threshold_min
                )
                self.user_preferences[key]["timestamp"] = datetime.now()

        # 4. fallback شامل: نتعلم من المحادثة كلها (حتى الكلمات المهمة زي runway و wind)
        self._fallback_keyword_learning()

        return self.user_preferences

    def _fallback_keyword_learning(self):
        """
        تعلم احتياطي من الكلمات المفتاحية المهمة في المحادثة كلها
        """
        full_text = " ".join(self.conversation).lower()

        important_keywords = {
            "runway": 2,
            "wind": 2,
            "hover": 2,
            "position": 2,
            "lighting": 1,
            "detailed": 1,
            "desert": 1,
            "military": 1,
            "golden hour": 2,
            "photorealistic": 1,
            "8k": 1,
            "cinematic": 1
        }

        for keyword, boost in important_keywords.items():
            if keyword in full_text:
                current_weight = self.user_preferences[keyword].get("weight", 0)
                self.user_preferences[keyword]["weight"] = min(current_weight + boost, self.weight_threshold_max)
                self.user_preferences[keyword]["timestamp"] = datetime.now()
                            
    def get_conversation(self):
        return "\n".join(self.conversation)

    def on_input_change(self, partial_prompt: str):
        if self.is_generating:
            return
        if self.current_prediction and self.current_prediction["prompt"] != partial_prompt:
            self.cancel_prediction()
        self.prepare_prediction(partial_prompt)

    async def on_enter_press(self, final_prompt: str, selected_suggestions: List[str] = None) -> str:
        if self.current_prediction and self.current_prediction["prompt"] == final_prompt:
            self.is_generating = True
            enhanced = self.current_prediction["enhanced_prompt"]
            self.conversation.append(f"Assistant: استخدام المعاينة الفورية ← {enhanced}")
            self.is_generating = False
            return enhanced
        
        self.is_generating = True
        enhanced = await self.interact(final_prompt, selected_suggestions)
        self.is_generating = False
        return enhanced