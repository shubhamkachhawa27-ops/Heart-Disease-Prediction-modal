import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from database import execute_query, fetch_all, fetch_one
from datetime import datetime

# Load Environment keys
load_dotenv()

class HealthcareChatbot:
    def __init__(self, user_email):
        self.user_email = user_email
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        
        # Initialize client securely if key available
        if self.api_key and "sk-" in self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def get_patient_context(self):
        """Fetch the most recent clinical parameters from database."""
        latest = fetch_one("SELECT risk_level, result, input_data FROM predictions WHERE user_email = ? ORDER BY date DESC LIMIT 1", (self.user_email,))
        if latest:
            risk_prob, risk_lbl, raw_json = latest
            try:
                vitals = json.loads(raw_json)
                context = (f"The user is a patient whose recent heart risk assessment generated a {risk_lbl} ({risk_prob:.1f}%). "
                           f"Their vitals include: Age {vitals.get('age', 'Unknown')}, "
                           f"Blood Pressure {vitals.get('trestbps', 'Unknown')} mmHg, "
                           f"Cholesterol {vitals.get('chol', 'Unknown')} mg/dl.")
                return context
            except:
                pass
        return "The user has not taken a recent health assessment."

    def generate_response(self, user_input, chat_history_context=None):
        if not self.client:
            return "Configuration Error: Valid OpenAI API key missing. Please configure your .env file."
            
        patient_context = self.get_patient_context()
        
        system_prompt = (
            "You are a helpful medical assistant specializing in cardiovascular/heart health. "
            "Provide simple, safe, and non-diagnostic advice using easy language with no complex medical jargon. "
            f"\nPatient Intelligence Data: {patient_context}\n"
            "If they ask general questions, respond accurately. Emphasize that you are an AI and they should consult doctors for critical issues."
        )

        messages = [{"role": "system", "content": system_prompt}]
        
        # Hydrate existing short-term context seamlessly
        if chat_history_context:
            for past in chat_history_context[-4:]: # Load last 4 interactions to save prompt tokens
                messages.append(past)
                
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.5,
                max_tokens=250
            )
            bot_reply = response.choices[0].message.content
            
            self._save_chat(user_input, bot_reply)
            return bot_reply
            
        except Exception as e:
            return "Server Error: Our NLP inference cluster is currently unavailable. Please check your network or try again later."

    def _save_chat(self, message, response):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execute_query('INSERT INTO chats (user_email, message, response, timestamp) VALUES (?, ?, ?, ?)', 
                     (self.user_email, message, response, timestamp))

    def load_chat_history(self):
        data = fetch_all('SELECT message, response FROM chats WHERE user_email = ? ORDER BY id ASC', (self.user_email,))
        history = []
        for msg, resp in data:
            history.append({"role": "user", "content": msg})
            history.append({"role": "assistant", "content": resp})
        return history
