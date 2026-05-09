import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import vlc
import os
import random
import math
import time
from PIL import Image, ImageDraw, ImageTk, ImageColor, ImageFont

class WADX:
    def __init__(self, root):
        self.root = root
        self.root.title("JamVault")
        image = Image.open("icon.png")
        photo = ImageTk.PhotoImage(image)
        root.iconphoto(True, photo)
        self.root.config(bg="#d8d8d8")
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.resizable(False, False)

        # Playback state
        self.loop_mode = 0  # 0=off,1=one,2=all
        self.shuffle_on = False
        self.is_playing = False
        self.updating_slider = False

        self.playlist = []
        self.current_index = -1
        self.temp_library = False

        self.load_images()

        menubar = tk.Menu(root, background='#d8d8d8')
        root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0, background='#d8d8d8')
        file_menu.add_command(label="New Library", command=self.new_library)
        file_menu.add_command(label="Load Library", command=self.load_library_dialog)
        file_menu.add_command(label="Save", command=self.save_playlist_as)
        file_menu.add_command(label="Load Main Library", command=lambda: self.load_playlist("library.m3u"))
        menubar.add_cascade(label="Files", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0, background='#d8d8d8')
        tools_menu.add_command(label="Find", command=self.open_find_window)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0, background='#d8d8d8')
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.seek_var = tk.DoubleVar()
        self.seekbar = tk.Scale(root, variable=self.seek_var, from_=0, to=1000,
                                orient=tk.HORIZONTAL, length=400,
                                command=self.seek, showvalue=0, fg="#333333")
        self.seekbar.pack(pady=10)

        control_panel = tk.Frame(root, background='#d8d8d8')
        control_panel.pack(pady=20)

        self.prev_btn = tk.Button(control_panel, image=self.img_back, bg="#d8d8d8", borderwidth=0,
                                  command=self.prev_track)
        if not self.img_back:
            self.prev_btn.config(text="Prev")
        self.prev_btn.pack(side=tk.LEFT, padx=3)

        self.play_pause_btn = tk.Button(control_panel, image=self.img_play, bg="#d8d8d8", borderwidth=0,
                                        command=self.play_pause)
        if not self.img_play:
            self.play_pause_btn.config(text="Play")
        self.play_pause_btn.pack(side=tk.LEFT, padx=3)

        self.next_btn = tk.Button(control_panel, image=self.img_forward, bg="#d8d8d8", borderwidth=0,
                                  command=self.next_track)
        if not self.img_forward:
            self.next_btn.config(text="Next")
        self.next_btn.pack(side=tk.LEFT, padx=3)

        self.loop_btn = tk.Button(control_panel, image=self.img_loop_off, bg="#d8d8d8", borderwidth=0,
                                  command=self.toggle_loop_mode)
        if not self.img_loop_off:
            self.loop_btn.config(text="Loop Off")
        self.loop_btn.pack(side=tk.LEFT, padx=10)

        self.shuffle_btn = tk.Button(control_panel, image=self.img_shuffle_off, bg="#d8d8d8", borderwidth=0,
                                     command=self.toggle_shuffle)
        if not self.img_shuffle_off:
            self.shuffle_btn.config(text="Shuffle Off")
        self.shuffle_btn.pack(side=tk.LEFT, padx=3)

        self.eq_frame = tk.Frame(root, bg="black", height=100)
        self.eq_frame.pack(fill=tk.X, pady=(10, 10))

        self.eq_canvas = tk.Canvas(self.eq_frame, bg="black", height=100)
        self.eq_canvas.pack(fill=tk.X, expand=True)

        self.num_bars = 20
        self.bar_width = 15
        self.bar_spacing = 5
        self.eq_bars = []
        for i in range(self.num_bars):
            x0 = i * (self.bar_width + self.bar_spacing)
            y0 = 100
            x1 = x0 + self.bar_width
            y1 = y0
            bar = self.eq_canvas.create_rectangle(x0, y0, x1, y1, fill="#4caf50", outline="")
            self.eq_bars.append(bar)

        self.playlist_frame = tk.Frame(root, bg="#d8d8d8")
        self.playlist_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        self.playlist_scrollbar = tk.Scrollbar(self.playlist_frame)
        self.playlist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.playlist_listbox = tk.Listbox(self.playlist_frame, yscrollcommand=self.playlist_scrollbar.set, height=8, width=60)
        self.playlist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.playlist_listbox.bind('<<ListboxSelect>>', self.playlist_select)

        self.playlist_scrollbar.config(command=self.playlist_listbox.yview)

        self.buttons_panel = tk.Frame(root, background='#d8d8d8')
        self.buttons_panel.pack(pady=(0, 20))

        self.add_songs_btn = tk.Button(self.buttons_panel, image=self.img_add, bg="#d8d8d8",
                                       command=self.add_songs)
        if not self.img_add:
            self.add_songs_btn.config(text="Add")
        self.add_songs_btn.pack(side=tk.LEFT, padx=5)

        self.rename_song_btn = tk.Button(self.buttons_panel, image=self.img_rename, bg="#d8d8d8",
                                        command=self.rename_song)
        if not self.img_rename:
            self.rename_song_btn.config(text="Rename")
        self.rename_song_btn.pack(side=tk.LEFT, padx=5)

        self.delete_song_btn = tk.Button(self.buttons_panel, image=self.img_remove, bg="#d8d8d8",
                                         command=self.delete_song)
        if not self.img_remove:
            self.delete_song_btn.config(text="Remove")
        self.delete_song_btn.pack(side=tk.LEFT, padx=5)

        self.move_up_btn = tk.Button(self.buttons_panel, image=self.img_up, bg="#d8d8d8",
                                     command=self.move_song_up)
        if not self.img_up:
            self.move_up_btn.config(text="Up")
        self.move_up_btn.pack(side=tk.LEFT, padx=5)

        self.move_down_btn = tk.Button(self.buttons_panel, image=self.img_down, bg="#d8d8d8",
                                       command=self.move_song_down)
        if not self.img_down:
            self.move_down_btn.config(text="Down")
        self.move_down_btn.pack(side=tk.LEFT, padx=5)

        events = self.player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)

        self.current_eq_heights = [0] * self.num_bars  # store current heights for smooth animation
        self.update_seekbar()
        self.animate_eq()

        self.load_playlist("library.m3u")

        self.find_window = None

    def load_images(self):
        def load_image(path):
            try:
                return tk.PhotoImage(file=path)
            except Exception:
                return None

        self.img_play = load_image("gui/play.png")
        self.img_pause = load_image("gui/pause.png")
        self.img_forward = load_image("gui/forward.png")
        self.img_back = load_image("gui/rewind.png")
        self.img_loop_off = load_image("gui/loop.png")
        self.img_loop_one = load_image("gui/loop1.png")
        self.img_loop_all = load_image("gui/loopall.png")
        self.img_shuffle_off = load_image("gui/shuffle.png")
        self.img_shuffle_on = load_image("gui/shuffleon.png")

        self.img_add = load_image("gui/add.png")
        self.img_rename = load_image("gui/rename.png")  # <-- New rename image
        self.img_remove = load_image("gui/remove.png")
        self.img_up = load_image("gui/up.png")
        self.img_down = load_image("gui/down.png")

    def get_song_name_from_path(self, path):
        filename = os.path.basename(path)
        name, _ = os.path.splitext(filename)
        return name

    def new_library(self):
        self.playlist.clear()
        self.playlist_listbox.delete(0, tk.END)
        self.current_index = -1
        self.is_playing = False
        if self.player.is_playing():
            self.player.stop()
        self.temp_library = True
        self.save_playlist_as("tmp.m3u")

    def load_library_dialog(self):
        filename = filedialog.askopenfilename(defaultextension=".m3u", filetypes=[("M3U Playlist", "*.m3u")])
        if filename:
            self.load_playlist(filename)

    def save_playlist_as(self, filename=None):
        if not filename:
            filename = filedialog.asksaveasfilename(defaultextension=".m3u", filetypes=[("M3U Playlist", "*.m3u")])
            if not filename:
                return
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                for path, name in self.playlist:
                    f.write(f"#EXTINF:-1,{name}\n{path}\n")
            messagebox.showinfo("Save Playlist", f"Playlist saved to:\n{filename}")
            self.temp_library = False
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save playlist:\n{str(e)}")

    def load_playlist(self, filename):
        if self.temp_library and filename != "tmp.m3u" and os.path.isfile("tmp.m3u"):
            try:
                os.remove("tmp.m3u")
            except Exception:
                pass
            self.temp_library = False

        if not os.path.isfile(filename):
            messagebox.showwarning("Playlist Load", f"Playlist file not found:\n{filename}")
            return
        self.playlist.clear()
        self.playlist_listbox.delete(0, tk.END)
        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            if not lines or lines[0] != "#EXTM3U":
                messagebox.showwarning("Playlist Error", "Invalid M3U playlist format.")
                return
            i = 1
            while i < len(lines) - 1:
                extinf = lines[i]
                path = lines[i + 1]
                i += 2
                if extinf.startswith("#EXTINF:"):
                    comma_index = extinf.find(",")
                    name = extinf[comma_index+1:] if comma_index != -1 else os.path.basename(path)
                    self.playlist.append([path, name])
                    self.playlist_listbox.insert(tk.END, name)
        self.current_index = -1
        self.is_playing = False
        if self.player.is_playing():
            self.player.stop()
        self.play_pause_btn.config(image=self.img_play if self.img_play else None)
        if not self.img_play:
            self.play_pause_btn.config(text="Play")
        self.reset_eq_bars()

    def save_playlist(self):
        filename = "tmp.m3u" if self.temp_library else "library.m3u"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                for path, name in self.playlist:
                    f.write(f"#EXTINF:-1,{name}\n{path}\n")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save playlist:\n{str(e)}")

    def add_song_to_playlist(self, filepath):
        name = self.get_song_name_from_path(filepath)
        self.playlist.append([filepath, name])
        self.playlist_listbox.insert(tk.END, name)
        self.save_playlist()

    def add_songs(self):
        filetypes = [("Audio files", "*.mp3 *.wav *.flac")]
        files = filedialog.askopenfilenames(title="Add Songs", filetypes=filetypes)
        if not files:
            return
        for filepath in files:
            if any(filepath == song[0] for song in self.playlist):
                continue
            self.add_song_to_playlist(filepath)

    def delete_song(self):
        selection = self.playlist_listbox.curselection()
        if not selection:
            messagebox.showinfo("Delete Song", "Please select a song to delete.")
            return
        index = selection[0]
        del self.playlist[index]
        self.playlist_listbox.delete(index)
        self.save_playlist()
        if self.current_index == index:
            self.current_index = -1
            self.player.stop()
            self.is_playing = False
            self.play_pause_btn.config(image=self.img_play if self.img_play else None)
            if not self.img_play:
                self.play_pause_btn.config(text="Play")
            self.reset_eq_bars()
        elif self.current_index > index:
            self.current_index -= 1

    def move_song_up(self):
        selection = self.playlist_listbox.curselection()
        if not selection:
            messagebox.showinfo("Move Song", "Please select a song to move.")
            return
        index = selection[0]
        if index == 0:
            return
        self.playlist[index], self.playlist[index - 1] = self.playlist[index - 1], self.playlist[index]
        name = self.playlist_listbox.get(index)
        self.playlist_listbox.delete(index)
        self.playlist_listbox.insert(index - 1, name)
        self.playlist_listbox.selection_set(index - 1)
        self.save_playlist()
        if self.current_index == index:
            self.current_index -= 1
        elif self.current_index == index - 1:
            self.current_index += 1

    def move_song_down(self):
        selection = self.playlist_listbox.curselection()
        if not selection:
            messagebox.showinfo("Move Song", "Please select a song to move.")
            return
        index = selection[0]
        if index == len(self.playlist) - 1:
            return
        self.playlist[index], self.playlist[index + 1] = self.playlist[index + 1], self.playlist[index]
        name = self.playlist_listbox.get(index)
        self.playlist_listbox.delete(index)
        self.playlist_listbox.insert(index + 1, name)
        self.playlist_listbox.selection_set(index + 1)
        self.save_playlist()
        if self.current_index == index:
            self.current_index += 1
        elif self.current_index == index + 1:
            self.current_index -= 1

    def playlist_select(self, event):
        if not self.playlist_listbox.curselection():
            return
        index = self.playlist_listbox.curselection()[0]
        self.play_song_by_index(index)

    def play_song_by_index(self, index):
        if index < 0 or index >= len(self.playlist):
            return
        path, name = self.playlist[index]
        if not os.path.isfile(path):
            answer = messagebox.askyesno("File Missing",
                                         f"The file:\n{path}\ndoes not exist.\nDo you want to remove it from the playlist?")
            if answer:
                del self.playlist[index]
                self.playlist_listbox.delete(index)
                self.save_playlist()
                if self.current_index == index:
                    self.current_index = -1
                    self.player.stop()
                    self.is_playing = False
                    self.play_pause_btn.config(image=self.img_play if self.img_play else None)
                    if not self.img_play:
                        self.play_pause_btn.config(text="Play")
                    self.reset_eq_bars()
                elif self.current_index > index:
                    self.current_index -= 1
            return
        media = self.instance.media_new(path)
        self.player.set_media(media)
        self.player.play()
        self.is_playing = True
        self.play_pause_btn.config(image=self.img_pause if self.img_pause else None)
        if not self.img_pause:
            self.play_pause_btn.config(text="Pause")
        self.current_index = index
        self.playlist_listbox.selection_clear(0, tk.END)
        self.playlist_listbox.selection_set(index)
        self.playlist_listbox.see(index)

    def play_pause(self):
        if self.is_playing:
            self.player.pause()
            self.play_pause_btn.config(image=self.img_play if self.img_play else None)
            if not self.img_play:
                self.play_pause_btn.config(text="Play")
            self.is_playing = False
        else:
            self.player.play()
            self.play_pause_btn.config(image=self.img_pause if self.img_pause else None)
            if not self.img_pause:
                self.play_pause_btn.config(text="Pause")
            self.is_playing = True

    def prev_track(self):
        if not self.playlist:
            return
        if self.shuffle_on:
            self.play_random_track()
            return
        if self.current_index <= 0:
            if self.loop_mode == 2:
                self.play_song_by_index(len(self.playlist) - 1)
        else:
            self.play_song_by_index(self.current_index - 1)

    def next_track(self):
        if not self.playlist:
            return
        if self.shuffle_on:
            self.play_random_track()
            return
        if self.current_index == -1 or self.current_index >= len(self.playlist) - 1:
            if self.loop_mode == 2:
                self.play_song_by_index(0)
        else:
            self.play_song_by_index(self.current_index + 1)

    def play_random_track(self):
        if not self.playlist:
            return
        index = random.randint(0, len(self.playlist) - 1)
        self.play_song_by_index(index)

    def toggle_loop_mode(self):
        self.loop_mode = (self.loop_mode + 1) % 3
        if self.loop_mode == 0:
            self.loop_btn.config(image=self.img_loop_off if self.img_loop_off else None)
            if not self.img_loop_off:
                self.loop_btn.config(text="Loop Off")
        elif self.loop_mode == 1:
            self.loop_btn.config(image=self.img_loop_one if self.img_loop_one else None)
            if not self.img_loop_one:
                self.loop_btn.config(text="Loop One")
        elif self.loop_mode == 2:
            self.loop_btn.config(image=self.img_loop_all if self.img_loop_all else None)
            if not self.img_loop_all:
                self.loop_btn.config(text="Loop All")

    def toggle_shuffle(self):
        self.shuffle_on = not self.shuffle_on
        if self.shuffle_on:
            self.shuffle_btn.config(image=self.img_shuffle_on if self.img_shuffle_on else None)
            if not self.img_shuffle_on:
                self.shuffle_btn.config(text="Shuffle On")
        else:
            self.shuffle_btn.config(image=self.img_shuffle_off if self.img_shuffle_off else None)
            if not self.img_shuffle_off:
                self.shuffle_btn.config(text="Shuffle Off")

    def seek(self, val):
        if not self.player:
            return
        if self.updating_slider:
            return
        pos = float(val) / 1000.0
        try:
            self.player.set_position(pos)
        except Exception:
            pass

    def update_seekbar(self):
        if self.player and self.is_playing:
            try:
                pos = self.player.get_position()
                if pos == -1:
                    pos = 0
                self.updating_slider = True
                self.seek_var.set(pos * 1000)
                self.updating_slider = False
            except Exception:
                pass
        self.root.after(500, self.update_seekbar)

    def _on_end_reached(self, event):
        if self.loop_mode == 1:
            self.play_song_by_index(self.current_index)  # Loop current song
        elif self.shuffle_on:
            self.play_random_track()
        elif self.loop_mode == 2:
            next_index = (self.current_index + 1) % len(self.playlist) if self.playlist else -1
            if next_index != -1:
                self.play_song_by_index(next_index)
        else:
            next_index = self.current_index + 1
            if next_index < len(self.playlist):
                self.play_song_by_index(next_index)
            else:
                self.is_playing = False
                self.play_pause_btn.config(image=self.img_play if self.img_play else None)
                if not self.img_play:
                    self.play_pause_btn.config(text="Play")
                self.reset_eq_bars()

    def animate_eq(self):
        if self.is_playing:
            for i in range(self.num_bars):
                new_height = random.randint(10, 100)
                current_height = self.current_eq_heights[i]
                diff = new_height - current_height
                step = diff * 0.1
                current_height += step
                current_height = max(10, min(100, current_height))
                self.current_eq_heights[i] = current_height

                x0 = i * (self.bar_width + self.bar_spacing)
                y0 = 100 - current_height
                x1 = x0 + self.bar_width
                y1 = 100
                self.eq_canvas.coords(self.eq_bars[i], x0, y0, x1, y1)
        else:
            self.reset_eq_bars()
        self.root.after(30, self.animate_eq)

    def reset_eq_bars(self):
        for i in range(self.num_bars):
            x0 = i * (self.bar_width + self.bar_spacing)
            y0 = 100
            x1 = x0 + self.bar_width
            y1 = y0
            self.eq_canvas.coords(self.eq_bars[i], x0, y0, x1, y1)
            self.current_eq_heights[i] = 0

    def open_find_window(self):
        if self.find_window and self.find_window.winfo_exists():
            self.find_window.lift()
            return
        self.find_window = tk.Toplevel(self.root)
        self.find_window.title("Find")
        self.find_window.geometry("300x100")
        self.find_window.config(bg="#d8d8d8")

        label = tk.Label(self.find_window, text="Find song:", bg="#d8d8d8")
        label.pack(pady=5)

        self.find_entry = tk.Entry(self.find_window)
        self.find_entry.pack(pady=5)
        self.find_entry.bind('<Return>', self.perform_find)

        find_btn = tk.Button(self.find_window, text="Find", command=self.perform_find)
        find_btn.pack(pady=5)

    def perform_find(self, event=None):
        query = self.find_entry.get().strip().lower()
        if not query:
            return
        for i, (path, name) in enumerate(self.playlist):
            if query in name.lower():
                self.playlist_listbox.selection_clear(0, tk.END)
                self.playlist_listbox.selection_set(i)
                self.playlist_listbox.see(i)
                break
        self.find_window.lift()

    def show_about(self):
        messagebox.showinfo("About", "JamVault Beta\nVersion: 0.8.1\nCreated by: Daniel Armstrong\n(C)2025 Daniel Armstrong")

    def on_close(self):
        self.player.stop()
        self.root.destroy()

    def rename_song(self):
        selection = self.playlist_listbox.curselection()
        if not selection:
            messagebox.showinfo("Rename Song", "Please select a song to rename.")
            return
        index = selection[0]
        current_name = self.playlist[index][1]
        new_name = simpledialog.askstring("Rename Song", "Enter new name:", initialvalue=current_name, parent=self.root)
        if new_name and new_name.strip():
            new_name = new_name.strip()
            self.playlist[index][1] = new_name
            self.playlist_listbox.delete(index)
            self.playlist_listbox.insert(index, new_name)
            self.playlist_listbox.selection_set(index)
            self.save_playlist()

if __name__ == "__main__":
    root = tk.Tk()
    app = WADX(root)
    root.mainloop()
