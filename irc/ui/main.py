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
from ..objects import Message
from .._utils import iter_to_dict
from ..commands import Commands


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
        messages = Message.all()
        messages_by_channel = iter_to_dict(messages, key=lambda message: message.channel)
        for channel, messages in messages_by_channel.items():
            for message in messages:
                chat_item = ChatListItem()
                chat_item.friend_name = message.channel
                chat_item.message = message.content
                chat_item.timestamp = message.timestamp
                chat_item.sender = message.author
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

    def __init__(self, channel_name: str, **kwargs):
        self.channel_name = channel_name
        super().__init__(**kwargs)

    def on_enter(self, *args):
        self._populate()

    def _populate(self) -> None:
        displayed: int = 0
        for message in Message.all(channel=self.channel_name):
            chat_bubble = ChatBubble()
            chat_bubble.message = message.content
            chat_bubble.time = message.timestamp
            chat_bubble.sender = message.author
            self.ids.message_list.add_widget(chat_bubble)
            displayed += 1

        if not displayed:
            Popup(title="Error", content=MDLabel(text="No message"))
            self.sm.switch_to(ChannelScreen())


class MainApp(MDApp):

    wm: ScreenManager
    commands = Commands()

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

    def create_chat(self, channel: str):
        """
        Get all messages and create a chat screen.
        """
        chat_screen = ChatScreen(channel)  # FIXME
        chat_screen.name = channel
        chat_screen.text = "C'est quoi ça?"
        self.wm.switch_to(chat_screen)

    def send(self):
        chat_screen = self.wm.get_screen("active_chat")
        text_input = chat_screen.ids.input.ids.value
        if text_input.startswith('/'):
            identifier = text_input[1:].split()[0]
            # The message is a command
            command = self.commands[identifier].parse(text_input)
        else:
            command = self.commands["msg"](
                nickname="",  # FIXME
                parameters=[text_input],
            )
        # TODO

        # Clear input field
        text_input.text = ""
