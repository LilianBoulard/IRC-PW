from pathlib import Path

from kivy.core.window import Window
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from .._events import global_stop_event


class WindowManager(ScreenManager):
    pass


class ChatListItem(MDCard):
    """
    A clickable chat item for the chat timeline.
    """

    friend_name = StringProperty()
    message = StringProperty()
    timestamp = StringProperty()
    friend_avatar = StringProperty()
    conversation = NumericProperty()


class ChannelScreen(Screen):
    """
    A screen that displays all message histories.
    """

    name = StringProperty("conversations")

    def on_enter(self, *args) -> None:
        self._populate()

    def _populate(self) -> None:
        conversations = []
        for conv in conversations:

            chat_item = ChatListItem()
            chat_item.friend_name = last_message.author.name
            chat_item.friend_avatar = last_message.author.pattern
            chat_item.message = last_message.value
            chat_item.timestamp = last_message.time_received
            chat_item.sender = last_message.author
            self.ids.chat_list.add_widget(chat_item)


class ChatBubble(MDBoxLayout):
    """
    A chat bubble for the chat screen messages.
    """

    message = StringProperty()
    time = StringProperty()
    sender = StringProperty()


class ChatScreen(Screen):
    """
    A screen that display messages with a node.
    """

    name = StringProperty("active_chat")
    text = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self, *args):
        self._populate()

    def _populate(self) -> None:
        displayed: int = 0
        for message in self.conversation.clear_messages:
            chat_bubble = ChatBubble()
            chat_bubble.message = message.value
            chat_bubble.time = message.time_received
            chat_bubble.sender = message.author
            self.ids.message_list.add_widget(chat_bubble)
            displayed += 1

        if not displayed:
            Popup(title="Error", content=MDLabel(text="No message"))
            self.sm.switch_to(ChannelScreen())


class MainApp(MDApp):

    wm: ScreenManager

    def __init__(self, **kwargs):
        Window.size = (320, 600)
        self.load_all_kv_files(str(Path(__file__).parent))
        super().__init__(**kwargs)

    def __del__(self):
        global_stop_event.set()  # FIXME: remove?

    def build(self):
        """
        Initializes the application and returns the root widget.
        """
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Blue"
        self.theme_cls.accent_hue = "400"
        self.title = "IRC"
        self.wm = WindowManager(transition=NoTransition())

        self.wm.add_widget(ChannelScreen())

        return self.wm

    def back_to_conversations(self):
        self.wm.switch_to(ChannelScreen())

    def switch_theme(self):
        """
        Switch the app's theme (light / dark).
        """
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.theme_style = "Light"
        else:
            self.theme_cls.theme_style = "Dark"

    def create_chat(self, conv_id: int):
        """
        Get all messages and create a chat screen.
        """
        chat_screen = ChatScreen()  # FIXME
        chat_screen.text = conv_id  # FIXME
        chat_screen.image = ""  # FIXME
        self.wm.switch_to(chat_screen)

    def send(self):
        chat_screen = self.wm.get_screen("active_chat")
        text_input = chat_screen.ids.input.ids.value
        # Clear input
        text_input.text = ""
