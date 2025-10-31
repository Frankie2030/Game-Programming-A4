extends Control

@onready var message_label = $MessageLabel
@onready var chat_container = $ChatContainer
@onready var chat_input = $ChatInput

func show_message(text: String):
    message_label.text = text
    message_label.show()
    await get_tree().create_timer(3.0).timeout
    message_label.hide()

func add_chat_message(player_id: String, message: String):
    var message_node = Label.new()
    message_node.text = player_id + ": " + message
    chat_container.add_child(message_node)
    
    # Keep only last 10 messages
    if chat_container.get_child_count() > 10:
        chat_container.get_child(0).queue_free()

func _on_chat_input_text_submitted(new_text: String):
    if new_text.strip_edges() != "":
        get_parent().send_chat(new_text)
        chat_input.text = ""
