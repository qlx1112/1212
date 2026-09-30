from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.colorpicker import ColorPicker
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle
from functools import partial
import random
import os
import json

app_dir = os.path.dirname(os.path.abspath(__file__))
LabelBase.register(name='Chinese', fn_regular=os.path.join(app_dir, 'msyh.ttc'))

SETTINGS_FILE = os.path.join(app_dir, "settings.json")

DEFAULT_THEME = {
    "bg": [0.96, 0.96, 0.98, 1],
    "btn": [0.20, 0.50, 0.90, 1],
    "text": [0.10, 0.10, 0.12, 1],
    "answer_text": [0.15, 0.70, 0.35, 1],
}


def load_theme():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key in DEFAULT_THEME:
                if key not in data:
                    data[key] = DEFAULT_THEME[key]
            return data
        except Exception:
            return DEFAULT_THEME.copy()
    return DEFAULT_THEME.copy()


def save_theme(theme):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(theme, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def apply_bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        widget.bg_rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda inst, val: update_bg_rect(inst), size=lambda inst, val: update_bg_rect(inst))


def update_bg_rect(widget):
    if hasattr(widget, 'bg_rect'):
        widget.bg_rect.pos = widget.pos
        widget.bg_rect.size = widget.size


class FlashCardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'flashcard'
        self.is_answer_shown = False

    def on_enter(self):
        app = App.get_running_app()
        app.load_question_bank()
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        app = App.get_running_app()
        theme = app.theme

        root = BoxLayout(orientation='vertical', padding=30, spacing=20)
        apply_bg(root, theme["bg"])

        top_bar = BoxLayout(size_hint_y=0.1, spacing=10)
        title = Label(
            text='学习卡片',
            font_name='msyh.ttc',
            font_size=22,
            color=theme["text"],
            size_hint_x=0.6,
            halign='left',
            valign='middle'
        )
        list_btn = Button(
            text='题库',
            font_name='msyh.ttc',
            font_size=15,
            size_hint_x=0.2,
            background_color=theme["btn"],
            color=(1, 1, 1, 1),
            on_press=self.go_to_list
        )
        setting_btn = Button(
            text='设置',
            font_name='msyh.ttc',
            font_size=15,
            size_hint_x=0.2,
            background_color=theme["btn"],
            color=(1, 1, 1, 1),
            on_press=app.open_settings
        )
        top_bar.add_widget(title)
        top_bar.add_widget(list_btn)
        top_bar.add_widget(setting_btn)
        root.add_widget(top_bar)

        # 问题标签：自动换行，不超出屏幕
        self.question_label = Label(
            text='先在「题库」添加题目，在点「下一题」开始学习',
            font_name='msyh.ttc',
            font_size=26,
            color=theme["text"],
            size_hint_y=0.4,
            halign='center',
            valign='middle'
        )
        # 绑定宽度，文本到边界自动换行
        self.question_label.bind(
            width=lambda inst, v: setattr(inst, 'text_size', (v, None))
        )
        root.add_widget(self.question_label)

        # 答案标签：自动换行
        self.answer_label = Label(
            text='',
            font_name='msyh.ttc',
            font_size=22,
            color=theme["answer_text"],
            size_hint_y=0.3,
            halign='center',
            valign='middle'
        )
        self.answer_label.bind(
            width=lambda inst, v: setattr(inst, 'text_size', (v, None))
        )
        root.add_widget(self.answer_label)

        btn_box = BoxLayout(size_hint_y=0.2, spacing=30)
        self.toggle_btn = Button(
            text='显示答案',
            font_name='msyh.ttc',
            font_size=18,
            background_color=theme["btn"],
            color=(1, 1, 1, 1),
            on_press=self.toggle_answer
        )
        self.next_btn = Button(
            text='下一题',
            font_name='msyh.ttc',
            font_size=18,
            background_color=theme["btn"],
            color=(1, 1, 1, 1),
            on_press=self.next_question
        )
        btn_box.add_widget(self.toggle_btn)
        btn_box.add_widget(self.next_btn)
        root.add_widget(btn_box)

        self.add_widget(root)

    def toggle_answer(self, instance):
        app = App.get_running_app()
        if not app.current_question:
            return

        if self.is_answer_shown:
            self.answer_label.text = ''
            self.toggle_btn.text = '显示答案'
            self.is_answer_shown = False
        else:
            self.answer_label.text = app.current_question[1]
            self.toggle_btn.text = '隐藏答案'
            self.is_answer_shown = True

    def next_question(self, instance):
        app = App.get_running_app()
        if app.qa_list:
            app.current_question = random.choice(app.qa_list)
            self.question_label.text = app.current_question[0]
            self.answer_label.text = ''
            self.toggle_btn.text = '显示答案'
            self.is_answer_shown = False

    def go_to_list(self, instance):
        self.manager.current = 'list'


class QuestionListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'list'

    def on_enter(self):
        app = App.get_running_app()
        app.load_question_bank()
        self.build_ui()
        self.refresh_list()

    def build_ui(self):
        self.clear_widgets()
        app = App.get_running_app()
        theme = app.theme

        root = BoxLayout(orientation='vertical', padding=20, spacing=15)
        apply_bg(root, theme["bg"])

        top_bar = BoxLayout(size_hint_y=0.1, spacing=10)
        back_btn = Button(
            text='返回',
            font_name="msyh.ttc",
            font_size=15,
            size_hint_x=0.2,
            background_color=theme["btn"],
            color=(1, 1, 1, 1),
            on_press=self.go_back
        )
        title = Label(
            text='题库管理',
            font_name="msyh.ttc",
            font_size=20,
            color=theme["text"],
            size_hint_x=0.6,
            halign='center'
        )
        add_btn = Button(
            text='添加',
            font_name="msyh.ttc",
            font_size=15,
            size_hint_x=0.2,
            background_color=(0.20, 0.75, 0.35, 1),
            color=(1, 1, 1, 1),
            on_press=self.go_to_add
        )
        top_bar.add_widget(back_btn)
        top_bar.add_widget(title)
        top_bar.add_widget(add_btn)
        root.add_widget(top_bar)

        self.scroll = ScrollView(size_hint_y=0.9)
        self.list_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=12,
            padding=5
        )
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def refresh_list(self):
        self.list_layout.clear_widgets()
        app = App.get_running_app()
        theme = app.theme

        if not app.qa_list:
            empty_label = Label(
                text='题库为空，点击右上角添加题目',
                font_name="msyh.ttc",
                font_size=16,
                color=theme["text"],
                size_hint_y=None,
                height=50
            )
            self.list_layout.add_widget(empty_label)
            return

        for idx, (q, a) in enumerate(app.qa_list):
            item = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                spacing=8,
                padding=10
            )

            q_row = BoxLayout(orientation='horizontal', size_hint_y=None, spacing=10)

            # 问题标签：自动换行，高度自适应，不超出按钮区域
            q_label = Label(
                text=f'{idx + 1}. {q}',
                font_name="msyh.ttc",
                font_size=15,
                color=theme["text"],
                size_hint_x=0.7,
                size_hint_y=None,
                halign='left',
                valign='middle'
            )
            q_label.bind(
                width=lambda inst, v: setattr(inst, 'text_size', (v, None)),
                texture_size=lambda inst, v: setattr(inst, 'height', v[1])
            )

            toggle_btn = Button(
                text='显示答案',
                font_name="msyh.ttc",
                font_size=12,
                size_hint_x=0.15,
                size_hint_y=None,
                height=36,
                background_color=theme["btn"],
                color=(1, 1, 1, 1)
            )
            del_btn = Button(
                text='删除',
                font_name="msyh.ttc",
                font_size=12,
                size_hint_x=0.15,
                size_hint_y=None,
                height=36,
                background_color=(0.88, 0.25, 0.25, 1),
                color=(1, 1, 1, 1)
            )
            q_row.add_widget(q_label)
            q_row.add_widget(toggle_btn)
            q_row.add_widget(del_btn)

            # 答案标签：自动换行，隐藏时高度为0
            a_label = Label(
                text=f'  答：{a}',
                font_name="msyh.ttc",
                font_size=14,
                color=theme["answer_text"],
                size_hint_x=1,
                size_hint_y=None,
                height=0,
                opacity=0,
                halign='left',
                valign='top'
            )
            a_label.bind(
                width=lambda inst, v: setattr(inst, 'text_size', (v, None))
            )

            toggle_btn.bind(on_press=partial(self.toggle_answer, a_label, toggle_btn))
            del_btn.bind(on_press=partial(self.delete_question, idx))

            item.add_widget(q_row)
            item.add_widget(a_label)
            self.list_layout.add_widget(item)

    def toggle_answer(self, a_label, btn, instance):
        if a_label.opacity == 0:
            a_label.opacity = 1
            # 显示时高度 = 文本实际高度
            a_label.height = a_label.texture_size[1]
            btn.text = '隐藏答案'
        else:
            a_label.opacity = 0
            a_label.height = 0
            btn.text = '显示答案'

    def delete_question(self, index, instance):
        app = App.get_running_app()
        if 0 <= index < len(app.qa_list):
            del app.qa_list[index]
        with open(app.qa_path, 'w', encoding='utf-8') as f:
            for q, a in app.qa_list:
                f.write(f'{q}|{a}\n')
        self.refresh_list()

    def go_to_add(self, instance):
        self.manager.current = 'add'

    def go_back(self, instance):
        self.manager.current = 'flashcard'


class AddQuestionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'add'

    def on_enter(self):
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        app = App.get_running_app()
        theme = app.theme

        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        apply_bg(layout, theme["bg"])

        top_bar = BoxLayout(size_hint_y=0.1)
        back_btn = Button(
            text='返回',
            font_name="msyh.ttc",
            font_size=15,
            size_hint_x=0.25,
            background_color=theme["btn"],
            color=(1, 1, 1, 1),
            on_press=self.go_back
        )
        title = Label(
            text='添加新题目',
            font_name="msyh.ttc",
            font_size=20,
            color=theme["text"],
            size_hint_x=0.75,
            halign='left'
        )
        top_bar.add_widget(back_btn)
        top_bar.add_widget(title)
        layout.add_widget(top_bar)

        layout.add_widget(Label(
            text='问题：',
            font_name="msyh.ttc",
            size_hint_y=0.05,
            color=theme["text"],
            halign='left'
        ))
        self.question_input = TextInput(
            font_name="msyh.ttc",
            font_size=17,
            size_hint_y=0.25,
            multiline=True,
            foreground_color=theme["text"],
            cursor_color=theme["btn"]
        )
        layout.add_widget(self.question_input)

        layout.add_widget(Label(
            text='答案：',
            font_name="msyh.ttc",
            size_hint_y=0.05,
            color=theme["text"],
            halign='left'
        ))
        self.answer_input = TextInput(
            font_name="msyh.ttc",
            font_size=17,
            size_hint_y=0.35,
            multiline=True,
            foreground_color=theme["text"],
            cursor_color=theme["btn"]
        )
        layout.add_widget(self.answer_input)

        self.tip_label = Label(
            text='',
            font_name="msyh.ttc",
            size_hint_y=0.08,
            color=(0.88, 0.25, 0.25, 1)
        )
        layout.add_widget(self.tip_label)

        save_btn = Button(
            text='保存题目',
            font_name="msyh.ttc",
            font_size=17,
            size_hint_y=0.12,
            background_color=(0.20, 0.75, 0.35, 1),
            color=(1, 1, 1, 1),
            on_press=self.save_question
        )
        layout.add_widget(save_btn)

        self.add_widget(layout)

    def save_question(self, instance):
        q = self.question_input.text.strip()
        a = self.answer_input.text.strip()

        if not q or not a:
            self.tip_label.text = '问题和答案都不能为空'
            return

        app = App.get_running_app()
        with open(app.qa_path, 'a', encoding='utf-8') as f:
            f.write(f'{q}|{a}\n')
        app.qa_list.append((q, a))

        self.question_input.text = ''
        self.answer_input.text = ''
        self.tip_label.text = '添加成功！'

    def go_back(self, instance):
        self.manager.current = 'list'


class ColorSettingRow(BoxLayout):
    def __init__(self, label_text, key, app, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 46
        self.spacing = 10
        self.padding = 5

        self.key = key
        self.app = app
        theme = app.theme

        self.label = Label(
            text=label_text,
            font_name="msyh.ttc",
            font_size=15,
            color=theme["text"],
            size_hint_x=0.35
        )

        self.preview = Button(
            text='',
            size_hint_x=0.2,
            background_color=theme[key]
        )
        self.preview.bind(on_press=self.open_picker)

        self.picker_btn = Button(
            text='选择颜色',
            font_name="msyh.ttc",
            font_size=14,
            size_hint_x=0.45,
            background_color=theme["btn"],
            color=(1, 1, 1, 1)
        )
        self.picker_btn.bind(on_press=self.open_picker)

        self.add_widget(self.label)
        self.add_widget(self.preview)
        self.add_widget(self.picker_btn)

    def open_picker(self, instance):
        picker = ColorPickerPopup(self.key, self.app)
        picker.open()


class ColorPickerPopup(Popup):
    def __init__(self, key, app, **kwargs):
        super().__init__(**kwargs)
        self.title = f'选择{key_label(key)}颜色'
        self.size_hint = (0.9, 0.8)
        self.key = key
        self.app = app
        theme = app.theme

        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        apply_bg(layout, theme["bg"])

        preview_title = Label(
            text='颜色预览',
            font_name="msyh.ttc",
            font_size=16,
            color=theme["text"],
            size_hint_y=0.06
        )

        self.preview_box = BoxLayout(size_hint_y=0.12)
        apply_bg(self.preview_box, theme[key])

        self.color_picker = ColorPicker()
        self.color_picker.color = theme[key]
        self.color_picker.bind(color=self.on_color)

        btn_box = BoxLayout(size_hint_y=0.12, spacing=20)
        cancel_btn = Button(
            text='取消',
            font_name="msyh.ttc",
            font_size=15,
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1),
            on_press=self.dismiss
        )
        confirm_btn = Button(
            text='确认',
            font_name="msyh.ttc",
            font_size=15,
            background_color=(0.20, 0.75, 0.35, 1),
            color=(1, 1, 1, 1),
            on_press=self.confirm
        )
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(confirm_btn)

        layout.add_widget(preview_title)
        layout.add_widget(self.preview_box)
        layout.add_widget(self.color_picker)
        layout.add_widget(btn_box)

        self.content = layout

    def on_color(self, instance, value):
        self.app.theme[self.key] = list(value)
        self.app.refresh_all_screens()
        update_bg_rect(self.preview_box)

    def confirm(self, instance):
        self.dismiss()


def key_label(key):
    mapping = {
        "bg": "背景",
        "btn": "按钮",
        "text": "文字",
        "answer_text": "答案文字"
    }
    return mapping.get(key, key)


class SettingsPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = '界面设置'
        self.size_hint = (0.9, 0.8)
        app = App.get_running_app()
        self.original_theme = deep_copy_theme(app.theme)
        theme = app.theme

        layout = BoxLayout(orientation='vertical', padding=15, spacing=12)
        apply_bg(layout, theme["bg"])

        title = Label(
            text='自定义界面颜色',
            font_name="msyh.ttc",
            font_size=18,
            color=theme["text"],
            size_hint_y=0.08
        )
        layout.add_widget(title)

        layout.add_widget(ColorSettingRow('背景颜色', 'bg', app))
        layout.add_widget(ColorSettingRow('按钮颜色', 'btn', app))
        layout.add_widget(ColorSettingRow('文字颜色', 'text', app))
        layout.add_widget(ColorSettingRow('答案文字', 'answer_text', app))

        tip = Label(
            text='拖动轮盘选择颜色，点击确认后自动保存',
            font_name="msyh.ttc",
            font_size=13,
            color=theme["text"],
            size_hint_y=0.08
        )
        layout.add_widget(tip)

        btn_box = BoxLayout(size_hint_y=0.14, spacing=20)
        cancel_btn = Button(
            text='取消',
            font_name="msyh.ttc",
            font_size=15,
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1),
            on_press=self.cancel
        )
        save_btn = Button(
            text='保存设置',
            font_name="msyh.ttc",
            font_size=15,
            background_color=(0.20, 0.75, 0.35, 1),
            color=(1, 1, 1, 1),
            on_press=self.save
        )
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(save_btn)
        layout.add_widget(btn_box)

        self.content = layout

    def cancel(self, instance):
        app = App.get_running_app()
        app.theme = self.original_theme
        app.refresh_all_screens()
        self.dismiss()

    def save(self, instance):
        app = App.get_running_app()
        save_theme(app.theme)
        self.dismiss()


def deep_copy_theme(theme):
    return {k: list(v) for k, v in theme.items()}


class FlashCardApp(App):
    def build(self):
        self.theme = load_theme()
        self.qa_path = os.path.join(app_dir, 'qa.txt')
        self.qa_list = []
        self.current_question = None
        self.load_question_bank()

        sm = ScreenManager()
        sm.add_widget(FlashCardScreen())
        sm.add_widget(QuestionListScreen())
        sm.add_widget(AddQuestionScreen())
        return sm

    def load_question_bank(self):
        self.qa_list = []
        if not os.path.exists(self.qa_path):
            return
        with open(self.qa_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or '|' not in line:
                    continue
                q, a = line.split('|', 1)
                self.qa_list.append((q.strip(), a.strip()))

    def open_settings(self, instance):
        SettingsPopup().open()

    def refresh_all_screens(self):
        for screen in self.root.screens:
            if hasattr(screen, 'build_ui'):
                screen.build_ui()
            if hasattr(screen, 'refresh_list'):
                screen.refresh_list()


if __name__ == '__main__':
    FlashCardApp().run()
