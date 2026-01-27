# 19
# Для сборки в APK потребуются: python3, kivy, requests, certifi
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window
import requests
import threading
import certifi # Важно для работы интернета в APK

Window.softinput_mode = "below_target"
API_KEY = "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".strip()
VERSION = "19.0"

state = {"mood": "обычный", "theme": "light", "history": []}

class MessageBubble(BoxLayout):
    def __init__(self, text, side, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, padding=(12, 10), **kwargs)
        is_ai = (side == 'left')
        bg = (0.9, 0.94, 1, 1) if not is_ai else (0.93, 0.93, 0.93, 1)
        txt_col = (0.1, 0.1, 0.1, 1)

        self.btn = Button(
            text=text, markup=True, size_hint=(None, None), 
            color=txt_col, font_size='16sp', background_normal='',
            background_color=(0,0,0,0), halign='left', padding=(18, 14)
        )
        self.btn.text_size = (Window.width * 0.75, None)
        self.btn.bind(texture_size=self.update_size)
        
        with self.btn.canvas.before:
            Color(*bg)
            self.rect = RoundedRectangle(radius=[20, 20, 5, 20] if not is_ai else [20, 20, 20, 5])
        self.btn.bind(pos=lambda i,v: setattr(self.rect, 'pos', i.pos), size=lambda i,v: setattr(self.rect, 'size', i.size))
        
        if side == 'right':
            self.add_widget(BoxLayout(size_hint_x=1)); self.add_widget(self.btn)
            self.pos_hint = {'right': 0.98}
        else:
            self.add_widget(self.btn); self.pos_hint = {'x': 0.02}

    def update_size(self, instance, size):
        instance.size = size
        self.height = size[1] + 35

class ChatApp(App):
    def build(self):
        self.title = f"AI JOPATI v{VERSION}"
        root = BoxLayout(orientation='vertical')
        Window.clearcolor = (0.98, 0.98, 1, 1)

        # HEADER
        header = BoxLayout(size_hint_y=None, height=70, padding=10, spacing=10)
        with header.canvas.before:
            Color(0.1, 0.4, 0.9, 1)
            self.h_rect = RoundedRectangle()
        header.bind(pos=lambda i,v: setattr(self.h_rect, 'pos', i.pos), size=lambda i,v: setattr(self.h_rect, 'size', i.size))

        btn_clr = Button(text='CLR', size_hint_x=None, width=70, background_color=(1,1,1,0.2))
        btn_clr.bind(on_release=lambda x: self.chat_list.clear_widgets())
        
        title_lbl = Label(text=f"JOPATI {VERSION}", bold=True)
        
        btn_upd = Button(text='UPD', size_hint_x=None, width=70, background_color=(1,1,1,0.2))
        btn_upd.bind(on_release=self.check_updates)

        header.add_widget(btn_clr); header.add_widget(title_lbl); header.add_widget(btn_upd)
        root.add_widget(header)

        # CHAT
        self.scroll = ScrollView(); self.chat_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15, padding=12)
        self.chat_list.bind(minimum_height=self.chat_list.setter('height'))
        self.scroll.add_widget(self.chat_list); root.add_widget(self.scroll)

        # INPUT
        input_area = BoxLayout(size_hint_y=None, height=90, padding=10, spacing=10)
        self.entry = TextInput(hint_text='Напиши...', multiline=False, font_size='18sp')
        btn_send = Button(text='>>', size_hint_x=None, width=80, background_color=(0.1, 0.4, 0.9, 1))
        btn_send.bind(on_release=self.process_send)
        
        input_area.add_widget(self.entry); input_area.add_widget(btn_send)
        root.add_widget(input_area)
        
        return root

    def check_updates(self, *args):
        # Здесь в будущем будет ссылка на твой файл с версией
        popup = Popup(title='Обновление', content=Label(text="У вас самая новая версия!"), size_hint=(0.7, 0.3))
        popup.open()

    def process_send(self, instance):
        text = self.entry.text.strip()
        if not text: return
        self.chat_list.add_widget(MessageBubble(text=text, side='right'))
        self.entry.text = ""
        threading.Thread(target=self.get_ai_answer, args=(text,)).start()

    def get_ai_answer(self, text):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                             headers={"Authorization": f"Bearer {API_KEY}"}, 
                             json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": text}]}, 
                             timeout=10, verify=certifi.where())
            ans = r.json()['choices'][0]['message']['content']
        except: ans = "Нет интернета..."
        Clock.schedule_once(lambda dt: self.chat_list.add_widget(MessageBubble(text=ans, side='left')))

if __name__ == '__main__':
    ChatApp().run()
