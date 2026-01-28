# 33 (FINAL STABLE APP VERSION)
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
import requests
import threading

# Фикс для мобильных устройств
Window.softinput_mode = "pan" 

API_KEY = "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".strip()

state = {
    "mood": "обычный", 
    "theme": "light", 
    "lang": "Русский",
    "mode": "Быстрые",
    "chat_name": "Новый чат",
    "history": []
}

class MessageBubble(BoxLayout):
    def __init__(self, text, side, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.padding = (15, 8)
        
        is_user = (side == 'left')
        is_system = (side == 'system')
        
        clean_text = text.replace("**", "[b]").replace("__", "[i]")
        
        if state["theme"] == "light":
            theme_bg = (1, 1, 1, 1)
            user_bg = (0.24, 0.45, 1, 1)
            ai_bg = (0.95, 0.96, 0.98, 1)
            txt_user = (1, 1, 1, 1)
            txt_ai = (0.1, 0.1, 0.1, 1)
            sys_txt_col = (0.5, 0.5, 0.5, 1)
        else:
            theme_bg = (0.05, 0.05, 0.07, 1)
            user_bg = (0.15, 0.3, 0.8, 1)
            ai_bg = (0.12, 0.12, 0.15, 1)
            txt_user = (1, 1, 1, 1)
            txt_ai = (0.9, 0.9, 0.9, 1)
            sys_txt_col = (0.6, 0.6, 0.6, 1)

        bg_color = theme_bg if is_system else (user_bg if is_user else ai_bg)
        final_txt_col = sys_txt_col if is_system else (txt_user if is_user else txt_ai)

        self.btn = Button(
            text=clean_text, markup=True, size_hint=(None, None), 
            color=final_txt_col, font_size='16sp', background_normal='',
            background_color=(0,0,0,0), halign='center' if is_system else 'left', 
            padding=(18, 12)
        )
        
        if not is_user and not is_system: 
            self.btn.bind(on_release=lambda x: Clipboard.copy(text))
            
        self.btn.text_size = (Window.width * (0.9 if is_system else 0.72), None)
        self.btn.bind(texture_size=self.update_size)
        
        with self.btn.canvas.before:
            Color(*bg_color)
            radius = [5] if is_system else ([18, 18, 18, 5] if is_user else [18, 18, 5, 18])
            self.rect = RoundedRectangle(radius=radius)
            
        self.btn.bind(pos=self.update_rect, size=self.update_rect)
        
        if side == 'right':
            self.add_widget(BoxLayout(size_hint_x=1))
            self.add_widget(self.btn)
        elif side == 'left':
            self.add_widget(self.btn)
            self.add_widget(BoxLayout(size_hint_x=1))
        else:
            self.add_widget(self.btn)

    def update_size(self, instance, size):
        instance.size = size
        self.height = size[1] + 16
        
    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class ChatApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')
        
        # ШАПКА
        header = BoxLayout(size_hint_y=None, height=100, padding=(10, 5), spacing=5)
        with header.canvas.before:
            self.h_bg = Color(1, 1, 1, 1)
            self.h_rect = Rectangle()
        header.bind(pos=self.update_header_canvas, size=self.update_header_canvas)

        btn_clr = Button(text='Clear', size_hint=(None, None), size=(80, 50), font_size='14sp', 
                         background_normal='', background_color=(0,0,0,0), color=(0.4, 0.4, 0.6, 1))
        btn_clr.bind(on_release=self.clear_chat)
        
        self.title_label = Button(
            text=state['chat_name'], font_size='18sp', bold=True,
            background_normal='', background_color=(0,0,0,0), color=(0,0,0,1)
        )
        self.title_label.bind(on_release=self.open_edit_title_popup)
        
        btn_menu = Button(text='Menu', size_hint=(None, None), size=(80, 50), font_size='14sp',
                          background_normal='', background_color=(0,0,0,0), color=(0.4, 0.4, 0.6, 1))
        btn_menu.bind(on_release=self.show_main_settings)

        header.add_widget(btn_clr)
        header.add_widget(self.title_label)
        header.add_widget(btn_menu)
        root.add_widget(header)
        
        self.scroll = ScrollView(bar_width=0)
        self.chat_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=(10, 10))
        self.chat_list.bind(minimum_height=self.chat_list.setter('height'))
        self.scroll.add_widget(self.chat_list)
        root.add_widget(self.scroll)

        # НИЖНЯЯ ПАНЕЛЬ
        input_container = BoxLayout(orientation='vertical', size_hint_y=None, height=260, padding=(12, 10), spacing=12)
        with input_container.canvas.before:
            self.f_bg = Color(1, 1, 1, 1)
            self.f_rect = Rectangle()
        input_container.bind(pos=self.update_footer_canvas, size=self.update_footer_canvas)

        # Кнопки-пилюли (КРУПНЫЕ)
        actions = BoxLayout(size_hint_y=None, height=55, spacing=15)
        for name, cmd in [("Глубокое", "АНАЛИЗ"), ("Поиск", "ПОИСК"), ("Кратко", "КРАТКО")]:
            b = Button(text=name, font_size='15sp', size_hint_x=None, width=120,
                       background_normal='', background_color=(0,0,0,0), color=(0.2, 0.4, 0.9, 1))
            with b.canvas.before:
                Color(0.92, 0.94, 1, 1)
                b.rrect = RoundedRectangle(radius=[25])
            b.bind(pos=lambda ins, v: setattr(ins.rrect, 'pos', v), size=lambda ins, v: setattr(ins.rrect, 'size', v))
            b.bind(on_release=lambda x, c=cmd: self.quick_command(c))
            actions.add_widget(b)
        
        entry_wrap = BoxLayout(spacing=5, size_hint_y=None, height=120, padding=(5, 5))
        with entry_wrap.canvas.before:
            Color(0.96, 0.96, 0.97, 1)
            self.entry_bg = RoundedRectangle(radius=[22])
        entry_wrap.bind(pos=self.update_entry_bg, size=self.update_entry_bg)

        btn_plus = Button(text='+', size_hint_x=None, width=55, font_size='26sp',
                          background_normal='', background_color=(0,0,0,0), color=(0.5, 0.5, 0.5, 1))

        self.entry = TextInput(
            hint_text='Спросите что-нибудь...', multiline=True, 
            font_size='17sp', background_normal='', background_color=(0,0,0,0),
            padding=(10, 15), cursor_color=(0.2, 0.4, 1, 1)
        )
        
        btn_send = Button(
            text='>', size_hint_x=None, width=70, 
            background_normal='', background_color=(0,0,0,0), 
            color=(1,1,1,1), bold=True, font_size='24sp'
        )
        with btn_send.canvas.before:
            Color(0.24, 0.45, 1, 1)
            btn_send.r_bg = RoundedRectangle(radius=[20])
        btn_send.bind(pos=lambda ins, v: setattr(ins.r_bg, 'pos', v), size=lambda ins, v: setattr(ins.r_bg, 'size', v))
        btn_send.bind(on_release=self.process_send)
        
        entry_wrap.add_widget(btn_plus)
        entry_wrap.add_widget(self.entry)
        entry_wrap.add_widget(btn_send)
        input_container.add_widget(actions)
        input_container.add_widget(entry_wrap)
        root.add_widget(input_container)
        
        self.update_theme_color()
        return root

    def update_header_canvas(self, instance, value):
        self.h_rect.pos = instance.pos
        self.h_rect.size = instance.size

    def update_footer_canvas(self, instance, value):
        self.f_rect.pos = instance.pos
        self.f_rect.size = instance.size
        
    def update_entry_bg(self, instance, value):
        self.entry_bg.pos = instance.pos
        self.entry_bg.size = instance.size

    def update_theme_color(self):
        is_light = state["theme"] == "light"
        Window.clearcolor = (1, 1, 1, 1) if is_light else (0.05, 0.05, 0.07, 1)
        self.h_bg.rgba = (1,1,1,1) if is_light else (0.08, 0.08, 0.1, 1)
        self.f_bg.rgba = (1,1,1,1) if is_light else (0.08, 0.08, 0.1, 1)
        self.title_label.color = (0,0,0,1) if is_light else (1,1,1,1)

    def show_main_settings(self, *args):
        container = BoxLayout(orientation='vertical', spacing=12, padding=20, size_hint_y=None)
        container.bind(minimum_height=container.setter('height'))
        
        menu_items = [
            ("ХАРАКТЕР", self.show_mood_settings), 
            ("РЕЖИМ", self.show_modes_settings), 
            ("ЯЗЫК", self.show_lang_settings), 
            ("ТЕМА", self.toggle_theme),
            ("ОЧИСТИТЬ", self.clear_chat)
        ]
        
        for t, f in menu_items:
            b = Button(text=t, size_hint_y=None, height=75, background_normal='', 
                       background_color=(0.24, 0.45, 1, 1), color=(1,1,1,1), bold=True)
            b.bind(on_release=f)
            container.add_widget(b)
            
        self.popup = Popup(title='Меню', content=container, size_hint=(0.85, 0.7))
        self.popup.open()

    def show_mood_settings(self, *args):
        self.popup.dismiss()
        container = BoxLayout(orientation='vertical', spacing=10, padding=20)
        # ВЕРНУЛИ ГРУСТНЫЙ
        for m in ["обычный", "добрый", "злой", "грустный"]:
            b = Button(text=m.upper(), size_hint_y=None, height=65)
            b.bind(on_release=lambda x, cur=m: self.set_mood(cur))
            container.add_widget(b)
        self.mood_popup = Popup(title='Характер', content=container, size_hint=(0.8, 0.6))
        self.mood_popup.open()

    def set_mood(self, mood): 
        state["mood"] = mood
        self.mood_popup.dismiss()
        self.chat_list.add_widget(MessageBubble(text=f"Система: Характер — {mood}", side='system'))

    def show_lang_settings(self, *args):
        self.popup.dismiss()
        container = BoxLayout(orientation='vertical', spacing=10, padding=20)
        for l in ["Русский", "English", "Deutsch"]:
            b = Button(text=l, size_hint_y=None, height=65)
            b.bind(on_release=lambda x, cur=l: self.set_lang(cur))
            container.add_widget(b)
        self.lang_popup = Popup(title='Язык', content=container, size_hint=(0.8, 0.5))
        self.lang_popup.open()

    def set_lang(self, l): 
        state["lang"] = l
        self.lang_popup.dismiss()
        self.chat_list.add_widget(MessageBubble(text=f"Система: Язык — {l}", side='system'))

    def show_modes_settings(self, *args):
        self.popup.dismiss()
        container = BoxLayout(orientation='vertical', spacing=10, padding=20)
        for k in ["Быстрые", "Думающие", "PRO"]:
            b = Button(text=k, size_hint_y=None, height=65)
            b.bind(on_release=lambda x, cur=k: self.set_mode(cur))
            container.add_widget(b)
        self.mode_popup = Popup(title='Режим', content=container, size_hint=(0.8, 0.5))
        self.mode_popup.open()

    def set_mode(self, m): 
        state["mode"] = m
        self.mode_popup.dismiss()
        self.chat_list.add_widget(MessageBubble(text=f"Система: Режим — {m}", side='system'))

    def toggle_theme(self, *args): 
        state["theme"] = "dark" if state["theme"] == "light" else "light"
        self.update_theme_color()
        self.popup.dismiss()

    def open_edit_title_popup(self, *args):
        box = BoxLayout(orientation='vertical', padding=20, spacing=10)
        inp = TextInput(text=state['chat_name'], multiline=False, height=65, size_hint_y=None)
        btn = Button(text="OK", height=65, size_hint_y=None, background_color=(0.2, 0.4, 1, 1))
        p = Popup(title='Название', content=box, size_hint=(0.8, 0.35))
        def save(x): 
            state['chat_name'] = inp.text
            self.title_label.text = inp.text
            p.dismiss()
        btn.bind(on_release=save)
        box.add_widget(inp)
        box.add_widget(btn)
        p.open()

    def quick_command(self, cmd): 
        self.entry.text = f"{cmd}: "

    def clear_chat(self, *args): 
        self.chat_list.clear_widgets()
        state["history"] = []
        if hasattr(self, 'popup'): self.popup.dismiss()
    
    def process_send(self, instance):
        text = self.entry.text.strip()
        if not text: return
        self.chat_list.add_widget(MessageBubble(text=text, side='left'))
        self.entry.text = ""
        threading.Thread(target=self.get_ai_answer, args=(text,)).start()

    def get_ai_answer(self, text):
        state["history"].append({"role": "user", "content": text})
        headers = {"Authorization": f"Bearer {API_KEY}"}
        sys_p = f"You are JOPATI PRO. Respond in {state['lang']}. Mood: {state['mood']}."
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, 
                             json={"model": "llama-3.1-8b-instant", "messages": [{"role": "system", "content": sys_p}] + state["history"][-8:]}, timeout=15)
            ans = r.json()['choices'][0]['message']['content']
        except: 
            ans = "Ошибка связи."
        state["history"].append({"role": "assistant", "content": ans})
        Clock.schedule_once(lambda dt: self.chat_list.add_widget(MessageBubble(text=ans, side='right')))

if __name__ == '__main__':
    ChatApp().run()
