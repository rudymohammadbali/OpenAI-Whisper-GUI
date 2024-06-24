import difflib
import os
import sys
import time
from typing import Literal

import customtkinter
import customtkinter as ctk
from PIL import Image, ImageTk
from customtkinter import filedialog as fd

from src.functions import DROPDOWN, FONTS, ICONS, save_config, change_theme, load_config
from src.py_win_style import set_opacity

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))


class CTkScrollableDropdownFrame(ctk.CTkToplevel):

    def __init__(self, attach, x=None, y=None, button_color=None, height: int = 200, width: int = None,
                 fg_color=None, button_height: int = 20, justify="center", scrollbar_button_color=None,
                 scrollbar=True, scrollbar_button_hover_color=None, frame_border_width=2, values=[],
                 command=None, image_values=[], alpha: float = 0.97, frame_corner_radius=20, double_click=False,
                 resize=True, frame_border_color=None, text_color=None, autocomplete=False, **button_kwargs):

        super().__init__(takefocus=1)

        self.focus()
        self.lift()
        self.alpha = alpha
        self.attach = attach
        self.corner = frame_corner_radius
        self.padding = 0
        self.focus_something = False
        self.disable = True
        self.update()

        if sys.platform.startswith("win"):
            self.after(100, lambda: self.overrideredirect(True))
            self.transparent_color = self._apply_appearance_mode(self._fg_color)
            self.attributes("-transparentcolor", self.transparent_color)
        elif sys.platform.startswith("darwin"):
            self.overrideredirect(True)
            self.transparent_color = 'systemTransparent'
            self.attributes("-transparent", True)
            self.focus_something = True
        else:
            self.overrideredirect(True)
            self.transparent_color = '#000001'
            self.corner = 0
            self.padding = 18
            self.withdraw()

        self.hide = True
        self.attach.bind('<Configure>', lambda e: self._withdraw() if not self.disable else None, add="+")
        self.attach.winfo_toplevel().bind('<Configure>', lambda e: self._withdraw() if not self.disable else None,
                                          add="+")
        self.attach.winfo_toplevel().bind("<ButtonPress>", lambda e: self._withdraw() if not self.disable else None,
                                          add="+")

        self.attributes('-alpha', 0)
        self.disable = False
        self.fg_color = ctk.ThemeManager.theme["CTkFrame"]["fg_color"] if fg_color is None else fg_color
        self.scroll_button_color = ctk.ThemeManager.theme["CTkScrollbar"][
            "button_color"] if scrollbar_button_color is None else scrollbar_button_color
        self.scroll_hover_color = ctk.ThemeManager.theme["CTkScrollbar"][
            "button_hover_color"] if scrollbar_button_hover_color is None else scrollbar_button_hover_color
        self.frame_border_color = ctk.ThemeManager.theme["CTkFrame"][
            "border_color"] if frame_border_color is None else frame_border_color
        self.button_color = ctk.ThemeManager.theme["CTkFrame"][
            "top_fg_color"] if button_color is None else button_color
        self.text_color = ctk.ThemeManager.theme["CTkLabel"][
            "text_color"] if text_color is None else text_color

        if scrollbar is False:
            self.scroll_button_color = self.fg_color
            self.scroll_hover_color = self.fg_color

        self.frame = ctk.CTkScrollableFrame(self, bg_color=self.transparent_color, fg_color=self.fg_color,
                                            scrollbar_button_hover_color=self.scroll_hover_color,
                                            corner_radius=self.corner, border_width=frame_border_width,
                                            scrollbar_button_color=self.scroll_button_color,
                                            border_color=self.frame_border_color)
        self.frame._scrollbar.grid_configure(padx=3)
        self.frame.pack(expand=True, fill="both")
        self.dummy_entry = ctk.CTkEntry(self.frame, fg_color="transparent", border_width=0, height=1, width=1)
        self.no_match = ctk.CTkLabel(self.frame, text="No Match")
        self.height = height
        self.height_new = height
        self.width = width
        self.command = command
        self.fade = False
        self.resize = resize
        self.autocomplete = autocomplete
        self.var_update = ctk.StringVar()
        self.appear = False

        if justify.lower() == "left":
            self.justify = "w"
        elif justify.lower() == "right":
            self.justify = "e"
        else:
            self.justify = "c"

        self.button_height = button_height
        self.values = values
        self.button_num = len(self.values)
        self.image_values = None if len(image_values) != len(self.values) else image_values

        self.resizable(width=False, height=False)
        self.transient(self.master)
        self._init_buttons(**button_kwargs)

        # Add binding for different ctk widgets
        if double_click or self.attach.winfo_name().startswith("!ctkentry") or self.attach.winfo_name().startswith(
                "!ctkcombobox"):
            self.attach.bind('<Double-Button-1>', lambda e: self._iconify(), add="+")
        else:
            self.attach.bind('<Button-1>', lambda e: self._iconify(), add="+")

        if self.attach.winfo_name().startswith("!ctkcombobox"):
            self.attach._canvas.tag_bind("right_parts", "<Button-1>", lambda e: self._iconify())
            self.attach._canvas.tag_bind("dropdown_arrow", "<Button-1>", lambda e: self._iconify())
            if self.command is None:
                self.command = self.attach.set

        if self.attach.winfo_name().startswith("!ctkoptionmenu"):
            self.attach._canvas.bind("<Button-1>", lambda e: self._iconify())
            self.attach._text_label.bind("<Button-1>", lambda e: self._iconify())
            if self.command is None:
                self.command = self.attach.set

        self.attach.bind("<Destroy>", lambda _: self._destroy(), add="+")

        self.update_idletasks()
        self.x = x
        self.y = y

        if self.autocomplete:
            self.bind_autocomplete()

        self.deiconify()
        self.withdraw()

        self.attributes("-alpha", self.alpha)

    def _destroy(self):
        self.after(500, self.destroy_popup)

    def _withdraw(self):
        if self.winfo_viewable() and self.hide:
            self.withdraw()

        self.event_generate("<<Closed>>")
        self.hide = True

    def _update(self, a, b, c):
        self.live_update(self.attach._entry.get())

    def bind_autocomplete(self, ):
        def appear(x):
            self.appear = True

        if self.attach.winfo_name().startswith("!ctkcombobox"):
            self.attach._entry.configure(textvariable=self.var_update)
            self.attach._entry.bind("<Key>", appear)
            self.attach.set(self.values[0])
            self.var_update.trace_add('write', self._update)

        if self.attach.winfo_name().startswith("!ctkentry"):
            self.attach.configure(textvariable=self.var_update)
            self.attach.bind("<Key>", appear)
            self.var_update.trace_add('write', self._update)

    def fade_out(self):
        for i in range(100, 0, -10):
            if not self.winfo_exists():
                break
            self.attributes("-alpha", i / 100)
            self.update()
            time.sleep(1 / 100)

    def fade_in(self):
        for i in range(0, 100, 10):
            if not self.winfo_exists():
                break
            self.attributes("-alpha", i / 100)
            self.update()
            time.sleep(1 / 100)

    def _init_buttons(self, **button_kwargs):
        self.i = 0
        self.widgets = {}
        for row in self.values:
            self.widgets[self.i] = ctk.CTkButton(self.frame,
                                                 text=row,
                                                 height=self.button_height,
                                                 fg_color=self.button_color,
                                                 text_color=self.text_color,
                                                 image=self.image_values[
                                                     self.i] if self.image_values is not None else None,
                                                 anchor=self.justify,
                                                 command=lambda k=row: self._attach_key_press(k),
                                                 **button_kwargs)
            self.widgets[self.i].pack(fill="x", pady=2, padx=(self.padding, 0))
            self.i += 1

        self.hide = False

    def destroy_popup(self):
        self.disable = True
        self.destroy()

    def place_dropdown(self):
        self.x_pos = self.attach.winfo_rootx() if self.x is None else self.x + self.attach.winfo_rootx()
        self.y_pos = self.attach.winfo_rooty() + self.attach.winfo_reqheight() + 5 if self.y is None else self.y + self.attach.winfo_rooty()
        self.width_new = self.attach.winfo_width() if self.width is None else self.width

        if self.resize:
            if self.button_num <= 5:
                self.height_new = self.button_height * self.button_num + 55
            else:
                self.height_new = self.button_height * self.button_num + 35
            if self.height_new > self.height:
                self.height_new = self.height

        self.geometry('{}x{}+{}+{}'.format(self.width_new, self.height_new,
                                           self.x_pos, self.y_pos))
        self.fade_in()
        self.attributes('-alpha', self.alpha)
        self.attach.focus()

    def _iconify(self):
        if self.disable: return
        if self.hide:
            self.event_generate("<<Opened>>")
            self._deiconify()
            self.focus()
            self.hide = False
            self.place_dropdown()
            if self.focus_something:
                self.dummy_entry.pack()
                self.dummy_entry.focus_set()
                self.after(100, self.dummy_entry.pack_forget)
        else:
            self.withdraw()
            self.hide = True

    def _attach_key_press(self, k):
        self.event_generate("<<Selected>>")
        self.fade = True
        if self.command:
            self.command(k)
        self.fade = False
        self.fade_out()
        self.withdraw()
        self.hide = True

    def live_update(self, string=None):
        if not self.appear: return
        if self.disable: return
        if self.fade: return
        if string:
            string = string.lower()
            self._deiconify()
            i = 1
            for key in self.widgets.keys():
                s = self.widgets[key].cget("text").lower()
                text_similarity = difflib.SequenceMatcher(None, s[0:len(string)], string).ratio()
                similar = s.startswith(string) or text_similarity > 0.75
                if not similar:
                    self.widgets[key].pack_forget()
                else:
                    self.widgets[key].pack(fill="x", pady=2, padx=(self.padding, 0))
                    i += 1

            if i == 1:
                self.no_match.pack(fill="x", pady=2, padx=(self.padding, 0))
            else:
                self.no_match.pack_forget()
            self.button_num = i
            self.place_dropdown()

        else:
            self.no_match.pack_forget()
            self.button_num = len(self.values)
            for key in self.widgets.keys():
                self.widgets[key].destroy()
            self._init_buttons()
            self.place_dropdown()

        self.frame._parent_canvas.yview_moveto(0.0)
        self.appear = False

    def insert(self, value, **kwargs):
        self.widgets[self.i] = ctk.CTkButton(self.frame,
                                             text=value,
                                             height=self.button_height,
                                             fg_color=self.button_color,
                                             text_color=self.text_color,
                                             anchor=self.justify,
                                             command=lambda k=value: self._attach_key_press(k), **kwargs)
        self.widgets[self.i].pack(fill="x", pady=2, padx=(self.padding, 0))
        self.i += 1
        self.values.append(value)

    def _deiconify(self):
        if len(self.values) > 0:
            self.deiconify()

    def popup(self, x=None, y=None):
        self.x = x
        self.y = y
        self.hide = True
        self._iconify()

    def configure(self, **kwargs):
        if "height" in kwargs:
            self.height = kwargs.pop("height")
            self.height_new = self.height

        if "alpha" in kwargs:
            self.alpha = kwargs.pop("alpha")

        if "width" in kwargs:
            self.width = kwargs.pop("width")

        if "fg_color" in kwargs:
            self.frame.configure(fg_color=kwargs.pop("fg_color"))

        if "values" in kwargs:
            self.values = kwargs.pop("values")
            self.image_values = None
            self.button_num = len(self.values)
            for key in self.widgets.keys():
                self.widgets[key].destroy()
            self._init_buttons()

        if "image_values" in kwargs:
            self.image_values = kwargs.pop("image_values")
            self.image_values = None if len(self.image_values) != len(self.values) else self.image_values
            if self.image_values is not None:
                i = 0
                for key in self.widgets.keys():
                    self.widgets[key].configure(image=self.image_values[i])
                    i += 1

        if "button_color" in kwargs:
            for key in self.widgets.keys():
                self.widgets[key].configure(fg_color=kwargs.pop("button_color"))

        for key in self.widgets.keys():
            self.widgets[key].configure(**kwargs)


class CTkMessagebox(customtkinter.CTkToplevel):
    ICONS = {
        "check": None,
        "cancel": None,
        "info": None,
        "question": None,
        "warning": None
    }
    ICON_BITMAP = {}

    def __init__(self,
                 master: any = None,
                 width: int = 400,
                 height: int = 200,
                 title: str = "CTkMessagebox",
                 message: str = "This is a CTkMessagebox!",
                 option_1: str = "OK",
                 option_2: str = None,
                 option_3: str = None,
                 options: list = [],
                 border_width: int = 1,
                 border_color: str = "default",
                 button_color: str = "default",
                 bg_color: str = "default",
                 fg_color: str = "default",
                 text_color: str = "default",
                 title_color: str = "default",
                 button_text_color: str = "default",
                 button_width: int = None,
                 button_height: int = None,
                 cancel_button_color: str = None,
                 cancel_button: str = None,  # types: circle, cross or none
                 button_hover_color: str = "default",
                 icon: str = "info",
                 icon_size: tuple = None,
                 corner_radius: int = 15,
                 justify: str = "right",
                 font: tuple = None,
                 header: bool = False,
                 topmost: bool = True,
                 fade_in_duration: int = 0,
                 sound: bool = False,
                 option_focus: Literal[1, 2, 3] = None):

        super().__init__()

        self.master_window = master

        self.width = 250 if width < 250 else width
        self.height = 150 if height < 150 else height

        if self.master_window is None:
            self.spawn_x = int((self.winfo_screenwidth() - self.width) / 2)
            self.spawn_y = int((self.winfo_screenheight() - self.height) / 2)
        else:
            self.spawn_x = int(
                self.master_window.winfo_width() * .5 + self.master_window.winfo_x() - .5 * self.width + 7)
            self.spawn_y = int(
                self.master_window.winfo_height() * .5 + self.master_window.winfo_y() - .5 * self.height + 20)

        self.after(10)
        self.geometry(f"{self.width}x{self.height}+{self.spawn_x}+{self.spawn_y}")
        self.title(title)
        self.resizable(width=False, height=False)
        self.fade = fade_in_duration

        if self.fade:
            self.fade = 20 if self.fade < 20 else self.fade
            self.attributes("-alpha", 0)

        if not header:
            self.overrideredirect(1)

        if topmost:
            self.attributes("-topmost", True)
        else:
            self.transient(self.master_window)

        if sys.platform.startswith("win"):
            self.transparent_color = self._apply_appearance_mode(self.cget("fg_color"))
            self.attributes("-transparentcolor", self.transparent_color)
            default_cancel_button = "cross"
        elif sys.platform.startswith("darwin"):
            self.transparent_color = 'systemTransparent'
            self.attributes("-transparent", True)
            default_cancel_button = "circle"
        else:
            self.transparent_color = '#000001'
            corner_radius = 0
            default_cancel_button = "cross"

        self.lift()

        self.config(background=self.transparent_color)
        self.protocol("WM_DELETE_WINDOW", self.button_event)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.x = self.winfo_x()
        self.y = self.winfo_y()
        self._title = title
        self.message = message
        self.font = font
        self.justify = justify
        self.sound = sound
        self.cancel_button = cancel_button if cancel_button else default_cancel_button
        self.round_corners = corner_radius if corner_radius <= 30 else 30
        self.button_width = button_width if button_width else self.width / 4
        self.button_height = button_height if button_height else 28

        if self.fade: self.attributes("-alpha", 0)

        if self.button_height > self.height / 4: self.button_height = self.height / 4 - 20
        self.dot_color = cancel_button_color
        self.border_width = border_width if border_width < 6 else 5

        if type(options) is list and len(options) > 0:
            try:
                option_1 = options[-1]
                option_2 = options[-2]
                option_3 = options[-3]
            except IndexError:
                None

        if bg_color == "default":
            self.bg_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"])
        else:
            self.bg_color = bg_color

        if fg_color == "default":
            self.fg_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkFrame"]["top_fg_color"])
        else:
            self.fg_color = fg_color

        default_button_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

        if sys.platform.startswith("win"):
            if self.bg_color == self.transparent_color or self.fg_color == self.transparent_color:
                self.configure(fg_color="#000001")
                self.transparent_color = "#000001"
                self.attributes("-transparentcolor", self.transparent_color)

        if button_color == "default":
            self.button_color = (default_button_color, default_button_color, default_button_color)
        else:
            if type(button_color) is tuple:
                if len(button_color) == 2:
                    self.button_color = (button_color[0], button_color[1], default_button_color)
                elif len(button_color) == 1:
                    self.button_color = (button_color[0], default_button_color, default_button_color)
                else:
                    self.button_color = button_color
            else:
                self.button_color = (button_color, button_color, button_color)

        if text_color == "default":
            self.text_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkLabel"]["text_color"])
        else:
            self.text_color = text_color

        if title_color == "default":
            self.title_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkLabel"]["text_color"])
        else:
            self.title_color = title_color

        if button_text_color == "default":
            self.bt_text_color = self._apply_appearance_mode(
                customtkinter.ThemeManager.theme["CTkButton"]["text_color"])
        else:
            self.bt_text_color = button_text_color

        if button_hover_color == "default":
            self.bt_hv_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkButton"]["hover_color"])
        else:
            self.bt_hv_color = button_hover_color

        if border_color == "default":
            self.border_color = self._apply_appearance_mode(
                customtkinter.ThemeManager.theme["CTkFrame"]["border_color"])
        else:
            self.border_color = border_color

        if icon_size:
            self.size_height = icon_size[1] if icon_size[1] <= self.height - 100 else self.height - 100
            self.size = (icon_size[0], self.size_height)
        else:
            self.size = (self.height / 4, self.height / 4)

        self.icon = self.load_icon(icon, icon_size) if icon else None

        self.frame_top = customtkinter.CTkFrame(self, corner_radius=self.round_corners, width=self.width,
                                                border_width=self.border_width,
                                                bg_color=self.transparent_color, fg_color=self.bg_color,
                                                border_color=self.border_color)
        self.frame_top.grid(sticky="nswe")

        if button_width:
            self.frame_top.grid_columnconfigure(0, weight=1)
        else:
            self.frame_top.grid_columnconfigure((1, 2, 3), weight=1)

        if button_height:
            self.frame_top.grid_rowconfigure((0, 1, 3), weight=1)
        else:
            self.frame_top.grid_rowconfigure((0, 1, 2), weight=1)

        self.frame_top.bind("<B1-Motion>", self.move_window)
        self.frame_top.bind("<ButtonPress-1>", self.oldxyset)

        if self.cancel_button == "cross":
            self.button_close = customtkinter.CTkButton(self.frame_top, corner_radius=10, width=0, height=0,
                                                        hover=False, border_width=0,
                                                        text_color=self.dot_color if self.dot_color else self.title_color,
                                                        text="✕", fg_color="transparent", command=self.button_event)
            self.button_close.grid(row=0, column=5, sticky="ne", padx=5 + self.border_width, pady=5 + self.border_width)
        elif self.cancel_button == "circle":
            self.button_close = customtkinter.CTkButton(self.frame_top, corner_radius=10, width=10, height=10,
                                                        hover=False, border_width=0,
                                                        text="",
                                                        fg_color=self.dot_color if self.dot_color else "#c42b1c",
                                                        command=self.button_event)
            self.button_close.grid(row=0, column=5, sticky="ne", padx=10, pady=10)

        self.title_label = customtkinter.CTkLabel(self.frame_top, width=1, text=self._title,
                                                  text_color=self.title_color, font=self.font)
        self.title_label.grid(row=0, column=0, columnspan=6, sticky="nw", padx=(15, 30), pady=5)
        self.title_label.bind("<B1-Motion>", self.move_window)
        self.title_label.bind("<ButtonPress-1>", self.oldxyset)

        self.info = customtkinter.CTkButton(self.frame_top, width=1, height=self.height / 2, corner_radius=0,
                                            text=self.message, font=self.font,
                                            fg_color=self.fg_color, hover=False, text_color=self.text_color,
                                            image=self.icon)
        self.info._text_label.configure(wraplength=self.width / 2, justify="left")
        self.info.grid(row=1, column=0, columnspan=6, sticky="nwes", padx=self.border_width)

        if self.info._text_label.winfo_reqheight() > self.height / 2:
            height_offset = int((self.info._text_label.winfo_reqheight()) - (self.height / 2) + self.height)
            self.geometry(f"{self.width}x{height_offset}")

        self.option_text_1 = option_1

        self.button_1 = customtkinter.CTkButton(self.frame_top, text=self.option_text_1, fg_color=self.button_color[0],
                                                width=self.button_width, font=self.font, text_color=self.bt_text_color,
                                                hover_color=self.bt_hv_color, height=self.button_height,
                                                command=lambda: self.button_event(self.option_text_1))

        self.option_text_2 = option_2
        if option_2:
            self.button_2 = customtkinter.CTkButton(self.frame_top, text=self.option_text_2,
                                                    fg_color=self.button_color[1],
                                                    width=self.button_width, font=self.font,
                                                    text_color=self.bt_text_color,
                                                    hover_color=self.bt_hv_color, height=self.button_height,
                                                    command=lambda: self.button_event(self.option_text_2))

        self.option_text_3 = option_3
        if option_3:
            self.button_3 = customtkinter.CTkButton(self.frame_top, text=self.option_text_3,
                                                    fg_color=self.button_color[2],
                                                    width=self.button_width, font=self.font,
                                                    text_color=self.bt_text_color,
                                                    hover_color=self.bt_hv_color, height=self.button_height,
                                                    command=lambda: self.button_event(self.option_text_3))

        if self.justify == "center":
            if button_width:
                columns = [4, 3, 2]
                span = 1
            else:
                columns = [4, 2, 0]
                span = 2
            if option_3:
                self.frame_top.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
                self.button_1.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(0, 10), pady=10)
                self.button_2.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=10, pady=10)
                self.button_3.grid(row=2, column=columns[2], columnspan=span, sticky="news", padx=(10, 0), pady=10)
            elif option_2:
                self.frame_top.columnconfigure((0, 5), weight=1)
                columns = [2, 3]
                self.button_1.grid(row=2, column=columns[0], sticky="news", padx=(0, 5), pady=10)
                self.button_2.grid(row=2, column=columns[1], sticky="news", padx=(5, 0), pady=10)
            else:
                if button_width:
                    self.frame_top.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
                else:
                    self.frame_top.columnconfigure((0, 2, 4), weight=2)
                self.button_1.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=(0, 10), pady=10)
        elif self.justify == "left":
            self.frame_top.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
            if button_width:
                columns = [0, 1, 2]
                span = 1
            else:
                columns = [0, 2, 4]
                span = 2
            if option_3:
                self.button_1.grid(row=2, column=columns[2], columnspan=span, sticky="news", padx=(0, 10), pady=10)
                self.button_2.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=10, pady=10)
                self.button_3.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(10, 0), pady=10)
            elif option_2:
                self.button_1.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=10, pady=10)
                self.button_2.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(10, 0), pady=10)
            else:
                self.button_1.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(10, 0), pady=10)
        else:
            self.frame_top.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
            if button_width:
                columns = [5, 4, 3]
                span = 1
            else:
                columns = [4, 2, 0]
                span = 2
            self.button_1.grid(row=2, column=columns[0], columnspan=span, sticky="news", padx=(0, 10), pady=10)
            if option_2:
                self.button_2.grid(row=2, column=columns[1], columnspan=span, sticky="news", padx=10, pady=10)
            if option_3:
                self.button_3.grid(row=2, column=columns[2], columnspan=span, sticky="news", padx=(10, 0), pady=10)

        if header:
            self.title_label.configure(text="")
            self.title_label.grid_configure(pady=0)
            self.button_close.configure(text_color=self.bg_color)
            self.frame_top.configure(corner_radius=0)

        if self.winfo_exists():
            self.grab_set()

        if self.sound:
            self.bell()

        if self.fade:
            self.fade_in()

        if option_focus:
            self.option_focus = option_focus
            self.focus_button(self.option_focus)
        else:
            if not self.option_text_2 and not self.option_text_3:
                self.button_1.focus()
                self.button_1.bind("<Return>", lambda event: self.button_event(self.option_text_1))

        self.bind("<Escape>", lambda e: self.button_event())

    def focus_button(self, option_focus):
        try:
            self.selected_button = getattr(self, "button_" + str(option_focus))
            self.selected_button.focus()
            self.selected_button.configure(border_color=self.bt_hv_color, border_width=3)
            self.selected_option = getattr(self, "option_text_" + str(option_focus))
            self.selected_button.bind("<Return>", lambda event: self.button_event(self.selected_option))
        except AttributeError:
            return

        self.bind("<Left>", lambda e: self.change_left())
        self.bind("<Right>", lambda e: self.change_right())

    def change_left(self):
        if self.option_focus == 3:
            return

        self.selected_button.unbind("<Return>")
        self.selected_button.configure(border_width=0)

        if self.option_focus == 1:
            if self.option_text_2:
                self.option_focus = 2

        elif self.option_focus == 2:
            if self.option_text_3:
                self.option_focus = 3

        self.focus_button(self.option_focus)

    def change_right(self):
        if self.option_focus == 1:
            return

        self.selected_button.unbind("<Return>")
        self.selected_button.configure(border_width=0)

        if self.option_focus == 2:
            self.option_focus = 1

        elif self.option_focus == 3:
            self.option_focus = 2

        self.focus_button(self.option_focus)

    def load_icon(self, icon, icon_size):
        if icon not in self.ICONS or self.ICONS[icon] is None:
            if icon in ["check", "cancel", "info", "question", "warning"]:
                image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icons', icon + '.png')
            else:
                image_path = icon
            if icon_size:
                size_height = icon_size[1] if icon_size[1] <= self.height - 100 else self.height - 100
                size = (icon_size[0], size_height)
            else:
                size = (self.height / 4, self.height / 4)
            self.ICONS[icon] = customtkinter.CTkImage(Image.open(image_path), size=size)
            self.ICON_BITMAP[icon] = ImageTk.PhotoImage(file=image_path)
        self.after(200, lambda: self.iconphoto(False, self.ICON_BITMAP[icon]))
        return self.ICONS[icon]

    def fade_in(self):
        for i in range(0, 110, 10):
            if not self.winfo_exists():
                break
            self.attributes("-alpha", i / 100)
            self.update()
            time.sleep(1 / self.fade)

    def fade_out(self):
        for i in range(100, 0, -10):
            if not self.winfo_exists():
                break
            self.attributes("-alpha", i / 100)
            self.update()
            time.sleep(1 / self.fade)

    def get(self):
        if self.winfo_exists():
            self.master.wait_window(self)
        return self.event

    def oldxyset(self, event):
        self.oldx = event.x
        self.oldy = event.y

    def move_window(self, event):
        self.y = event.y_root - self.oldy
        self.x = event.x_root - self.oldx
        self.geometry(f'+{self.x}+{self.y}')

    def button_event(self, event=None):
        try:
            self.button_1.configure(state="disabled")
            self.button_2.configure(state="disabled")
            self.button_3.configure(state="disabled")
        except AttributeError:
            pass

        if self.fade:
            self.fade_out()
        self.grab_release()
        self.destroy()
        self.event = event


class CTkLoader(ctk.CTkFrame):
    def __init__(self, master: any, opacity: float = 0.8, width: int = 40, height: int = 40):
        self.master = master
        self.opacity = opacity
        self.width = width
        self.height = height
        self.master.update()
        self.master_width = self.master.winfo_width()
        self.master_height = self.master.winfo_height()
        super().__init__(master, width=self.master_width, height=self.master_height, corner_radius=0)

        set_opacity(self.winfo_id(), value=self.opacity)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.loader = CTkGif(self, f"{CURRENT_PATH}\\icons\\loader.gif", width=self.width, height=self.height)
        self.loader.grid(row=0, column=0, sticky="nsew")
        self.loader.start()

        self.place(relwidth=1.0, relheight=1.0)

    def stop_loader(self):
        if self.loader:
            self.loader.stop()
        self.destroy()


class CTkGif(ctk.CTkLabel):

    def __init__(self, master: any, path, loop=True, acceleration=1, repeat=1, width=40, height=40, **kwargs):
        super().__init__(master, **kwargs)
        if acceleration <= 0:
            raise ValueError('Acceleration must be strictly positive')
        self.master = master
        self.repeat = repeat
        self.configure(text='')
        self.path = path
        self.count = 0
        self.loop = loop
        self.acceleration = acceleration
        self.index = 0
        self.is_playing = False
        self.gif = Image.open(path)
        self.n_frame = self.gif.n_frames
        self.frame_duration = self.gif.info['duration'] * 1 / self.acceleration
        self.force_stop = False

        self.width = width
        self.height = height

    def update(self):
        if self.index < self.n_frame:
            if not self.force_stop:
                self.gif.seek(self.index)
                self.configure(image=ctk.CTkImage(self.gif, size=(self.width, self.height)))
                self.index += 1
                self.after(int(self.frame_duration), self.update)
            else:
                self.force_stop = False
        else:
            self.index = 0
            self.count += 1
            if self.is_playing and (self.count < self.repeat or self.loop):
                self.after(int(self.frame_duration), self.update)
            else:
                self.is_playing = False

    def start(self):
        if not self.is_playing:
            self.count = 0
            self.is_playing = True
            self.after(int(self.frame_duration), self.update)

    def stop(self, forced=False):
        if self.is_playing:
            self.is_playing = False
            self.force_stop = forced

    def toggle(self, forced=False):
        if self.is_playing:
            self.stop(forced=forced)
        else:
            self.start()


class SettingsInterface(ctk.CTkFrame):
    def __init__(self, master: any, **kwargs):
        super().__init__(master, border_width=2, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.config_file = f"{CURRENT_PATH}\\config.json"
        self.config = load_config(self.config_file)

        label = ctk.CTkLabel(self, text="Settings", font=FONTS["title"])
        label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        theme_label = ctk.CTkLabel(self, text="Theme")
        theme_label.grid(row=1, column=0, padx=40, pady=(20, 5), sticky="w")

        values = ["System", "Dark", "Light"]
        self.theme_option = ctk.CTkOptionMenu(self, height=28, corner_radius=3)
        self.theme_option.grid(row=1, column=1, padx=40, pady=(20, 5), sticky="e")
        self.theme_dropdown = CTkScrollableDropdownFrame(self.theme_option, values=values,
                                                         **DROPDOWN, height=100, button_height=25,
                                                         command=self.theme_callback)
        self.theme_option.set(self.config["theme"])

        folder_label = ctk.CTkLabel(self, text="Download Folder")
        folder_label.grid(row=2, column=0, padx=40, pady=0, sticky="w")

        self.path_label = ctk.CTkLabel(self, text=self.config["download_path"], font=("", 11))
        self.path_label.grid(row=3, column=0, padx=40, pady=0, sticky="w")
        folder_btn = ctk.CTkButton(self, text="", image=ICONS["folder"], width=80, height=26,
                                   command=self.select_dir_callback)
        folder_btn.grid(row=3, column=1, padx=40, pady=0, sticky="w")

        close_btn = ctk.CTkButton(self, text="Close", command=lambda: self.destroy(), width=100)
        close_btn.grid(row=4, column=1, padx=20, pady=20, sticky="se")

    def select_dir_callback(self):
        new_dir = fd.askdirectory()
        if new_dir:
            save_config({"download_path": new_dir}, self.config_file)
            self.path_label.configure(text=new_dir)

    def theme_callback(self, theme) -> None:
        self.theme_option.set(theme)
        save_config({"theme": str(theme).lower()}, self.config_file)
        change_theme(theme)
