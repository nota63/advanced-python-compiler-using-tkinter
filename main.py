import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
import subprocess
import sys
import io
import os
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.styles import get_style_by_name
import time
import jedi


class PythonCompilerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Python Compiler App")
        self.root.geometry("1000x700")

        # Setting up the color scheme
        self.colors = {
            'background': '#2c3e50',
            'text_bg': '#1e272e',
            'text_fg': '#ffffff',
            'output_bg': '#2d3436',
            'output_fg': '#dfe6e9',
            'button_bg': '#0984e3',
            'button_fg': '#ffffff',
            'error_fg': '#d63031',
            'highlight': '#74b9ff'
        }

        self.root.configure(bg=self.colors['background'])

        # Create a menu bar
        self.menu_bar = tk.Menu(root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label="Change Theme", command=self.change_theme)
        self.settings_menu.add_command(label="Change Font Size", command=self.change_font_size)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)

        root.config(menu=self.menu_bar)

        # Create a PanedWindow
        self.paned_window = tk.PanedWindow(root, orient=tk.VERTICAL, bg=self.colors['background'])
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # Frame for Code Editor with line numbers
        self.editor_frame = tk.Frame(self.paned_window, bg=self.colors['background'])
        self.code_input = ScrolledText(self.editor_frame, width=80, height=15, bg=self.colors['text_bg'],
                                       fg=self.colors['text_fg'], insertbackground=self.colors['text_fg'], undo=True)
        self.code_input.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)
        self.code_input.bind("<KeyRelease>", self.syntax_highlight)
        self.code_input.bind("<KeyRelease>", self.update_line_numbers)
        self.code_input.bind("<KeyRelease>", self.show_autocomplete)
        self.line_numbers = tk.Text(self.editor_frame, width=4, bg=self.colors['background'], fg=self.colors['text_fg'],
                                    state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.paned_window.add(self.editor_frame)

        # Frame for Output
        self.output_frame = tk.Frame(self.paned_window, bg=self.colors['background'])
        self.output_display = ScrolledText(self.output_frame, width=80, height=10, bg=self.colors['output_bg'],
                                           fg=self.colors['output_fg'], insertbackground=self.colors['output_fg'])
        self.output_display.pack(fill=tk.BOTH, expand=1)
        self.paned_window.add(self.output_frame)

        # Button to run code
        self.run_button = tk.Button(root, text="Run Code", command=self.animate_button, bg=self.colors['button_bg'],
                                    fg=self.colors['button_fg'])
        self.run_button.pack(pady=5)

        self.update_line_numbers()

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'r') as file:
                self.code_input.delete("1.0", tk.END)
                self.code_input.insert(tk.END, file.read())
                self.syntax_highlight()

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".py",
                                                 filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.code_input.get("1.0", tk.END))

    def animate_button(self):
        original_color = self.run_button.cget("bg")
        self.run_button.config(bg=self.colors['highlight'])
        self.root.update_idletasks()
        time.sleep(0.1)
        self.run_button.config(bg=original_color)
        self.root.after(100, self.run_code)

    def run_code(self):
        code = self.code_input.get("1.0", tk.END)
        output = self.execute_code(code)
        self.animate_output(output)

    def execute_code(self, code):
        # Redirect stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        try:
            # Execute the code
            exec(code)
            output = sys.stdout.getvalue()
            error = sys.stderr.getvalue()
        except Exception as e:
            output = ""
            error = str(e)
        finally:
            # Reset stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        if error:
            return f"Error:\n{error}"
        return output

    def animate_output(self, output):
        self.output_display.delete("1.0", tk.END)
        self.output_display.insert(tk.END, output)
        self.output_display.tag_configure("error", foreground=self.colors['error_fg'])

        if "Error:" in output:
            self.output_display.tag_add("error", "1.0", "end")
            for i in range(5):
                self.output_display.config(bg=self.colors['error_fg'])
                self.root.update_idletasks()
                time.sleep(0.1)
                self.output_display.config(bg=self.colors['output_bg'])
                self.root.update_idletasks()
                time.sleep(0.1)

    def syntax_highlight(self, event=None):
        code = self.code_input.get("1.0", tk.END)
        self.code_input.mark_set("range_start", "1.0")
        for token, content in lex(code, PythonLexer()):
            self.code_input.mark_set("range_end", f"range_start + {len(content)}c")
            self.code_input.tag_add(str(token), "range_start", "range_end")
            self.code_input.mark_set("range_start", "range_end")
        # Define styles
        style = get_style_by_name('default')
        for token, style_def in style:
            if style_def['color']:
                self.code_input.tag_configure(str(token), foreground=f"#{style_def['color']}")

    def update_line_numbers(self, event=None):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        line_count = int(self.code_input.index('end-1c').split('.')[0])
        line_numbers_string = "\n".join(map(str, range(1, line_count)))
        self.line_numbers.insert('1.0', line_numbers_string)
        self.line_numbers.config(state='disabled')

    def change_theme(self):
        theme = simpledialog.askstring("Input", "Enter theme (light or dark):")
        if theme == "light":
            self.colors['background'] = '#ffffff'
            self.colors['text_bg'] = '#f5f5f5'
            self.colors['text_fg'] = '#000000'
            self.colors['output_bg'] = '#e0e0e0'
            self.colors['output_fg'] = '#000000'
            self.colors['button_bg'] = '#3498db'
            self.colors['button_fg'] = '#ffffff'
            self.colors['highlight'] = '#2980b9'
            self.colors['error_fg'] = '#e74c3c'
        elif theme == "dark":
            self.colors['background'] = '#2c3e50'
            self.colors['text_bg'] = '#1e272e'
            self.colors['text_fg'] = '#ffffff'
            self.colors['output_bg'] = '#2d3436'
            self.colors['output_fg'] = '#dfe6e9'
            self.colors['button_bg'] = '#0984e3'
            self.colors['button_fg'] = '#ffffff'
            self.colors['highlight'] = '#74b9ff'
            self.colors['error_fg'] = '#d63031'
        self.update_colors()

    def change_font_size(self):
        font_size = simpledialog.askinteger("Input", "Enter font size:", minvalue=8, maxvalue=32)
        if font_size:
            self.code_input.config(font=("Courier", font_size))
            self.output_display.config(font=("Courier", font_size))
            self.line_numbers.config(font=("Courier", font_size))

    def update_colors(self):
        self.root.configure(bg=self.colors['background'])
        self.code_input.config(bg=self.colors['text_bg'], fg=self.colors['text_fg'],
                               insertbackground=self.colors['text_fg'])
        self.output_display.config(bg=self.colors['output_bg'], fg=self.colors['output_fg'],
                                   insertbackground=self.colors['output_fg'])
        self.run_button.config(bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        self.line_numbers.config(bg=self.colors['background'], fg=self.colors['text_fg'])

    def show_autocomplete(self, event=None):
        # Use Jedi for auto-completion
        code = self.code_input.get("1.0", tk.END)
        script = jedi.Script(code, len(code.splitlines()), len(code.splitlines()[-1]), '')
        completions = script.complete()
        if completions:
            # Show completions in a dropdown menu
            popup = tk.Menu(self.code_input, tearoff=0)
            for completion in completions:
                popup.add_command(label=completion.name, command=lambda comp=completion: self.insert_completion(comp))
            popup.tk_popup(self.code_input.winfo_rootx() + event.x, self.code_input.winfo_rooty() + event.y)

    def insert_completion(self, completion):
        self.code_input.insert(tk.INSERT, completion.name[len(completion.complete):])


if __name__ == "__main__":
    root = tk.Tk()
    app = PythonCompilerApp(root)
    root.mainloop()


