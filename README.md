# -----------------------------
# Input Map (Project → Project Settings → Input Map)
#   ui_up, ui_down, ui_left, ui_right, ui_accept (Enter/Space)
#   ui_page_up, ui_page_down (bind to Q / E or PageUp / PageDown)

# -----------------------------
# Quick Start
# 1) Create a new Godot 4 project and add the files.
# 2) Open Main.tscn and run it (local hotseat by default). Use arrow keys to move, Q/E (or PageUp/Down) to change layer, Space/Enter to place.
# 3) Single-player vs AI: from the console or an in‑game toggle you add later, call:
#      get_tree().current_scene.set_mode_single_ai()
# 4) Server: run scenes/ServerLauncher.tscn headless:
#      godot4 --headless --path . --scene res://scenes/ServerLauncher.tscn
# 5) Client: run Main.tscn, then connect:
#      get_tree().current_scene.set_mode_client("<server_ip>", 7777)
#    Your local scene becomes a network client; the server is authoritative.
#
# Notes
# - The server holds the true grid and validates moves, broadcasting updates.
# - The client only sends intents (x,y,z). The server assigns colors on join.
# - The AI is simple but fast; raise max_depth/beam_width for stronger play.
# - Board rendering uses simple grid lines + spheres via MultiMesh for speed.
