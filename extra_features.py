from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle

GRAY_BG = (0.25, 0.25, 0.25, 1)
OFF_WHITE = (0.95, 0.95, 0.92, 1)
DARK_GRAY = (0.15, 0.15, 0.15, 1)


class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=30, spacing=15)

        with self.layout.canvas.before:
            Color(*GRAY_BG)
            self.bg_rect = Rectangle(pos=self.layout.pos, size=self.layout.size)

        self.layout.bind(pos=self.update_bg, size=self.update_bg)
        self.add_widget(self.layout)

    def update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


# ---------------- MATCH SETTINGS (mid-match edit) ----------------

class MatchSettingsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.return_screen = "scoring"

        title = Label(text="Match Settings", font_size=22, color=OFF_WHITE, size_hint=(1, 0.15))

        self.overs_input = TextInput(
            hint_text="Overs limit",
            multiline=False,
            input_filter="int",
            size_hint=(1, 0.12),
            background_color=OFF_WHITE,
            foreground_color=DARK_GRAY
        )

        self.wickets_input = TextInput(
            hint_text="Wickets limit (example 10)",
            multiline=False,
            input_filter="int",
            size_hint=(1, 0.12),
            background_color=OFF_WHITE,
            foreground_color=DARK_GRAY
        )

        save_btn = Button(text="Save Changes", size_hint=(1, 0.15), background_color=DARK_GRAY, color=OFF_WHITE)
        save_btn.bind(on_release=self.save_settings)

        back_btn = Button(text="Back", size_hint=(1, 0.12), background_color=OFF_WHITE, color=DARK_GRAY)
        back_btn.bind(on_release=self.go_back)

        self.status_label = Label(text="", font_size=14, color=OFF_WHITE, size_hint=(1, 0.1))

        self.layout.add_widget(title)
        self.layout.add_widget(self.overs_input)
        self.layout.add_widget(self.wickets_input)
        self.layout.add_widget(save_btn)
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(back_btn)

    def on_pre_enter(self):
        app = App.get_running_app()
        self.overs_input.text = str(app.overs_limit)
        self.wickets_input.text = str(getattr(app, "wickets_limit", 10))

    def save_settings(self, instance):
        app = App.get_running_app()
        try:
            new_overs = int(self.overs_input.text.strip())
            new_wickets = int(self.wickets_input.text.strip())
        except ValueError:
            self.status_label.text = "Enter valid numbers"
            return

        app.overs_limit = new_overs
        app.wickets_limit = new_wickets
        self.status_label.text = "Updated: " + str(new_overs) + " overs, " + str(new_wickets) + " wickets"

    def go_back(self, instance):
        self.manager.current = self.return_screen


# ---------------- SAVED PLAYERS SYSTEM ----------------

class PlayersListScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pick_mode = False
        self.pick_target = None

        title = Label(text="Players", font_size=22, color=OFF_WHITE, size_hint=(1, 0.1))

        self.search_input = TextInput(
            hint_text="Search player",
            multiline=False,
            size_hint=(1, 0.1),
            background_color=OFF_WHITE,
            foreground_color=DARK_GRAY
        )
        self.search_input.bind(text=self.on_search)

        self.scroll = ScrollView(size_hint=(1, 0.65))
        self.list_box = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.scroll.add_widget(self.list_box)

        add_btn = Button(text="Add New Player", size_hint=(1, 0.12), background_color=DARK_GRAY, color=OFF_WHITE)
        add_btn.bind(on_release=self.add_new_player)

        back_btn = Button(text="Back", size_hint=(1, 0.1), background_color=OFF_WHITE, color=DARK_GRAY)
        back_btn.bind(on_release=self.go_back)

        self.layout.add_widget(title)
        self.layout.add_widget(self.search_input)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(add_btn)
        self.layout.add_widget(back_btn)

    def on_pre_enter(self):
        self.search_input.text = ""
        self.refresh_list()

    def on_search(self, instance, value):
        self.refresh_list()

    def refresh_list(self):
        app = App.get_running_app()
        self.list_box.clear_widgets()
        query = self.search_input.text.strip().lower()

        for player in app.saved_players:
            if query == "" or query in player["name"].lower():
                btn = Button(
                    text=player["name"] + "  (" + str(player["matches"]) + " matches)",
                    size_hint=(1, None),
                    height=50,
                    background_color=DARK_GRAY,
                    color=OFF_WHITE
                )
                btn.bind(on_release=lambda instance, p=player: self.player_tapped(p))
                self.list_box.add_widget(btn)

    def player_tapped(self, player):
        app = App.get_running_app()
        if self.pick_mode:
            if self.pick_target == "team_a":
                app.team_a_players.append(player["name"])
            elif self.pick_target == "team_b":
                app.team_b_players.append(player["name"])
            self.pick_mode = False
            self.manager.current = "player_setup"
        else:
            profile_screen = self.manager.get_screen("player_profile")
            profile_screen.load_player(player)
            self.manager.current = "player_profile"

    def add_new_player(self, instance):
        app = App.get_running_app()
        name = self.search_input.text.strip()
        if name == "":
            return
        existing_names = [p["name"] for p in app.saved_players]
        if name not in existing_names:
            app.saved_players.append({
                "name": name,
                "matches": 0,
                "runs": 0,
                "wickets": 0,
                "best_score": 0,
                "best_bowling": "0-0",
                "history": []
            })
        self.search_input.text = ""
        self.refresh_list()

    def go_back(self, instance):
        self.manager.current = "home"


class PlayerProfileScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name_label = Label(text="", font_size=24, color=OFF_WHITE, size_hint=(1, 0.12))
        self.stats_label = Label(text="", font_size=16, color=OFF_WHITE, size_hint=(1, 0.3))

        self.history_scroll = ScrollView(size_hint=(1, 0.4))
        self.history_box = BoxLayout(orientation="vertical", spacing=8, size_hint_y=None)
        self.history_box.bind(minimum_height=self.history_box.setter("height"))
        self.history_scroll.add_widget(self.history_box)

        back_btn = Button(text="Back", size_hint=(1, 0.12), background_color=OFF_WHITE, color=DARK_GRAY)
        back_btn.bind(on_release=self.go_back)

        self.layout.add_widget(self.name_label)
        self.layout.add_widget(self.stats_label)
        self.layout.add_widget(self.history_scroll)
        self.layout.add_widget(back_btn)

    def load_player(self, player):
        self.name_label.text = player["name"]
        stats_text = "Matches: " + str(player["matches"])
        stats_text = stats_text + "\nTotal Runs: " + str(player["runs"])
        stats_text = stats_text + "\nTotal Wickets: " + str(player["wickets"])
        stats_text = stats_text + "\nBest Score: " + str(player["best_score"])
        stats_text = stats_text + "\nBest Bowling: " + player["best_bowling"]
        self.stats_label.text = stats_text

        self.history_box.clear_widgets()
        for entry in player["history"]:
            label = Label(text=entry, font_size=14, color=OFF_WHITE, size_hint=(1, None), height=30)
            self.history_box.add_widget(label)

    def go_back(self, instance):
        self.manager.current = "players_list"


# ---------------- CLUB SYSTEM ----------------

class ClubScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        title = Label(text="Clubs", font_size=22, color=OFF_WHITE, size_hint=(1, 0.1))

        self.club_name_input = TextInput(
            hint_text="New club name",
            multiline=False,
            size_hint=(1, 0.12),
            background_color=OFF_WHITE,
            foreground_color=DARK_GRAY
        )

        create_btn = Button(text="Create Club", size_hint=(1, 0.12), background_color=DARK_GRAY, color=OFF_WHITE)
        create_btn.bind(on_release=self.create_club)

        self.scroll = ScrollView(size_hint=(1, 0.5))
        self.list_box = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.scroll.add_widget(self.list_box)

        back_btn = Button(text="Back", size_hint=(1, 0.1), background_color=OFF_WHITE, color=DARK_GRAY)
        back_btn.bind(on_release=self.go_back)

        self.layout.add_widget(title)
        self.layout.add_widget(self.club_name_input)
        self.layout.add_widget(create_btn)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(back_btn)

    def on_pre_enter(self):
        self.refresh_list()

    def refresh_list(self):
        app = App.get_running_app()
        self.list_box.clear_widgets()
        for club in app.clubs:
            btn = Button(text=club["name"], size_hint=(1, None), height=50, background_color=DARK_GRAY, color=OFF_WHITE)
            btn.bind(on_release=lambda instance, c=club: self.open_club(c))
            self.list_box.add_widget(btn)

    def create_club(self, instance):
        app = App.get_running_app()
        name = self.club_name_input.text.strip()
        if name == "":
            return
        app.clubs.append({"name": name, "tournaments": [], "open_matches": []})
        self.club_name_input.text = ""
        self.refresh_list()

    def open_club(self, club):
        app = App.get_running_app()
        app.current_club = club
        detail_screen = self.manager.get_screen("club_detail")
        detail_screen.load_club(club)
        self.manager.current = "club_detail"

    def go_back(self, instance):
        self.manager.current = "home"


class ClubDetailScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.club = None

        self.title_label = Label(text="", font_size=22, color=OFF_WHITE, size_hint=(1, 0.1))

        self.tournament_input = TextInput(
            hint_text="New tournament name",
            multiline=False,
            size_hint=(1, 0.1),
            background_color=OFF_WHITE,
            foreground_color=DARK_GRAY
        )
        add_tournament_btn = Button(text="Add Tournament", size_hint=(1, 0.1), background_color=DARK_GRAY, color=OFF_WHITE)
        add_tournament_btn.bind(on_release=self.add_tournament)

        self.scroll = ScrollView(size_hint=(1, 0.5))
        self.list_box = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.scroll.add_widget(self.list_box)

        back_btn = Button(text="Back", size_hint=(1, 0.1), background_color=OFF_WHITE, color=DARK_GRAY)
        back_btn.bind(on_release=self.go_back)

        self.layout.add_widget(self.title_label)
        self.layout.add_widget(self.tournament_input)
        self.layout.add_widget(add_tournament_btn)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(back_btn)

    def load_club(self, club):
        self.club = club
        self.title_label.text = club["name"]
        self.refresh_list()

    def refresh_list(self):
        self.list_box.clear_widgets()
        for tournament_name in self.club["tournaments"]:
            label = Label(text="Tournament: " + tournament_name, font_size=16, color=OFF_WHITE, size_hint=(1, None), height=40)
            self.list_box.add_widget(label)
        for match_name in self.club["open_matches"]:
            label = Label(text="Open Match: " + match_name, font_size=16, color=OFF_WHITE, size_hint=(1, None), height=40)
            self.list_box.add_widget(label)

    def add_tournament(self, instance):
        name = self.tournament_input.text.strip()
        if name == "":
            return
        self.club["tournaments"].append(name)
        self.tournament_input.text = ""
        self.refresh_list()

    def go_back(self, instance):
        self.manager.current = "club_list"


# ---------------- ANNOUNCEMENTS ----------------

class AnnouncementScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        title = Label(text="Announcements", font_size=22, color=OFF_WHITE, size_hint=(1, 0.1))

        self.text_input = TextInput(
            hint_text="Announcement text (match/tournament details)",
            multiline=True,
            size_hint=(1, 0.2),
            background_color=OFF_WHITE,
            foreground_color=DARK_GRAY
        )

        post_btn = Button(text="Post Announcement", size_hint=(1, 0.12), background_color=DARK_GRAY, color=OFF_WHITE)
        post_btn.bind(on_release=self.post_announcement)

        self.scroll = ScrollView(size_hint=(1, 0.45))
        self.list_box = BoxLayout(orientation="vertical", spacing=15, size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.scroll.add_widget(self.list_box)

        back_btn = Button(text="Back", size_hint=(1, 0.1), background_color=OFF_WHITE, color=DARK_GRAY)
        back_btn.bind(on_release=self.go_back)

        self.layout.add_widget(title)
        self.layout.add_widget(self.text_input)
        self.layout.add_widget(post_btn)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(back_btn)

    def on_pre_enter(self):
        self.refresh_list()

    def post_announcement(self, instance):
        app = App.get_running_app()
        text = self.text_input.text.strip()
        if text == "":
            return
        app.announcements.append({"text": text, "confirmed_players": []})
        self.text_input.text = ""
        self.refresh_list()

    def refresh_list(self):
        app = App.get_running_app()
        self.list_box.clear_widgets()

        for announcement in app.announcements:
            item_box = BoxLayout(orientation="vertical", spacing=5, size_hint=(1, None), height=110)

            text_label = Label(text=announcement["text"], font_size=15, color=OFF_WHITE, size_hint=(1, 0.5))

            confirmed_text = "Confirmed: " + ", ".join(announcement["confirmed_players"]) if announcement["confirmed_players"] else "Confirmed: none yet"
            confirmed_label = Label(text=confirmed_text, font_size=13, color=OFF_WHITE, size_hint=(1, 0.2))

            name_input = TextInput(hint_text="Your name", multiline=False, size_hint=(1, 0.15), background_color=OFF_WHITE, foreground_color=DARK_GRAY)

            confirm_btn = Button(text="Confirm", size_hint=(1, 0.15), background_color=DARK_GRAY, color=OFF_WHITE)
            confirm_btn.bind(on_release=lambda instance, a=announcement, ti=name_input: self.confirm_player(a, ti))

            item_box.add_widget(text_label)
            item_box.add_widget(confirmed_label)
            item_box.add_widget(name_input)
            item_box.add_widget(confirm_btn)

            self.list_box.add_widget(item_box)

    def confirm_player(self, announcement, name_input):
        name = name_input.text.strip()
        if name == "":
            return
        if name not in announcement["confirmed_players"]:
            announcement["confirmed_players"].append(name)
        name_input.text = ""
        self.refresh_list()

    def go_back(self, instance):
        self.manager.current = "home"
