from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

GRAY_BG = (0.25, 0.25, 0.25, 1)
OFF_WHITE = (0.95, 0.95, 0.92, 1)
DARK_GRAY = (0.15, 0.15, 0.15, 1)

Window.clearcolor = GRAY_BG


class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=40, spacing=20)

        with self.layout.canvas.before:
            Color(*GRAY_BG)
            self.bg_rect = Rectangle(pos=self.layout.pos, size=self.layout.size)

        self.layout.bind(pos=self.update_bg, size=self.update_bg)
        self.add_widget(self.layout)

    def update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


class SplashScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        title = Label(
            text="YKC - Cricket Scorer",
            font_size=28,
            color=OFF_WHITE,
            size_hint=(1, 0.5),
            halign="center",
            valign="middle"
        )

        subtitle = Label(
            text="By Abubakar Saudagar",
            font_size=16,
            color=OFF_WHITE,
            size_hint=(1, 0.3),
            halign="center",
            valign="middle"
        )

        self.layout.add_widget(title)
        self.layout.add_widget(subtitle)

    def on_enter(self):
        Clock.schedule_once(self.go_to_home, 2.5)

    def go_to_home(self, dt):
        self.manager.current = "home"


class HomeScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        title = Label(
            text="YKC Cricket Scorer",
            font_size=32,
            color=OFF_WHITE,
            size_hint=(1, 0.3)
        )

        new_match_btn = Button(
            text="New Match",
            size_hint=(1, 0.2),
            background_color=DARK_GRAY,
            color=OFF_WHITE
        )
        new_match_btn.bind(on_release=self.go_to_create_team)

        self.layout.add_widget(title)
        self.layout.add_widget(new_match_btn)

    def go_to_create_team(self, instance):
        self.manager.current = "create_team"


class CreateTeamScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        label = Label(text="Enter Team Names", font_size=24, color=OFF_WHITE, size_hint=(1, 0.2))

        self.team_a_input = TextInput(
            hint_text="Team A Name",
            size_hint=(1, 0.15),
            multiline=False,
            background_color=OFF_WHITE,
            foreground_color=DARK_GRAY
        )
        self.team_b_input = TextInput(
            hint_text="Team B Name",
            size_hint=(1, 0.15),
            multiline=False,
            background_color=OFF_WHITE,
            foreground_color=DARK_GRAY
        )

        continue_btn = Button(
            text="Continue to Toss",
            size_hint=(1, 0.2),
            background_color=DARK_GRAY,
            color=OFF_WHITE
        )
        continue_btn.bind(on_release=self.go_to_toss)

        back_btn = Button(
            text="Back",
            size_hint=(1, 0.15),
            background_color=OFF_WHITE,
            color=DARK_GRAY
        )
        back_btn.bind(on_release=self.go_back)

        self.layout.add_widget(label)
        self.layout.add_widget(self.team_a_input)
        self.layout.add_widget(self.team_b_input)
        self.layout.add_widget(continue_btn)
        self.layout.add_widget(back_btn)

    def go_to_toss(self, instance):
        app = App.get_running_app()
        app.team_a_name = self.team_a_input.text.strip() or "Team A"
        app.team_b_name = self.team_b_input.text.strip() or "Team B"
        toss_screen = self.manager.get_screen("toss")
        toss_screen.update_teams(app.team_a_name, app.team_b_name)
        self.manager.current = "toss"

    def go_back(self, instance):
        self.manager.current = "home"


class TossScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.info_label = Label(text="Who won the toss?", font_size=24, color=OFF_WHITE, size_hint=(1, 0.2))

        self.team_a_btn = Button(text="Team A", size_hint=(1, 0.2), background_color=DARK_GRAY, color=OFF_WHITE)
        self.team_b_btn = Button(text="Team B", size_hint=(1, 0.2), background_color=DARK_GRAY, color=OFF_WHITE)

        self.team_a_btn.bind(on_release=lambda instance: self.select_toss_winner("A"))
        self.team_b_btn.bind(on_release=lambda instance: self.select_toss_winner("B"))

        self.layout.add_widget(self.info_label)
        self.layout.add_widget(self.team_a_btn)
        self.layout.add_widget(self.team_b_btn)

    def update_teams(self, team_a_name, team_b_name):
        self.team_a_btn.text = team_a_name
        self.team_b_btn.text = team_b_name

    def select_toss_winner(self, team_key):
        app = App.get_running_app()
        app.toss_winner = team_key
        winner_name = self.team_a_btn.text if team_key == "A" else self.team_b_btn.text

        self.layout.clear_widgets()

        result_label = Label(
            text=winner_name + " won the toss",
            font_size=22,
            color=OFF_WHITE,
            size_hint=(1, 0.2)
        )

        bat_btn = Button(text="Choose to Bat", size_hint=(1, 0.2), background_color=DARK_GRAY, color=OFF_WHITE)
        bowl_btn = Button(text="Choose to Bowl", size_hint=(1, 0.2), background_color=DARK_GRAY, color=OFF_WHITE)

        bat_btn.bind(on_release=lambda instance: self.select_decision("bat"))
        bowl_btn.bind(on_release=lambda instance: self.select_decision("bowl"))

        self.layout.add_widget(result_label)
        self.layout.add_widget(bat_btn)
        self.layout.add_widget(bowl_btn)

    def select_decision(self, decision):
        app = App.get_running_app()
        app.toss_decision = decision
        self.manager.current = "match_setup"


class MatchSetupScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        label = Label(
            text="Match setup screen coming next",
            font_size=22,
            color=OFF_WHITE
        )
        self.layout.add_widget(label)


class YKCApp(App):
    def build(self):
        self.team_a_name = "Team A"
        self.team_b_name = "Team B"
        self.toss_winner = None
        self.toss_decision = None

        sm = ScreenManager()
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(CreateTeamScreen(name="create_team"))
        sm.add_widget(TossScreen(name="toss"))
        sm.add_widget(MatchSetupScreen(name="match_setup"))
        sm.current = "splash"
        return sm


if __name__ == "__main__":
    YKCApp().run()
