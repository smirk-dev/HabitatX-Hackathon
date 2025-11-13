import re

file_path = r'templates\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all old blue shades with light blue
replacements = [
    ('#3b82f6', '#87CEEB'),
    ('#60a5fa', '#87CEEB'),
    ('#93c5fd', '#87CEEB'),
    ('#e0e7ff', '#cbd5e1'),
    ('#1e3a8a', '#000000'),
    ('#1e40af', '#1a1a1a'),
    ('rgba(30, 58, 138', 'rgba(0, 0, 0'),
    ('rgba(30, 64, 175', 'rgba(26, 26, 26'),
    ('rgba(59, 130, 246', 'rgba(135, 206, 250'),
    ('rgba(96, 165, 250', 'rgba(135, 206, 250'),
    ('rgba(147, 197, 253', 'rgba(135, 206, 250'),
    # Reduce font weights (less bold)
    ('font-weight: 700', 'font-weight: 600'),
    ('font-weight: 600', 'font-weight: 500'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ UI updated with black and light blue (#87CEEB) theme!")
print("✅ Font weights reduced for less highlighting")
print("✅ Refresh your browser to see changes!")
