# -*- coding: utf-8 -*-
"""
JARVIS - Hindi Voice Assistant with ALL Features
Version: 5.0 - COMPLETE + AI OPENROUTER
Features: YouTube, News, Weather, Apps, System Info, WhatsApp, Screenshot, etc. + AI
"""

import speech_recognition as sr
import datetime
import webbrowser
import os
import time
import sys
import threading
import requests
import json
import re
import random
import pyautogui
import psutil
import platform
import socket
import subprocess
from gtts import gTTS
import playsound
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# ==================== NEW: OPENROUTER AI IMPORT ====================
import openai

# ==================== FLASK GUI SETUP ====================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

conversation_history = []

@app.route('/')
def index():
    return render_template('gui.html')

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('status_update', {'mic': 'active', 'ai': 'active', 'connection': 'active'})

@socketio.on('voice_command')
def handle_voice_command(data):
    command = data.get('command', '')
    print(f"Voice command received: {command}")
    
    add_message('user', command)
    response = process_gui_command_enhanced(command)  # CHANGED: Enhanced function
    add_message('jarvis', response)
    
    emit('assistant_response', {
        'response': response,
        'conversation': conversation_history
    })

@socketio.on('quick_command')
def handle_quick_command(data):
    command = data.get('command', '')
    print(f"Quick command: {command}")
    
    response = process_gui_command_enhanced(command)  # CHANGED: Enhanced function
    add_message('jarvis', response)
    
    emit('assistant_response', {
        'response': response,
        'conversation': conversation_history
    })

def add_message(sender, text):
    message = {
        'id': len(conversation_history) + 1,
        'sender': sender,
        'text': text,
        'time': datetime.datetime.now().strftime("%H:%M")
    }
    conversation_history.append(message)
    
    if len(conversation_history) > 50:
        conversation_history.pop(0)
    
    socketio.emit('new_message', message)

# ==================== NEW: OPENROUTER AI CONFIG ====================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
AI_MODEL = "openai/gpt-3.5-turbo"

# OpenAI client setup
openai.api_key = OPENROUTER_API_KEY
openai.api_base = OPENROUTER_BASE_URL

# ==================== NEW: AI RESPONSE FUNCTION ====================
def get_ai_response(user_query):
    """
    OpenRouter AI का उपयोग करके intelligent response generate करता है
    """
    try:
        print(f"🤖 AI Query Processing: {user_query}")
        
        # System prompt हिंदी में
        system_prompt = """तुम जार्विस हो, एक हिंदी भाषी AI असिस्टेंट। 
        तुम्हारे निम्नलिखित कार्य हैं:
        1. हिंदी में बात करना और उत्तर देना
        2. सरल और समझने योग्य भाषा का प्रयोग करना
        3. मददगार और विनम्र रहना
        4. प्रश्नों का सटीक उत्तर देना
        5. चुटकुले सुनाना, कहानियाँ सुनाना, सलाह देना
        6. गणित के सवाल हल करना
        7. सामान्य ज्ञान के प्रश्नों के उत्तर देना
        
        उत्तर हमेशा हिंदी में देना और संक्षिप्त रखना।"""
        
        # OpenRouter API call
        response = openai.ChatCompletion.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            max_tokens=300,
            temperature=0.7,
            headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "JARVIS Hindi Assistant"
            }
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Check if response is in Hindi, if not translate
        if not any(char in '\u0900-\u097F' for char in ai_response):
            try:
                translate_prompt = f"Translate this to Hindi in a friendly assistant tone: {ai_response}"
                translate_response = openai.ChatCompletion.create(
                    model=AI_MODEL,
                    messages=[{"role": "user", "content": translate_prompt}],
                    max_tokens=200
                )
                ai_response = translate_response.choices[0].message.content.strip()
            except:
                # Fallback translation
                ai_response = "क्षमा करें, मैं इस प्रश्न का हिंदी में उत्तर देने में असमर्थ हूं।"
        
        return ai_response
        
    except Exception as e:
        print(f"❌ AI Error: {e}")
        fallback_responses = [
            "माफ़ करें, मैं इस समय जवाब नहीं दे पा रहा हूं।",
            "कनेक्शन समस्या हो रही है।",
            "कृपया थोड़ी देर बाद पूछें।"
        ]
        return random.choice(fallback_responses)

# ==================== NEW: ENHANCED COMMAND PROCESSOR ====================
def process_gui_command_enhanced(command):
    """
    Enhanced command processor जो AI का उपयोग करता है
    """
    try:
        command_lower = command.lower()
        
        # स्पष्ट commands के लिए conditions
        if any(word in command_lower for word in ['youtube', 'यूट्यूब']):
            return open_youtube_silent()
        
        elif any(word in command_lower for word in ['समय', 'टाइम']):
            return get_time_silent()
        
        elif any(word in command_lower for word in ['तारीख', 'डेट']):
            return get_date_silent()
        
        elif any(word in command_lower for word in ['दिन']):
            return get_day_silent()
        
        elif any(word in command_lower for word in ['मौसम', 'weather']):
            if 'का मौसम' in command_lower:
                city = command_lower.split('का मौसम')[0].strip()
                return weather_report_silent(city)
            return weather_report_silent("Delhi")
        
        elif any(word in command_lower for word in ['खबर', 'न्यूज़']):
            return get_news_fixed()
        
        elif any(word in command_lower for word in ['बैटरी', 'चार्ज']):
            return get_battery_status_silent()
        
        elif any(word in command_lower for word in ['मेमोरी', 'रैम']):
            return get_memory_info_silent()
        
        elif any(word in command_lower for word in ['सिस्टम']):
            return get_system_info_silent()
        
        elif any(word in command_lower for word in ['स्क्रीनशॉट']):
            return take_screenshot_silent()
        
        elif any(word in command_lower for word in ['नोटपैड']):
            return open_notepad_silent()
        
        elif any(word in command_lower for word in ['क्रोम', 'ब्राउज़र']):
            return open_chrome_silent()
        
        elif any(word in command_lower for word in ['वर्ड', 'माइक्रोसॉफ्ट']):
            return open_word_silent()
        
        elif any(word in command_lower for word in ['पेंट']):
            return open_paint_silent()
        
        elif any(word in command_lower for word in ['कैलकुलेटर']):
            return open_calculator_silent()
        
        elif any(word in command_lower for word in ['कमांड', 'सीएमडी']):
            return open_cmd_silent()
        
        elif any(word in command_lower for word in ['व्हाट्सएप', 'whatsapp']):
            return open_whatsapp_silent()
        
        elif any(word in command_lower for word in ['फाइल', 'फोल्डर']):
            return open_explorer_silent()
        
        # Greetings
        elif any(word in command_lower for word in ['नमस्ते', 'हैलो', 'hi', 'hello']):
            greetings = [
                "नमस्ते सर! मैं जार्विस हूं।",
                "राधे राधे! मैं यहां हूं।",
                "नमस्कार! जार्विस आपकी सेवा में।"
            ]
            return random.choice(greetings)
        
        elif any(word in command_lower for word in ['धन्यवाद', 'थैंक्स']):
            return "आपका स्वागत है सर!"
        
        elif any(word in command_lower for word in ['मदद', 'हेल्प']):
            return get_help_text_silent_enhanced()
        
        elif any(word in command_lower for word in ['तुम कौन हो']):
            return "मैं जार्विस हूं, आपका AI सहायक। मैं OpenRouter AI द्वारा संचालित हूं।"
        
        # विशेष AI commands
        elif any(word in command_lower for word in ['जोक', 'चुटकुला', 'जोक सुनाओ', 'चुटकुला सुनाओ', 'जोक सुनाओ', 'जोक बताओ']):
            return get_ai_response("एक फनी हिंदी जोक सुनाओ")
        
        elif any(word in command_lower for word in ['कहानी', 'कहानी सुनाओ', 'स्टोरी']):
            return get_ai_response("एक छोटी सी नैतिक कहानी हिंदी में सुनाओ")
        
        elif any(word in command_lower for word in ['कविता', 'पोएम', 'कविता सुनाओ']):
            return get_ai_response("एक छोटी सी हिंदी कविता सुनाओ")
        
        elif any(word in command_lower for word in ['राशिफल', 'आज का राशिफल']):
            return get_ai_response("आज का राशिफल हिंदी में बताओ")
        
        elif any(word in command_lower for word in ['सलाह', 'सुझाव', 'एडवाइस']):
            return get_ai_response("जीवन की एक अच्छी सलाह हिंदी में दो")
        
        # बाकी सबके लिए AI response
        else:
            return get_ai_response(command)
            
    except Exception as e:
        print(f"❌ Command Error: {e}")
        return "त्रुटि हुई। कृपया दोबारा प्रयास करें।"

# ==================== ORIGINAL FUNCTION (KEPT AS IS) ====================
def process_gui_command(command):
    try:
        command_lower = command.lower()
        
        # सभी commands के लिए conditions
        if 'youtube' in command_lower or 'यूट्यूब' in command_lower:
            return open_youtube_silent()
        elif 'समय' in command_lower:
            return get_time_silent()
        elif 'तारीख' in command_lower or 'डेट' in command_lower:
            return get_date_silent()
        elif 'दिन' in command_lower:
            return get_day_silent()
        elif 'मौसम' in command_lower:
            if 'का मौसम' in command_lower:
                city = command_lower.split('का मौसम')[0].strip()
                return weather_report_silent(city)
            else:
                return weather_report_silent("Delhi")
        elif 'खबर' in command_lower or 'न्यूज़' in command_lower:
            return get_news_fixed()
        elif 'बैटरी' in command_lower or 'चार्ज' in command_lower:
            return get_battery_status_silent()
        elif 'मेमोरी' in command_lower or 'रैम' in command_lower:
            return get_memory_info_silent()
        elif 'सिस्टम' in command_lower or 'कंप्यूटर' in command_lower:
            return get_system_info_silent()
        elif 'स्क्रीनशॉट' in command_lower or 'स्क्रीन' in command_lower:
            return take_screenshot_silent()
        elif 'नोटपैड' in command_lower:
            return open_notepad_silent()
        elif 'क्रोम' in command_lower or 'ब्राउज़र' in command_lower:
            return open_chrome_silent()
        elif 'वर्ड' in command_lower or 'माइक्रोसॉफ्ट' in command_lower:
            return open_word_silent()
        elif 'पेंट' in command_lower:
            return open_paint_silent()
        elif 'कैलकुलेटर' in command_lower:
            return open_calculator_silent()
        elif 'कमांड' in command_lower or 'सीएमडी' in command_lower:
            return open_cmd_silent()
        elif 'व्हाट्सएप' in command_lower or 'whatsapp' in command_lower:
            return open_whatsapp_silent()
        elif 'मैसेज' in command_lower or 'मैसेज भेजो' in command_lower:
            return "WhatsApp मैसेज भेजने के लिए वॉइस कमांड का उपयोग करें"
        elif 'फाइल' in command_lower or 'फोल्डर' in command_lower:
            return open_explorer_silent()
        elif any(word in command_lower for word in ['नमस्ते', 'हैलो', 'hi', 'hello']):
            return "नमस्ते सर! मैं जार्विस हूं।"
        elif 'धन्यवाद' in command_lower or 'थैंक्स' in command_lower:
            return "आपका स्वागत है सर!"
        elif 'मदद' in command_lower or 'हेल्प' in command_lower:
            return get_help_text_silent()
        else:
            return "कृपया वॉइस कमांड का उपयोग करें।"
    except Exception as e:
        print(f"GUI Command Error: {e}")
        return "कमांड प्रोसेस करने में त्रुटि हुई"

# ==================== API KEYS ====================
#  git pr upload krne ke liye
# WEATHER_API_KEY = "e2356146428ff37f65f4abcade97206f"
# es ka use
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


# ==================== VOICE FUNCTIONS ====================

def speak_hindi(text):
    print(f"🤖 जार्विस: {text}")
    
    socketio.emit('assistant_speech', {'text': text})
    
    try:
        tts = gTTS(text=text, lang='hi', slow=False)
        filename = "jarvis_hindi.mp3"
        tts.save(filename)
        playsound.playsound(filename)
        
        time.sleep(0.1)
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass
    except Exception as e:
        print(f"⚠️ Audio Error: {e}")

def speak(text):
    speak_hindi(text)

def listen():
    try:
        r = sr.Recognizer()
        
        with sr.Microphone() as source:
            print("👂 सुन रहा हूँ...")
            r.pause_threshold = 1
            r.energy_threshold = 400
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=8, phrase_time_limit=15)
    
        print("🧠 समझ रहा हूँ...")
        query = r.recognize_google(audio, language='hi-IN')
        print(f"🗣️ आपने कहा: {query}")
        
        socketio.emit('user_speech', {'text': query})
            
        return query.lower()
        
    except sr.UnknownValueError:
        print("🔇 आवाज समझ नहीं आई")
        return "none"
        
    except sr.RequestError:
        print("🌐 इंटरनेट कनेक्शन चेक करें")
        return "none"
        
    except Exception as e:
        print(f"❌ Listen Error: {e}")
        return "none"

# ==================== ACTIVATION ====================
def check_activation(query):
    activation_words = ['hello raj', 'हेलो राज', 'जार्विस', 'ओके जार्विस', 'राज', 'वेक अप', 'जागो']
    
    query_lower = query.lower()
    for word in activation_words:
        if word in query_lower:
            greet = random.choice([
                "जी सर, मैं सुन रहा हूँ। आप क्या चाहते हैं?",
                "राधे राधे! मैं तैयार हूँ सर।",
                "जी बोलिए सर, मैं आपकी सेवा में हूँ।",
                "हाँ सर, मैं यहाँ हूँ। क्या आदेश है?"
            ])
            speak_hindi(greet)
            return True
    return False

# ==================== WISH ME ====================
def wish_me():
    hour = datetime.datetime.now().hour
    day = datetime.datetime.now().strftime("%A")
    
    day_map = {
        'Monday': 'सोमवार',
        'Tuesday': 'मंगलवार', 
        'Wednesday': 'बुधवार',
        'Thursday': 'गुरुवार',
        'Friday': 'शुक्रवार',
        'Saturday': 'शनिवार',
        'Sunday': 'रविवार'
    }
    
    hindi_day = day_map.get(day, day)
    
    if hour < 12:
        time_greet = "शुभ प्रभात सर!"
    elif hour < 18:
        time_greet = "शुभ दोपहर सर!"
    else:
        time_greet = "शुभ संध्या सर!"
    
    greeting = f"राधे राधे! मैं जार्विस आपकी सेवा में हूं। आज {hindi_day} है। {time_greet}"
    
    print(f"🤖 जार्विस: {greeting}")
    speak_hindi(greeting)

# ==================== TIME & DATE FUNCTIONS ====================
def get_time_silent():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    return f"अभी समय है {current_time}"

def get_date_silent():
    today = datetime.datetime.now()
    month_map = {
        'January': 'जनवरी',
        'February': 'फरवरी',
        'March': 'मार्च',
        'April': 'अप्रैल',
        'May': 'मई',
        'June': 'जून',
        'July': 'जुलाई',
        'August': 'अगस्त',
        'September': 'सितंबर',
        'October': 'अक्टूबर',
        'November': 'नवंबर',
        'December': 'दिसंबर'
    }
    month_name = month_map.get(today.strftime("%B"), today.strftime("%B"))
    hindi_date = f"{today.day} {month_name} {today.year}"
    return f"आज की तारीख है {hindi_date}"

def get_day_silent():
    today = datetime.datetime.now().strftime("%A")
    day_map = {
        'Monday': 'सोमवार',
        'Tuesday': 'मंगलवार', 
        'Wednesday': 'बुधवार',
        'Thursday': 'गुरुवार',
        'Friday': 'शुक्रवार',
        'Saturday': 'शनिवार',
        'Sunday': 'रविवार'
    }
    hindi_day = day_map.get(today, today)
    return f"आज {hindi_day} है"

def get_time():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    response = f"अभी समय है {current_time}"
    speak_hindi(response)
    return response

def get_date():
    today = datetime.datetime.now()
    month_map = {
        'January': 'जनवरी',
        'February': 'फरवरी',
        'March': 'मार्च',
        'April': 'अप्रैल',
        'May': 'मई',
        'June': 'जून',
        'July': 'जुलाई',
        'August': 'अगस्त',
        'September': 'सितंबर',
        'October': 'अक्टूबर',
        'November': 'नवंबर',
        'December': 'दिसंबर'
    }
    month_name = month_map.get(today.strftime("%B"), today.strftime("%B"))
    hindi_date = f"{today.day} {month_name} {today.year}"
    response = f"आज की तारीख है {hindi_date}"
    speak_hindi(response)
    return response

def get_day():
    today = datetime.datetime.now().strftime("%A")
    day_map = {
        'Monday': 'सोमवार',
        'Tuesday': 'मंगलवार', 
        'Wednesday': 'बुधवार',
        'Thursday': 'गुरुवार',
        'Friday': 'शुक्रवार',
        'Saturday': 'शनिवार',
        'Sunday': 'रविवार'
    }
    hindi_day = day_map.get(today, today)
    response = f"आज {hindi_day} है"
    speak_hindi(response)
    return response

# ==================== WEATHER FUNCTION ====================
def weather_report_silent(city="Delhi"):
    try:
        city_map = {
            'दिल्ली': 'Delhi',
            'मुंबई': 'Mumbai',
            'चेन्नई': 'Chennai',
            'कोलकाता': 'Kolkata',
            'बैंगलोर': 'Bangalore',
            'हैदराबाद': 'Hyderabad',
            'पुणे': 'Pune',
            'अहमदाबाद': 'Ahmedabad',
            'लखनऊ': 'Lucknow',
            'जयपुर': 'Jaipur'
        }
        
        city_english = city_map.get(city.title(), city)
        
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_english}&appid={WEATHER_API_KEY}&units=metric&lang=hi"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data['cod'] == 200:
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            description = data['weather'][0]['description']
            wind_speed = data['wind']['speed']
            
            weather_info = f"""{city} का मौसम:
तापमान: {temp}°C, महसूस हो रहा: {feels_like}°C
मौसम: {description}
नमी: {humidity}%
हवा की गति: {wind_speed} किमी/घंटा"""
            
            return weather_info
        else:
            return f"शहर '{city}' नहीं मिला।"
    except Exception as e:
        print(f"❌ Weather Error: {e}")
        return "मौसम जानकारी लोड नहीं हो पाई"

def weather_report(city=None):
    try:
        if not city:
            speak_hindi("किस शहर का मौसम जानना चाहते हैं?")
            city_input = listen()
            if city_input == "none":
                city = "Delhi"
                speak_hindi("मैं दिल्ली का मौसम बताता हूं")
            else:
                city = city_input
        else:
            city = city.replace('का मौसम', '').replace('मौसम', '').strip()
            if not city:
                city = "Delhi"
        
        speak_hindi(f"{city} का मौसम ढूंढ रहा हूं...")
        
        city_map = {
            'दिल्ली': 'Delhi',
            'मुंबई': 'Mumbai',
            'चेन्नई': 'Chennai',
            'कोलकाता': 'Kolkata',
            'बैंगलोर': 'Bangalore',
            'हैदराबाद': 'Hyderabad',
            'पुणे': 'Pune',
            'अहमदाबाद': 'Ahmedabad',
            'लखनऊ': 'Lucknow',
            'जयपुर': 'Jaipur'
        }
        
        city_english = city_map.get(city.title(), city)
        
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_english}&appid={WEATHER_API_KEY}&units=metric&lang=hi"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data['cod'] == 200:
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            description = data['weather'][0]['description']
            wind_speed = data['wind']['speed']
            
            speak_hindi(f"{city} का मौसम:")
            speak_hindi(f"तापमान: {temp}°C")
            speak_hindi(f"महसूस हो रहा: {feels_like}°C")
            speak_hindi(f"{description}")
            speak_hindi(f"नमी: {humidity}%")
            speak_hindi(f"हवा की गति: {wind_speed} किमी प्रति घंटा")
            
            return f"{city} का मौसम: {temp}°C, {description}"
        else:
            response = f"शहर '{city}' नहीं मिला।"
            speak_hindi(response)
            return response
    except Exception as e:
        print(f"❌ Weather Error: {e}")
        response = "मौसम जानकारी लोड नहीं हो पाई"
        speak_hindi(response)
        return response

# ==================== NEWS FUNCTION ====================
def get_news_fixed():
    try:
        #  git hub pr push krne ke liye
        # newsapi_key = "cca940cf9d5f49628f9d2e6c886e7e8a"
        newsapi_key = os.getenv("NEWS_API_KEY")

        
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={newsapi_key}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            news = response.json()
            
            if news.get('status') == 'ok' and news.get('articles'):
                headlines = []
                for i in range(min(5, len(news['articles']))):
                    title = news['articles'][i]['title']
                    clean_title = re.sub(r'[^\w\s.,!?-]', '', title)
                    headlines.append(f"{i+1}. {clean_title}")
                
                return "\n".join(headlines)
        
        return get_backup_news()
            
    except Exception as e:
        print(f"❌ News Error: {e}")
        return get_backup_news()

def get_backup_news():
    day = datetime.datetime.now().strftime("%A")
    
    news_sets = {
        'Monday': [
            "सोमवार: भारत सरकार ने नई आर्थिक योजनाओं की घोषणा की",
            "शेयर बाजार में सप्ताह की शुरुआत में तेजी",
            "मौसम विभाग ने उत्तरी भारत में ठंड की चेतावनी जारी की",
            "शिक्षा मंत्रालय नई शिक्षा नीति पर बैठक आयोजित करेगा",
            "खेल: आईपीएल की तैयारियां शुरू"
        ],
        'Tuesday': [
            "मंगलवार: राष्ट्रीय सुरक्षा पर विशेष बैठक",
            "बैंकों ने नई ब्याज दरों की घोषणा की",
            "किसानों के लिए नई सब्सिडी योजना",
            "स्वास्थ्य मंत्रालय ने नई स्वास्थ्य योजना शुरू की",
            "क्रिकेट: भारतीय टीम की टेस्ट सीरीज की तैयारी"
        ],
        'Wednesday': [
            "बुधवार: तकनीकी शिक्षा पर सम्मेलन",
            "मुद्रास्फीति दर में गिरावट की उम्मीद",
            "केंद्र सरकार ने बुनियादी ढांचा परियोजनाओं को मंजूरी दी",
            "पर्यावरण मंत्रालय ने वृक्षारोपण अभियान शुरू किया",
            "फुटबॉल: राष्ट्रीय लीग के मैच आज"
        ],
        'Thursday': [
            "गुरुवार: विदेश नीति पर चर्चा",
            "उद्योग जगत के लिए नई नीतियां",
            "कृषि क्षेत्र के लिए नई तकनीकी सहायता",
            "युवा उद्यमियों के लिए स्टार्टअप फंड",
            "टेनिस: राष्ट्रीय टूर्नामेंट की शुरुआत"
        ],
        'Friday': [
            "शुक्रवार: सप्ताहांत से पहले शेयर बाजार में उतार-चढ़ाव",
            "पेट्रोल-डीजल की कीमतों में बदलाव",
            "सप्ताहांत के लिए मौसम का पूर्वानुमान",
            "सप्ताहांत में होने वाले सांस्कृतिक कार्यक्रम",
            "खेल: सप्ताहांत के मैचों की तैयारी"
        ],
        'Saturday': [
            "शनिवार: सप्ताहांत बाजार में गहमागहमी",
            "सप्ताहांत के लिए पर्यटन स्थलों पर भीड़",
            "सप्ताहांत में होने वाले शादी समारोह",
            "सप्ताहांत फिल्मों का रिलीज",
            "खेल: आज के प्रमुख मैच"
        ],
        'Sunday': [
            "रविवार: आज का मुख्य समाचार",
            "सप्ताह की समीक्षा और आगामी सप्ताह की योजनाएं",
            "रविवार बाजार की स्थिति",
            "आज के धार्मिक और सांस्कृतिक कार्यक्रम",
            "खेल: कल के मैचों की तैयारी"
        ]
    }
    
    today_news = news_sets.get(day, news_sets['Monday'])
    
    formatted_news = []
    for i, news in enumerate(today_news, 1):
        formatted_news.append(f"{i}. {news}")
    
    return "\n".join(formatted_news)

def news_headlines():
    try:
        speak_hindi("आज की ताजा खबरें ला रहा हूं...")
        
        news_text = get_news_fixed()
        news_lines = news_text.split('\n')
        
        for i in range(min(3, len(news_lines))):
            line = news_lines[i]
            if '. ' in line:
                _, news_content = line.split('. ', 1)
                speak_hindi(news_content)
            else:
                speak_hindi(line)
            time.sleep(1.5)
        
        speak_hindi("ये थीं आज की मुख्य खबरें।")
        return news_text
            
    except Exception as e:
        print(f"❌ News Error: {e}")
        response = "खबरें लोड नहीं हो पाईं"
        speak_hindi(response)
        return response

# ==================== SYSTEM INFO FUNCTIONS ====================

def get_battery_status_silent():
    """बैटरी स्टेटस बताता है"""
    try:
        battery = psutil.sensors_battery()
        
        if battery:
            percent = battery.percent
            plugged = battery.power_plugged
            time_left = battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "अनंत"
            
            if time_left != "अनंत":
                hours = time_left // 3600
                minutes = (time_left % 3600) // 60
            
            if plugged:
                status = "चार्जर लगा हुआ है"
                info = f"बैटरी: {percent}% चार्ज है। {status}"
            else:
                status = "चार्जर नहीं लगा है"
                if time_left != "अनंत":
                    info = f"बैटरी: {percent}% चार्ज है। {status}\nसमय बचा: {hours} घंटे {minutes} मिनट"
                else:
                    info = f"बैटरी: {percent}% चार्ज है। {status}"
            return info
        else:
            return "बैटरी जानकारी उपलब्ध नहीं है (डेस्कटॉप कंप्यूटर)"
    except Exception as e:
        print(f"❌ Battery Error: {e}")
        return "बैटरी जानकारी लोड नहीं हो पाई"

def get_battery_status():
    """Voice के लिए बैटरी स्टेटस"""
    try:
        battery = psutil.sensors_battery()
        
        if battery:
            percent = battery.percent
            plugged = battery.power_plugged
            
            if plugged:
                response = f"बैटरी {percent}% चार्ज है। चार्जर लगा हुआ है।"
            else:
                response = f"बैटरी {percent}% चार्ज है। चार्जर नहीं लगा है।"
            
            speak_hindi(response)
            return response
        else:
            response = "बैटरी जानकारी उपलब्ध नहीं है। यह डेस्कटॉप कंप्यूटर हो सकता है।"
            speak_hindi(response)
            return response
    except Exception as e:
        print(f"❌ Battery Error: {e}")
        response = "बैटरी जानकारी लोड नहीं हो पाई"
        speak_hindi(response)
        return response

def get_memory_info_silent():
    """मेमोरी इन्फो बताता है"""
    try:
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024**3)
        available_gb = memory.available / (1024**3)
        used_gb = memory.used / (1024**3)
        percent_used = memory.percent
        
        info = f"""मेमोरी स्थिति:
कुल मेमोरी: {total_gb:.2f} GB
उपयोग में: {used_gb:.2f} GB ({percent_used}%)
उपलब्ध: {available_gb:.2f} GB"""
        
        return info
    except Exception as e:
        print(f"❌ Memory Error: {e}")
        return "मेमोरी जानकारी लोड नहीं हो पाई"

def get_memory_info():
    """Voice के लिए मेमोरी इन्फो"""
    try:
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024**3)
        used_gb = memory.used / (1024**3)
        percent_used = memory.percent
        
        response = f"कुल मेमोरी {total_gb:.1f} जीबी है। {percent_used}% उपयोग में है।"
        speak_hindi(response)
        return response
    except Exception as e:
        print(f"❌ Memory Error: {e}")
        response = "मेमोरी जानकारी लोड नहीं हो पाई"
        speak_hindi(response)
        return response

def get_system_info_silent():
    """सिस्टम इन्फो बताता है"""
    try:
        system_info = platform.system()
        node_name = platform.node()
        release = platform.release()
        version = platform.version()
        processor = platform.processor()
        
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        info = f"""सिस्टम जानकारी:
ऑपरेटिंग सिस्टम: {system_info}
सिस्टम नाम: {node_name}
वर्जन: {release}
प्रोसेसर: {processor[:50]}...
CPU कोर: {cpu_count}
CPU उपयोग: {cpu_percent}%"""
        
        return info
    except Exception as e:
        print(f"❌ System Info Error: {e}")
        return "सिस्टम जानकारी लोड नहीं हो पाई"

def get_system_info():
    """Voice के लिए सिस्टम इन्फो"""
    try:
        system_info = platform.system()
        node_name = platform.node()
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        response = f"सिस्टम: {system_info}, नाम: {node_name}, CPU कोर: {cpu_count}, CPU उपयोग: {cpu_percent}%"
        speak_hindi(response)
        return response
    except Exception as e:
        print(f"❌ System Info Error: {e}")
        response = "सिस्टम जानकारी लोड नहीं हो पाई"
        speak_hindi(response)
        return response

# ==================== SCREENSHOT FUNCTION ====================

def take_screenshot_silent():
    """स्क्रीनशॉट लेता है"""
    try:
        screenshot = pyautogui.screenshot()
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        screenshot.save(filename)
        return f"स्क्रीनशॉट ले लिया गया है: {filename}"
    except Exception as e:
        print(f"❌ Screenshot Error: {e}")
        return "स्क्रीनशॉट नहीं ले पाया"

def take_screenshot():
    """Voice के लिए स्क्रीनशॉट"""
    try:
        speak_hindi("स्क्रीनशॉट ले रहा हूं...")
        screenshot = pyautogui.screenshot()
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        screenshot.save(filename)
        
        response = f"स्क्रीनशॉट ले लिया गया है, फाइल नाम है: {filename}"
        speak_hindi(response)
        return response
    except Exception as e:
        print(f"❌ Screenshot Error: {e}")
        response = "स्क्रीनशॉट नहीं ले पाया"
        speak_hindi(response)
        return response

# ==================== APPLICATION FUNCTIONS ====================

def open_notepad_silent():
    """नोटपैड खोलता है"""
    try:
        os.system("start notepad")
        return "नोटपैड खोल रहा हूं..."
    except Exception as e:
        print(f"❌ Notepad Error: {e}")
        return "नोटपैड नहीं खोल पाया"

def open_notepad():
    try:
        speak_hindi("नोटपैड खोल रहा हूं...")
        os.system("start notepad")
        time.sleep(1)
        speak_hindi("नोटपैड खुल गया")
        return "नोटपैड खुल गया"
    except Exception as e:
        print(f"❌ Notepad Error: {e}")
        speak_hindi("नोटपैड नहीं खोल पाया")
        return "नोटपैड नहीं खोल पाया"

def open_chrome_silent():
    """क्रोम ब्राउज़र खोलता है"""
    try:
        os.system("start chrome")
        return "क्रोम ब्राउज़र खोल रहा हूं..."
    except Exception as e:
        print(f"❌ Chrome Error: {e}")
        return "क्रोम नहीं खोल पाया"

def open_chrome():
    try:
        speak_hindi("क्रोम ब्राउज़र खोल रहा हूं...")
        os.system("start chrome")
        time.sleep(2)
        speak_hindi("क्रोम खुल गया")
        return "क्रोम खुल गया"
    except Exception as e:
        print(f"❌ Chrome Error: {e}")
        speak_hindi("क्रोम नहीं खोल पाया")
        return "क्रोम नहीं खोल पाया"

def open_word_silent():
    """MS Word खोलता है"""
    try:
        os.system("start winword")
        return "माइक्रोसॉफ्ट वर्ड खोल रहा हूं..."
    except Exception as e:
        print(f"❌ Word Error: {e}")
        return "वर्ड नहीं खोल पाया"

def open_word():
    try:
        speak_hindi("माइक्रोसॉफ्ट वर्ड खोल रहा हूं...")
        os.system("start winword")
        time.sleep(2)
        speak_hindi("वर्ड खुल गया")
        return "वर्ड खुल गया"
    except Exception as e:
        print(f"❌ Word Error: {e}")
        speak_hindi("वर्ड नहीं खोल पाया")
        return "वर्ड नहीं खोल पाया"

def open_paint_silent():
    """पेंट खोलता है"""
    try:
        os.system("start mspaint")
        return "पेंट खोल रहा हूं..."
    except Exception as e:
        print(f"❌ Paint Error: {e}")
        return "पेंट नहीं खोल पाया"

def open_paint():
    try:
        speak_hindi("पेंट खोल रहा हूं...")
        os.system("start mspaint")
        time.sleep(1)
        speak_hindi("पेंट खुल गया")
        return "पेंट खुल गया"
    except Exception as e:
        print(f"❌ Paint Error: {e}")
        speak_hindi("पेंट नहीं खोल पाया")
        return "पेंट नहीं खोल पाया"

def open_calculator_silent():
    """कैलकुलेटर खोलता है"""
    try:
        os.system("start calc")
        return "कैलकुलेटर खोल रहा हूं..."
    except Exception as e:
        print(f"❌ Calculator Error: {e}")
        return "कैलकुलेटर नहीं खोल पाया"

def open_calculator():
    try:
        speak_hindi("कैलकुलेटर खोल रहा हूं...")
        os.system("start calc")
        time.sleep(1)
        speak_hindi("कैलकुलेटर खुल गया")
        return "कैलकुलेटर खुल गया"
    except Exception as e:
        print(f"❌ Calculator Error: {e}")
        speak_hindi("कैलकुलेटर नहीं खोल पाया")
        return "कैलकुलेटर नहीं खोल पाया"

def open_cmd_silent():
    """कमांड प्रॉम्प्ट खोलता है"""
    try:
        os.system("start cmd")
        return "कमांड प्रॉम्प्ट खोल रहा हूं..."
    except Exception as e:
        print(f"❌ CMD Error: {e}")
        return "कमांड प्रॉम्प्ट नहीं खोल पाया"

def open_cmd():
    try:
        speak_hindi("कमांड प्रॉम्प्ट खोल रहा हूं...")
        os.system("start cmd")
        time.sleep(1)
        speak_hindi("कमांड प्रॉम्प्ट खुल गया")
        return "कमांड प्रॉम्प्ट खुल गया"
    except Exception as e:
        print(f"❌ CMD Error: {e}")
        speak_hindi("कमांड प्रॉम्प्ट नहीं खोल पाया")
        return "कमांड प्रॉम्प्ट नहीं खोल पाया"

def open_explorer_silent():
    """फाइल एक्सप्लोरर खोलता है"""
    try:
        os.system("start explorer")
        return "फाइल एक्सप्लोरर खोल रहा हूं..."
    except Exception as e:
        print(f"❌ Explorer Error: {e}")
        return "फाइल एक्सप्लोरर नहीं खोल पाया"

def open_explorer():
    try:
        speak_hindi("फाइल एक्सप्लोरर खोल रहा हूं...")
        os.system("start explorer")
        time.sleep(1)
        speak_hindi("फाइल एक्सप्लोरर खुल गया")
        return "फाइल एक्सप्लोरर खुल गया"
    except Exception as e:
        print(f"❌ Explorer Error: {e}")
        speak_hindi("फाइल एक्सप्लोरर नहीं खोल पाया")
        return "फाइल एक्सप्लोरर नहीं खोल पाया"

# ==================== WHATSAPP FUNCTIONS ====================

def open_whatsapp_silent():
    """WhatsApp Web खोलता है"""
    try:
        webbrowser.open("https://web.whatsapp.com")
        return "WhatsApp वेब खोल रहा हूं..."
    except Exception as e:
        print(f"❌ WhatsApp Error: {e}")
        return "WhatsApp नहीं खोल पाया"

def open_whatsapp():
    try:
        speak_hindi("WhatsApp खोल रहा हूं...")
        webbrowser.open("https://web.whatsapp.com")
        time.sleep(2)
        speak_hindi("WhatsApp वेब खुल गया")
        return "WhatsApp खुल गया"
    except Exception as e:
        print(f"❌ WhatsApp Error: {e}")
        speak_hindi("WhatsApp नहीं खोल पाया")
        return "WhatsApp नहीं खोल पाया"

def send_whatsapp_message():
    """WhatsApp मैसेज भेजता है"""
    try:
        speak_hindi("किसे WhatsApp मैसेज भेजना है? फोन नंबर बताएं।")
        phone_input = listen()
        
        if phone_input == "none":
            speak_hindi("फोन नंबर समझ नहीं आया")
            return "फोन नंबर समझ नहीं आया"
        
        phone_number = ''.join(filter(str.isdigit, phone_input))
        
        speak_hindi("क्या मैसेज भेजना है?")
        message = listen()
        
        if message == "none":
            speak_hindi("मैसेज समझ नहीं आया")
            return "मैसेज समझ नहीं आया"
        
        if len(phone_number) == 10:
            phone_number = "+91" + phone_number
        
        whatsapp_url = f"https://web.whatsapp.com/send?phone={phone_number}&text={requests.utils.quote(message)}"
        webbrowser.open(whatsapp_url)
        
        response = f"WhatsApp खोल रहा हूं {phone_number} पर मैसेज भेजने के लिए। 10 सेकेंड बाद सेंड क्लिक करें।"
        speak_hindi(response)
        
        return response
        
    except Exception as e:
        print(f"❌ WhatsApp Message Error: {e}")
        response = "WhatsApp मैसेज नहीं भेज पाया"
        speak_hindi(response)
        return response

# ==================== YOUTUBE FUNCTION ====================
def open_youtube_silent():
    try:
        youtube_url = "https://www.youtube.com"
        webbrowser.open(youtube_url)
        os.system(f"start {youtube_url}")
        return "YouTube खोल रहा हूं... YouTube खुल गया!"
    except Exception as e:
        print(f"YouTube Error: {e}")
        return "YouTube नहीं खोल पाया"

def open_youtube():
    try:
        speak_hindi("YouTube खोल रहा हूं...")
        youtube_url = "https://www.youtube.com"
        webbrowser.open(youtube_url)
        os.system(f"start {youtube_url}")
        time.sleep(2)
        speak_hindi("YouTube खुल गया!")
        return "YouTube खुल गया"
    except Exception as e:
        print(f"YouTube Error: {e}")
        speak_hindi("YouTube नहीं खोल पाया")
        return "YouTube नहीं खोल पाया"

# ==================== NEW: ENHANCED HELP FUNCTION ====================
def get_help_text_silent_enhanced():
    help_text = """मैं ये सब कर सकता हूं:

🎯 **BASIC COMMANDS:**
• YouTube, Chrome, WhatsApp खोलना
• नोटपैड, वर्ड, पेंट, कैलकुलेटर खोलना
• समय, तारीख, दिन बताना
• मौसम बताना
• खबरें सुनाना
• सिस्टम जानकारी देना

🧠 **AI FEATURES (OpenRouter):**
• किसी भी प्रश्न का उत्तर
• गणित के सवाल हल करना
• सामान्य ज्ञान की जानकारी
• चुटकुले सुनाना
• उपयोगी सलाह देना
• अनुवाद करना
• कहानियाँ सुनाना
• कविताएँ सुनाना
• राशिफल बताना

💬 **EXAMPLES:**
• "भारत की राजधानी क्या है?"
• "२५ का वर्ग क्या है?"
• "एक चुटकुला सुनाओ"
• "आज का राशिफल बताओ"
• "एक कहानी सुनाओ"
• "कविता सुनाओ"
• "सलाह दो"

कुछ भी पूछिए!"""
    return help_text

# ==================== ORIGINAL HELP FUNCTION (KEPT AS IS) ====================
def get_help_text_silent():
    help_text = """मैं ये सब कर सकता हूं:
1. YouTube, Chrome, WhatsApp खोलना
2. नोटपैड, वर्ड, पेंट, कैलकुलेटर, कमांड प्रॉम्प्ट खोलना
3. समय, तारीख, दिन बताना
4. मौसम बताना (किसी भी शहर का)
5. खबरें सुनाना
6. बैटरी स्टेटस बताना
7. मेमोरी और सिस्टम जानकारी देना
8. स्क्रीनशॉट लेना
9. फाइल एक्सप्लोरर खोलना
10. WhatsApp मैसेज भेजना"""
    return help_text

def get_help():
    help_text = """मैं ये सब कर सकता हूं:
1. YouTube, Chrome, WhatsApp खोल सकता हूं
2. नोटपैड, वर्ड, पेंट, कैलकुलेटर खोल सकता हूं
3. समय, तारीख, दिन बता सकता हूं
4. मौसम बता सकता हूं
5. खबरें सुना सकता हूं
6. बैटरी स्टेटस बता सकता हूं
7. स्क्रीनशॉट ले सकता हूं
8. WhatsApp मैसेज भेज सकता हूं"""
    
    speak_hindi(help_text)
    return "मदद की जानकारी दी गई"

# ==================== MAIN PROGRAM ====================

def main():
    print("""
    ╔══════════════════════════════════════════════════╗
    ║         जार्विस - हिंदी वॉइस असिस्टेंट + AI       ║
    ║         VERSION 6.0 - AI ENHANCED              ║
    ║         ALL FEATURES + OPENROUTER AI          ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    print("🚀 जार्विस AI मोड में शुरू हो रहा है...")
    
    wish_me()
    
    print("\n" + "="*60)
    print("🎤 Say 'Hello Raj' or 'जार्विस' to activate")
    print("🎮 GUI: http://localhost:5000")
    print("🧠 AI: OpenRouter Powered - Ask Anything!")
    print("📋 Available Commands: All Features + AI")
    print("="*60 + "\n")
    
    is_active = False
    
    while True:
        query = listen()
        
        if query == "none":
            if not is_active:
                continue
            speak_hindi("कुछ और बताएं?")
            continue
        
        # ACTIVATION CHECK
        if not is_active:
            if check_activation(query):
                is_active = True
            continue
        
        # EXIT COMMANDS
        if any(word in query for word in ['बंद करो', 'रुको', 'अलविदा', 'बाय', 'स्टॉप']):
            speak_hindi("अलविदा सर! राधे राधे!")
            break
        
        # TIME COMMANDS
        elif any(word in query for word in ['समय', 'टाइम', 'क्या समय हुआ']):
            get_time()
            continue
        
        # DATE COMMANDS
        elif any(word in query for word in ['तारीख', 'डेट', 'क्या तारीख है']):
            get_date()
            continue
        
        # DAY COMMANDS
        elif any(word in query for word in ['दिन', 'क्या दिन है', 'आज कौन सा दिन']):
            get_day()
            continue
        
        # YOUTUBE COMMAND
        elif 'यूट्यूब' in query or 'youtube' in query:
            open_youtube()
            continue
        
        # WEATHER COMMAND
        elif 'मौसम' in query or 'weather' in query:
            if 'का मौसम' in query:
                city = query.split('का मौसम')[0].strip()
                weather_report(city)
            else:
                weather_report()
            continue
        
        # NEWS COMMAND
        elif any(word in query for word in ['खबर', 'न्यूज़', 'समाचार', 'news']):
            news_headlines()
            continue
        
        # BATTERY COMMAND
        elif any(word in query for word in ['बैटरी', 'चार्ज', 'बैटरी स्टेटस', 'चार्जिंग']):
            get_battery_status()
            continue
        
        # MEMORY COMMAND
        elif any(word in query for word in ['मेमोरी', 'रैम', 'मेमोरी कितनी है']):
            get_memory_info()
            continue
        
        # SYSTEM INFO COMMAND
        elif any(word in query for word in ['सिस्टम', 'कंप्यूटर', 'सिस्टम जानकारी']):
            get_system_info()
            continue
        
        # SCREENSHOT COMMAND
        elif any(word in query for word in ['स्क्रीनशॉट', 'स्क्रीन शॉट', 'स्क्रीन कैप्चर']):
            take_screenshot()
            continue
        
        # NOTEPAD COMMAND
        elif 'नोटपैड' in query or 'notepad' in query:
            open_notepad()
            continue
        
        # CHROME COMMAND
        elif any(word in query for word in ['क्रोम', 'ब्राउज़र', 'ब्राउजर', 'गूगल']):
            open_chrome()
            continue
        
        # WORD COMMAND
        elif any(word in query for word in ['वर्ड', 'माइक्रोसॉफ्ट', 'एमएस वर्ड']):
            open_word()
            continue
        
        # PAINT COMMAND
        elif 'पेंट' in query or 'paint' in query:
            open_paint()
            continue
        
        # CALCULATOR COMMAND
        elif 'कैलकुलेटर' in query or 'calculator' in query:
            open_calculator()
            continue
        
        # CMD COMMAND
        elif any(word in query for word in ['कमांड', 'सीएमडी', 'कमांड प्रॉम्प्ट']):
            open_cmd()
            continue
        
        # FILE EXPLORER COMMAND
        elif any(word in query for word in ['फाइल', 'फोल्डर', 'एक्सप्लोरर']):
            open_explorer()
            continue
        
        # WHATSAPP COMMANDS
        elif 'व्हाट्सएप' in query or 'whatsapp' in query:
            if 'मैसेज' in query or 'भेजो' in query or 'मेसेज' in query:
                send_whatsapp_message()
            else:
                open_whatsapp()
            continue
        
        # GREETINGS
        elif any(word in query for word in ['नमस्ते', 'हैलो', 'कैसे हो', 'hi', 'hello']):
            responses = ["नमस्ते सर! मैं कैसे मदद कर सकता हूं?", "राधे राधे! मैं ठीक हूं, आप बताएं?"]
            speak_hindi(random.choice(responses))
            continue
        
        elif 'तुम कौन हो' in query:
            speak_hindi("मैं जार्विस हूं, आपका AI असिस्टेंट! OpenRouter AI द्वारा संचालित। राधे राधे!")
            continue
        
        elif 'धन्यवाद' in query or 'थैंक्स' in query:
            speak_hindi("आपका स्वागत है सर!")
            continue
        
        elif 'मदद' in query or 'हेल्प' in query:
            get_help()
            continue
        
        # ==================== NEW AI COMMANDS ====================
        # जोक / चुटकुला commands
        elif any(word in query for word in ['जोक', 'चुटकुला', 'जोक सुनाओ', 'चुटकुला सुनाओ', 'जोक सुनाओ', 'जोक बताओ', 'मजाक']):
            speak_hindi("एक फनी जोक सुनाता हूं...")
            ai_response = get_ai_response("एक फनी हिंदी जोक सुनाओ")
            speak_hindi(ai_response)
            continue
        
        # कहानी commands
        elif any(word in query for word in ['कहानी', 'कहानी सुनाओ', 'स्टोरी', 'स्टोरी सुनाओ']):
            speak_hindi("एक नैतिक कहानी सुनाता हूं...")
            ai_response = get_ai_response("एक छोटी सी नैतिक कहानी हिंदी में सुनाओ")
            speak_hindi(ai_response)
            continue
        
        # कविता commands
        elif any(word in query for word in ['कविता', 'पोएम', 'कविता सुनाओ', 'पोएम सुनाओ']):
            speak_hindi("एक छोटी सी कविता सुनाता हूं...")
            ai_response = get_ai_response("एक छोटी सी हिंदी कविता सुनाओ")
            speak_hindi(ai_response)
            continue
        
        # राशिफल commands
        elif any(word in query for word in ['राशिफल', 'आज का राशिफल', 'राशिफल बताओ']):
            speak_hindi("आज का राशिफल बताता हूं...")
            ai_response = get_ai_response("आज का राशिफल हिंदी में बताओ")
            speak_hindi(ai_response)
            continue
        
        # सलाह commands
        elif any(word in query for word in ['सलाह', 'सुझाव', 'एडवाइस', 'सलाह दो']):
            speak_hindi("एक अच्छी सलाह देता हूं...")
            ai_response = get_ai_response("जीवन की एक अच्छी सलाह हिंदी में दो")
            speak_hindi(ai_response)
            continue
        
        # गणित commands
        elif any(word in query for word in ['गणित', 'कैलकुलेट', 'हिसाब', 'जोड़', 'घटाव', 'गुणा', 'भाग']):
            speak_hindi("गणित का सवाल हल करता हूं...")
            ai_response = get_ai_response(query)
            speak_hindi(ai_response)
            continue
        
        # अनुवाद commands
        elif any(word in query for word in ['अनुवाद', 'ट्रांसलेट', 'अंग्रेजी में', 'हिंदी में']):
            speak_hindi("अनुवाद करता हूं...")
            ai_response = get_ai_response(query)
            speak_hindi(ai_response)
            continue
        
        # बाकी सभी unknown commands के लिए AI response
        else:
            speak_hindi("समझ रहा हूं...")
            ai_response = get_ai_response(query)
            speak_hindi(ai_response)
            continue

# ==================== STARTUP FUNCTION ====================
def start_jarvis():
    print("\n🔍 Checking libraries...")
    
    required_libs = [
        ('speechrecognition', 'speech_recognition'),
        ('gtts', 'gtts'),
        ('playsound', 'playsound'),
        ('requests', 'requests'),
        ('pyautogui', 'pyautogui'),
        ('psutil', 'psutil'),
        ('flask', 'flask'),
        ('flask-socketio', 'flask_socketio'),
        ('openai', 'openai')  # NEW: OpenAI/OpenRouter library
    ]
    
    for pip_name, import_name in required_libs:
        try:
            __import__(import_name)
            print(f"✅ {pip_name}: OK")
        except ImportError:
            print(f"⚠️  Installing {pip_name}...")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                print(f"✅ {pip_name}: Installed")
            except:
                print(f"❌ {pip_name}: Failed to install")
    
    print("\n" + "="*60)
    print("🌐 GUI: http://localhost:5000")
    print("🎤 Voice: Say 'Hello Raj' or 'जार्विस'")
    print("🧠 AI: OpenRouter Powered")
    print("📋 All Features: Available + AI")
    print("="*60 + "\n")
    # Git hub pr push krne ke liye

    # # Check API key
    # if OPENROUTER_API_KEY == "
    #     print("\n⚠️  WARNING: OpenRouter API Key not set!")
    #     print("Get free API key from: https://openrouter.ai/keys")
    #     print("Then update line 48 in code with your actual key")
    #     print("\nRunning in basic mode without AI...\n")
    # else:
    #     print("✅ OpenRouter API Key: Configured")

    #  new code
    # Check API key - Get from environment variable
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("\n⚠️  WARNING: OpenRouter API Key not set!")
    print("1. Create a .env file in the project root")
    print("2. Add: OPENROUTER_API_KEY=your_actual_api_key_here")
    print("3. Get free API key from: https://openrouter.ai/keys")
    print("\nRunning in basic mode without AI...\n")
else:
    print("✅ OpenRouter API Key: Configured")
    
    time.sleep(2)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 प्रोग्राम बंद किया जा रहा है...")
        speak_hindi("राधे राधे! अलविदा सर!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        speak_hindi("प्रोग्राम में त्रुटि हुई")

# ==================== PROGRAM START ====================
if __name__ == "__main__":
    # Start GUI in separate thread
    def start_gui():
        try:
            socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
        except Exception as e:
            print(f"GUI Error: {e}")
    
    gui_thread = threading.Thread(target=start_gui, daemon=True)
    gui_thread.start()
    
    time.sleep(2)
    
    start_jarvis()