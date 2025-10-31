extends Control

# Scene references
@onready var main_menu = get_node_or_null("MainMenu")
@onready var game_menu = get_node_or_null("GameMenu")
@onready var settings_menu = get_node_or_null("SettingsMenu")
@onready var multiplayer_menu = get_node_or_null("MultiplayerMenu")
@onready var ai_menu = get_node_or_null("AIMenu")

# Current game state
var current_menu: Control
var game_settings = {
	"ai_difficulty": "medium",
	"board_size": 15,
	"game_mode": "single_player"
}

func _ready():
	# Initialize menus by hiding all except main menu
	if game_menu:
		game_menu.hide()
	if settings_menu:
		settings_menu.hide()
	if multiplayer_menu:
		multiplayer_menu.hide()
	if ai_menu:
		ai_menu.hide()
	
	if main_menu:
		main_menu.show()
		current_menu = main_menu
	
	# Connect main menu buttons
	connect_button("MainMenu/SinglePlayerBtn", _on_single_player_pressed)
	connect_button("MainMenu/MultiplayerBtn", _on_multiplayer_pressed)
	connect_button("MainMenu/SettingsBtn", _on_settings_pressed)
	connect_button("MainMenu/QuitBtn", _on_quit_pressed)
	
	# Connect multiplayer menu buttons
	connect_button("MultiplayerMenu/HostBtn", _on_host_pressed)
	connect_button("MultiplayerMenu/JoinBtn", _on_join_pressed)
	connect_button("MultiplayerMenu/BackBtn", show_main_menu)
	
	# Connect AI menu buttons
	connect_button("AIMenu/EasyBtn", func(): _start_ai_game("easy"))
	connect_button("AIMenu/MediumBtn", func(): _start_ai_game("medium"))
	connect_button("AIMenu/HardBtn", func(): _start_ai_game("hard"))
	connect_button("AIMenu/BackBtn", show_main_menu)
	
	# Connect settings menu buttons
	connect_button("SettingsMenu/BackBtn", show_main_menu)
	
	# Print debug information
	print_debug("Menu System Initialization:")
	print_debug("Main Menu: ", main_menu != null)
	print_debug("Game Menu: ", game_menu != null)
	print_debug("Settings Menu: ", settings_menu != null)
	print_debug("Multiplayer Menu: ", multiplayer_menu != null)
	print_debug("AI Menu: ", ai_menu != null)
	
	# Print debug information
	print_debug("Menu System Initialization:")
	print_debug("Main Menu: ", main_menu != null)
	print_debug("Game Menu: ", game_menu != null)
	print_debug("Settings Menu: ", settings_menu != null)
	print_debug("Multiplayer Menu: ", multiplayer_menu != null)
	print_debug("AI Menu: ", ai_menu != null)

# Helper function to safely connect button signals
func connect_button(path: String, callback: Callable) -> void:
	var button = get_node_or_null(path)
	if button:
		if !button.is_connected("pressed", callback):
			button.connect("pressed", callback)
	else:
		print_debug("Warning: Button not found: ", path)

func show_menu(menu: Control) -> void:
	if menu == null:
		print_debug("Warning: Attempted to show null menu")
		return
		
	print_debug("Switching to menu: ", menu.name)
	
	if current_menu:
		print_debug("Hiding current menu: ", current_menu.name)
		current_menu.hide()
	current_menu = menu
	current_menu.show()
	print_debug("Menu switch complete. Current menu: ", current_menu.name)

func show_main_menu() -> void:
	if main_menu:
		show_menu(main_menu)
	else:
		print_debug("Error: Main menu not found")

func _on_single_player_pressed() -> void:
	if ai_menu:
		show_menu(ai_menu)
	else:
		print_debug("Error: AI menu not found")

func _on_multiplayer_pressed():
	show_menu(multiplayer_menu)

func _on_settings_pressed():
	show_menu(settings_menu)

func _on_quit_pressed():
	get_tree().quit()

func _on_host_pressed():
	game_settings["game_mode"] = "host"
	get_parent().start_multiplayer_game(game_settings)

func _on_join_pressed():
	game_settings["game_mode"] = "join"
	var game_code = $MultiplayerMenu/GameCodeInput.text
	if game_code.strip_edges() != "":
		get_parent().join_multiplayer_game(game_code)

func _start_ai_game(difficulty: String):
	game_settings["game_mode"] = "single_player"
	game_settings["ai_difficulty"] = difficulty
	get_parent().start_single_player_game(game_settings)

# Called from parent when game starts
func hide_menus():
	if current_menu:
		current_menu.hide()
		current_menu = null
