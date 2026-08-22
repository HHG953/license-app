from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.clipboard import Clipboard
import os
import json
import base64
import hashlib
import time
import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class LicenseGenerator:
    def __init__(self):
        self.salt = b"YourSalt_16Byte!"
        self.secret = "YourSecretKey_32ByteLengthHere!"
        self.key = hashlib.sha256(self.secret.encode()).digest()

    def encrypt_data(self, data):
        cipher = AES.new(self.key, AES.MODE_CBC, self.salt)
        padded = pad(data.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode('utf-8')

    def generate_license(self, hardware_id, days=0, hours=0, minutes=0):
        now = int(time.time())
        expire_time = now + days * 86400 + hours * 3600 + minutes * 60
        license_data = {
            "hardware_id": hardware_id.upper().strip(),
            "expire_time": expire_time,
            "issue_time": now,
            "salt": os.urandom(16).hex()
        }
        json_data = json.dumps(license_data)
        encrypted = self.encrypt_data(json_data)
        groups = [encrypted[i:i+4] for i in range(0, len(encrypted), 4)]
        return "-".join(groups)


class LicenseAppLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(LicenseAppLayout, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        self.generator = LicenseGenerator()
        self.current_code = ""
        self.current_hw = ""

        self.add_widget(Label(
            text="🔑 注册码生成器",
            font_size=24,
            size_hint_y=None,
            height=50,
            bold=True,
            color=(0.17, 0.42, 0.62, 1)
        ))

        self.add_widget(Label(text="硬件码:", size_hint_y=None, height=30, halign='left'))
        self.hw_input = TextInput(
            hint_text="请输入硬件码",
            multiline=False,
            size_hint_y=None,
            height=44,
            font_size=16,
            background_color=(0.95, 0.96, 0.97, 1)
        )
        self.add_widget(self.hw_input)

        self.add_widget(Label(text="授权期限:", size_hint_y=None, height=30, halign='left'))

        period_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=10)
        days_layout = BoxLayout(orientation='horizontal', spacing=5)
        days_layout.add_widget(Label(text="天", size_hint_x=0.3))
        self.days_input = TextInput(text="0", multiline=False, input_filter='int', size_hint_x=0.7)
        days_layout.add_widget(self.days_input)
        period_layout.add_widget(days_layout)

        hours_layout = BoxLayout(orientation='horizontal', spacing=5)
        hours_layout.add_widget(Label(text="时", size_hint_x=0.3))
        self.hours_input = TextInput(text="0", multiline=False, input_filter='int', size_hint_x=0.7)
        hours_layout.add_widget(self.hours_input)
        period_layout.add_widget(hours_layout)

        minutes_layout = BoxLayout(orientation='horizontal', spacing=5)
        minutes_layout.add_widget(Label(text="分", size_hint_x=0.3))
        self.minutes_input = TextInput(text="0", multiline=False, input_filter='int', size_hint_x=0.7)
        minutes_layout.add_widget(self.minutes_input)
        period_layout.add_widget(minutes_layout)
        self.add_widget(period_layout)

        preset_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        presets = [("7天", 7, 0, 0), ("30天", 30, 0, 0), ("90天", 90, 0, 0), ("180天", 180, 0, 0), ("365天", 365, 0, 0), ("永久", 9999, 0, 0)]
        for label, d, h, m in presets:
            btn = Button(text=label, size_hint_x=1, background_color=(0.2, 0.5, 0.8, 1))
            btn.bind(on_press=lambda instance, d=d, h=h, m=m: self.set_period(d, h, m))
            preset_layout.add_widget(btn)
        self.add_widget(preset_layout)

        generate_btn = Button(text="🚀 生成注册码", size_hint_y=None, height=50, font_size=18, background_color=(0.17, 0.42, 0.62, 1))
        generate_btn.bind(on_press=self.generate)
        self.add_widget(generate_btn)

        self.add_widget(Label(text="注册码:", size_hint_y=None, height=30, halign='left'))
        self.result_input = TextInput(text="", multiline=True, size_hint_y=None, height=120, font_size=14, background_color=(0.95, 0.96, 0.97, 1))
        self.add_widget(self.result_input)

        action_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=10)
        copy_btn = Button(text="📋 复制", background_color=(0.2, 0.6, 0.4, 1))
        copy_btn.bind(on_press=self.copy_code)
        action_layout.add_widget(copy_btn)
        clear_btn = Button(text="🧹 清空", background_color=(0.7, 0.3, 0.3, 1))
        clear_btn.bind(on_press=self.clear_all)
        action_layout.add_widget(clear_btn)
        self.add_widget(action_layout)

        self.expire_label = Label(text="", size_hint_y=None, height=30, color=(0.8, 0.5, 0, 1))
        self.add_widget(self.expire_label)

        self.add_widget(Label(text="日志:", size_hint_y=None, height=25, halign='left'))
        self.log_input = TextInput(text="就绪", multiline=True, size_hint_y=None, height=80, font_size=12, background_color=(0.98, 0.98, 0.99, 1), readonly=True)
        self.add_widget(self.log_input)

    def set_period(self, days, hours, minutes):
        self.days_input.text = str(days)
        self.hours_input.text = str(hours)
        self.minutes_input.text = str(minutes)

    def log(self, msg):
        self.log_input.text = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\n" + self.log_input.text
        if len(self.log_input.text) > 500:
            self.log_input.text = self.log_input.text[:500]

    def generate(self, instance):
        hw_id = self.hw_input.text.strip()
        if not hw_id:
            self.log("❌ 请输入硬件码")
            return
        try:
            days = int(self.days_input.text) if self.days_input.text else 0
            hours = int(self.hours_input.text) if self.hours_input.text else 0
            minutes = int(self.minutes_input.text) if self.minutes_input.text else 0
        except:
            self.log("❌ 请输入有效数字")
            return
        if days == 0 and hours == 0 and minutes == 0:
            self.log("❌ 请设置授权期限")
            return
        try:
            code = self.generator.generate_license(hw_id, days, hours, minutes)
            self.result_input.text = code
            self.current_code = code
            self.current_hw = hw_id
            now = int(time.time())
            expire_time = now + days * 86400 + hours * 3600 + minutes * 60
            expire_str = datetime.datetime.fromtimestamp(expire_time).strftime("%Y-%m-%d %H:%M:%S")
            if days >= 9999:
                self.expire_label.text = "✅ 永久授权"
            else:
                self.expire_label.text = f"⏰ 授权到期: {expire_str}"
            self.log(f"✅ 注册码已生成 | 硬件码: {hw_id[:8]}... | 期限: {days}天{hours}时{minutes}分")
        except Exception as e:
            self.log(f"❌ 生成失败: {str(e)}")

    def copy_code(self, instance):
        code = self.result_input.text.strip()
        if code:
            Clipboard.copy(code)
            self.log("📋 已复制到剪贴板")
            popup = Popup(title="✅ 已复制", content=Label(text="注册码已复制到剪贴板"), size_hint=(0.8, 0.3), auto_dismiss=True)
            popup.open()

    def clear_all(self, instance):
        self.hw_input.text = ""
        self.result_input.text = ""
        self.expire_label.text = ""
        self.log_input.text = "已清空"
        self.current_code = ""
        self.current_hw = ""


class LicenseApp(App):
    def build(self):
        self.title = "🔑 注册码生成器"
        return LicenseAppLayout()


if __name__ == "__main__":
    LicenseApp().run()