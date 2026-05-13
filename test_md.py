import tkinter as tk
from tkinter import scrolledtext
import re

content = """## <span style="color:#0078D7">🪟 1. Building for Windows (.exe)</span>
Some text here
"""

root = tk.Tk()
st = scrolledtext.ScrolledText(root)
st.pack()

def insert_inline_md(text_str, tags=()):
    text_str = re.sub(r'<[^>]+>', '', text_str)
    pattern = re.compile(r'(\*\*.*?\*\*|\*.*?\*|`.*?`|\[.*?\]\(.*?\))')
    parts = pattern.split(text_str)
    for p in parts:
        current_tags = list(tags)
        if p.startswith('**') and p.endswith('**'):
            current_tags.append("bold")
            st.insert(tk.END, p[2:-2], tuple(current_tags))
        elif p.startswith('*') and p.endswith('*') and len(p) > 2:
            current_tags.append("italic")
            st.insert(tk.END, p[1:-1], tuple(current_tags))
        elif p.startswith('`') and p.endswith('`'):
            current_tags.append("code")
            st.insert(tk.END, p[1:-1], tuple(current_tags))
        elif p.startswith('[') and '](' in p and p.endswith(')'):
            title = p[1:p.find('](')]
            current_tags.append("link")
            st.insert(tk.END, title, tuple(current_tags))
        else:
            st.insert(tk.END, p, tuple(current_tags))

in_code_block = False
for line in content.split('\n'):
    if line.startswith("```"):
        in_code_block = not in_code_block
        st.insert(tk.END, "\n")
        continue
    if in_code_block:
        st.insert(tk.END, line + "\n", "codeblock")
        continue
    if line.startswith("## "):
        insert_inline_md(line.lstrip("# \t"), ("h2",))
        st.insert(tk.END, "\n", "h2")
    else:
        insert_inline_md(line)
        st.insert(tk.END, "\n")

print("Result:")
print(repr(st.get(1.0, tk.END)))
