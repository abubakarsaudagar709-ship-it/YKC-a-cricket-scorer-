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


def calculate_par_result(team_a_history, team_b_runs, team_b_wickets, stoppage_over, stoppage_balls):
    target_key = str(stoppage_over) + "." + str(stoppage_balls)
    team_a_score_at_stage = None
    team_a_wickets_at_stage = None

    for entry in team_a_history:
        if entry["over"] == stoppage_over and entry["ball"] == stoppage_balls:
            team_a_score_at_stage = entry["runs"]
            team_a_wickets_at_stage = entry["wickets"]
            break

    if team_a_score_at_stage is None:
        closest_entry = None
        for entry in team_a_history:
            if entry["over"] < stoppage_over or (entry["over"] == stoppage_over and entry["ball"] <= stoppage_balls):
                closest_entry = entry
        if closest_entry is not None:
            team_a_score_at_stage = closest_entry["runs"]
            team_a_wickets_at_stage = closest_entry["wickets"]
        else:
            team_a_score_at_stage = 0
            team_a_wickets_at_stage = 0

    if team_b_runs > team_a_score_at_stage:
        margin = team_b_runs - team_a_score_at_stage
        return "team_b", margin, "runs"
    elif team_b_runs < team_a_score_at_stage:
        margin = team_a_score_at_stage - team_b_runs
        return "team_a", margin, "runs"
    else:
        if team_b_wickets < team_a_wickets_at_stage:
            return "team_b", 0, "fewer wickets lost"
        elif team_b_wickets > team_a_wickets_at_stage:
            return "team_a", 0, "fewer wickets lost"
        else:
            return "tie", 0, ""


class InningsBreakScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title_label = Label(text="", font_size=22, color=OFF_WHITE, size_hint=(1, 0.2))
        self.summary_label = Label(text="", font_size=18, color=OFF_WHITE, size_hint=(1, 0.3))
        self.layout.add_widget(self.title_label)
        self.layout.add_widget(self.summary_label)

    def show_break(self):
        app = App.get_running_app()

        for child in list(self.layout.children):
            self.layout.remove_widget(child)

        self.title_label = Label(text="Innings Break", font_size=22, color=OFF_WHITE, size_hint=(1, 0.2))
        summary_text = app.batting_team_name + " scored " + str(app.total_runs) + "/" + str(app.total_wickets)
        summary_text = summary_text + " in " + str(app.overs_completed) + "." + str(app.balls_this_over) + " overs"
        self.summary_label = Label(text=summary_text, font_size=18, color=OFF_WHITE, size_hint=(1, 0.3))

        target_text = "Target for " + app.bowling_team_name + ": " + str(app.total_runs + 1)
        target_label = Label(text=target_text, font_size=18, color=OFF_WHITE, size_hint=(1, 0.15))

        start_btn = Button(text="Start Second Innings", size_hint=(1, 0.2), background_color=DARK_GRAY, color=OFF_WHITE)
        start_btn.bind(on_release=self.start_second_innings)

        self.layout.add_widget(self.title_label)
        self.layout.add_widget(self.summary_label)
        self.layout.add_widget(target_label)
        self.layout.add_widget(start_btn)

    def start_second_innings(self, instance):
        app = App.get_running_app()

        app.innings_one_history = list(app.ball_history)
        app.innings_one_runs = app.total_runs
        app.innings_one_wickets = app.total_wickets
        app.target_runs = app.total_runs + 1

        old_batting = app.batting_team_name
        old_bowling = app.bowling_team_name
        old_batting_players = app.batting_players
        old_bowling_players = app.bowling_players

        app.batting_team_name = old_bowling
        app.bowling_team_name = old_batting
        app.batting_players = old_bowling_players
        app.bowling_players = old_batting_players

        app.available_batsmen = list(app.batting_players)
        app.ball_history = []
        app.total_runs = 0
        app.total_wickets = 0
        app.balls_this_over = 0
        app.overs_completed = 0
        app.current_innings = 2

        opener_screen = self.manager.get_screen("select_openers")
        opener_screen.start_selection()
        self.manager.current = "select_openers"


class MatchResultScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def show_result(self, stopped_early=False, stoppage_over=None, stoppage_balls=None):
        self.layout.clear_widgets()
        app = App.get_running_app()

        if stopped_early and app.current_innings == 2:
            winner, margin, reason = calculate_par_result(
                app.innings_one_history,
                app.total_runs,
                app.total_wickets,
                stoppage_over,
                stoppage_balls
            )
            if winner == "team_b":
                result_text = app.batting_team_name + " won"
                if margin > 0:
                    result_text = result_text + " by " + str(margin) + " runs (DLS method)"
                else:
                    result_text = result_text + " (DLS method, " + reason + ")"
            elif winner == "team_a":
                result_text = app.bowling_team_name + " won"
                if margin > 0:
                    result_text = result_text + " by " + str(margin) + " runs (DLS method)"
                else:
                    result_text = result_text + " (DLS method, " + reason + ")"
            else:
                result_text = "Match tied (DLS method)"
        else:
            if app.current_innings == 2:
                if app.total_runs >= app.target_runs:
                    wickets_left = 10 - app.total_wickets
                    result_text = app.batting_team_name + " won by " + str(wickets_left) + " wickets"
                elif app.total_runs == app.target_runs - 1:
                    result_text = "Match tied"
                else:
                    margin = app.target_runs - 1 - app.total_runs
                    result_text = app.bowling_team_name + " won by " + str(margin) + " runs"
            else:
                result_text = "Match finished"

        title = Label(text="Match Result", font_size=24, color=OFF_WHITE, size_hint=(1, 0.2))
        result_label = Label(text=result_text, font_size=20, color=OFF_WHITE, size_hint=(1, 0.3))

        self.layout.add_widget(title)
        self.layout.add_widget(result_label)


class TestDayScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def show_day_options(self):
        self.layout.clear_widgets()
        app = App.get_running_app()

        title_text = "Day " + str(app.test_day_number) + " - " + str(app.overs_completed) + " overs bowled"
        title = Label(text=title_text, font_size=20, color=OFF_WHITE, size_hint=(1, 0.15))

        score_text = app.batting_team_name + " " + str(app.total_runs) + "/" + str(app.total_wickets)
        score_label = Label(text=score_text, font_size=18, color=OFF_WHITE, size_hint=(1, 0.15))

        continue_btn = Button(text="Continue Same Day", size_hint=(1, 0.15), background_color=DARK_GRAY, color=OFF_WHITE)
        continue_btn.bind(on_release=self.continue_same_day)

        end_day_btn = Button(text="End Day " + str(app.test_day_number), size_hint=(1, 0.15), background_color=DARK_GRAY, color=OFF_WHITE)
        end_day_btn.bind(on_release=self.end_day)

        declare_btn = Button(text="Declare Innings", size_hint=(1, 0.15), background_color=DARK_GRAY, color=OFF_WHITE)
        declare_btn.bind(on_release=self.declare_innings)

        self.layout.add_widget(title)
        self.layout.add_widget(score_label)
        self.layout.add_widget(continue_btn)
        self.layout.add_widget(end_day_btn)
        self.layout.add_widget(declare_btn)

    def continue_same_day(self, instance):
        self.manager.current = "scoring"

    def end_day(self, instance):
        app = App.get_running_app()
        day_record = {
            "day": app.test_day_number,
            "team": app.batting_team_name,
            "runs": app.total_runs,
            "wickets": app.total_wickets,
            "overs": str(app.overs_completed) + "." + str(app.balls_this_over)
        }
        app.test_day_scores.append(day_record)
        app.test_day_number = app.test_day_number + 1
        app.overs_today = 0

        self.layout.clear_widgets()
        locked_text = "Day " + str(day_record["day"]) + " ended.\n"
        locked_text = locked_text + day_record["team"] + " " + str(day_record["runs"]) + "/" + str(day_record["wickets"])
        locked_text = locked_text + " (" + day_record["overs"] + " overs)"

        label = Label(text=locked_text, font_size=18, color=OFF_WHITE, size_hint=(1, 0.4))
        start_next_btn = Button(text="Start Day " + str(app.test_day_number), size_hint=(1, 0.15), background_color=DARK_GRAY, color=OFF_WHITE)
        start_next_btn.bind(on_release=self.start_next_day)

        self.layout.add_widget(label)
        self.layout.add_widget(start_next_btn)

    def start_next_day(self, instance):
        self.manager.current = "scoring"

    def declare_innings(self, instance):
        app = App.get_running_app()
        innings_break_screen = self.manager.get_screen("innings_break")
        innings_break_screen.show_break()
        self.manager.current = "innings_break"
