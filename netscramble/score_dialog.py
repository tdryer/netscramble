from gi.repository import Gtk, GObject #pylint: disable=E0611
import time
import json

from netscramble import res, data

class ScoreModel():
    """Stores and reads high scores.

    file_path is assumed to exist and be writeable.
    """

    def __init__(self, file_path):
        self.file_path = file_path

    def add_score(self, new_score):
        """Add score dict to file."""
        scores_list = [score for score in self.get_scores()]
        scores_list.append(new_score)
        f = open(self.file_path, "w")
        json.dump(scores_list, f)
        f.close()

    def get_scores(self):
        """Generate score dicts from file."""
        f = open(self.file_path, "r")
        try:
            scores_list = json.load(f) if f else []
        except ValueError:
            # scores file is empty or corrupt
            scores_list = []
        finally:
            f.close()
        for score in scores_list:
            yield score


class SimpleTreeView():
    """A TreeView wrapper providing a simple interface."""

    def __init__(self, tree_view, columns):
        self._tree_view = tree_view
        self._columns = columns

        # create the list store
        types = []
        for col in columns:
            types.append(col["type"])
            if "subtype" in col:
                types.append(col["subtype"])
        self._list_store = Gtk.ListStore.new(types)

        col_num = 0
        for col in columns:
            # add renderer
            tvcol = Gtk.TreeViewColumn(col["label"],
                                     Gtk.CellRendererText(), text=col_num)
            self._tree_view.append_column(tvcol)
            # make the column sortable
            if "subtype" in col:
                col_num += 1
            tvcol.set_sort_column_id(col_num)
            col_num += 1

        self._tree_view.set_model(self._list_store)

    def set_sorted_column(self, num):
        # TODO: by label
        self._list_store.set_sort_column_id(num, Gtk.SortType.DESCENDING)

    def append(self, *args):
        args = list(args)
        args.reverse()
        res = []
        for col in self._columns:
            if "subtype" not in col:
                res.append(args.pop())
            else:
                res.append(col["gen_f"](args[-1]))
                res.append(args.pop())

        # return the iter
        return self._list_store.append(res)


class ScoreDialog():
    """The high scores dialog."""

    def __init__(self, parent_window, new_game_f):
        self._new_game_f = new_game_f

        self.score_model = ScoreModel(data("scores.json"))

        builder = Gtk.Builder()
        builder.add_from_file(res("glade/scoresdialog.glade"))
        builder.connect_signals(self)
        self.window = builder.get_object("scores_dialog")
        self.window.set_transient_for(parent_window)

        self.message_label = builder.get_object("message_label")
        self.score_view = builder.get_object("score_view")

        self._stv = SimpleTreeView(self.score_view, [
            {"label": "Name", "type": GObject.TYPE_STRING},
            {"label": "Date", "type": GObject.TYPE_STRING,
             "subtype": GObject.TYPE_INT, "gen_f": self.format_unix_date},
            {"label": "Clicks", "type": GObject.TYPE_INT},
            {"label": "Time", "type": GObject.TYPE_STRING,
             "subtype": GObject.TYPE_INT, "gen_f": self.format_time},
        ])
        self.load_scores()
        self._stv.set_sorted_column(2)
        #selection = self.score_view.get_selection()
        #selection.select_iter(d)

    def load_scores(self):
        """Load scores from file into list store."""
        for s in self.score_model.get_scores():
            self.add_score(s["name"], s["date"], s["clicks"], s["time"])

    def save_score(self, name, unix_date, clicks, time_secs):
        """Append score to the scores file."""
        self.score_model.add_score({"name": name, "date": unix_date,
                                    "clicks": clicks, "time": time_secs})

    @staticmethod
    def get_unix_date():
        return time.time()

    @staticmethod
    def format_unix_date(unix_date):
        return time.strftime("%b %e, %Y", time.localtime(unix_date))

    @staticmethod
    def format_time(seconds):
        return "{}m {}s".format(seconds / 60, seconds % 60)

    def show(self):
        """Show the scores window."""
        # show before set_text fixes wrapping, but causes ugly jerk
        self.message_label.set_text("")
        self.window.show()

    def show_and_add_score(self, name, unix_date, clicks, time_secs):
        """Add a new score, select it in the TreeView, and show the dialog."""
        msg = "Congratulations!"
        scores_list = list(self.score_model.get_scores())
        clicks_list = [s["clicks"] for s in scores_list]
        clicks_list.sort()
        if len(clicks_list) == 0 or clicks < clicks_list[0]:
            msg += " This is your best click count."
        time_list = [s["time"] for s in scores_list]
        time_list.sort()
        if len(clicks_list) == 0 or time_secs < time_list[0]:
            msg += " This is your best time."
        self.message_label.set_text(msg)
        # TODO: msg should be persisted while until new game is started
        self.add_score(name, unix_date, clicks, time_secs)
        self.save_score(name, unix_date, clicks, time_secs)
        self.window.show()

    def add_score(self, name, unix_date, clicks, time_secs):
        """Add a score to the TreeView."""
        tree_iter = self._stv.append(name, unix_date, clicks, time_secs)
        selection = self.score_view.get_selection()
        selection.select_iter(tree_iter)

    def on_close_window_action_activate(self, action, data=None):
        self.window.hide()

    def on_new_game_action_activate(self, action, data=None):
        self._new_game_f()
        self.window.hide()
