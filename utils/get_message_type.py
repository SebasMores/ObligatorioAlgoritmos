def get_message_type(message):
    content = ""
    message_type = message["type"]

    if message_type == "text":
        # Extrae el texto para un mensaje de texto simple
        content = message["text"]["body"]
    
    elif message_type == "interactive":
        # Procesa mensajes interactivos (botones o listas)
        interactive_object = message["interactive"]
        interactive_type = interactive_object["type"]

        if interactive_type == "button_reply":
            # Extrae el título del botón que el usuario presionó
            content = interactive_object["button_reply"]["id"]
        elif interactive_type == "list_reply":
            # Extrae el título del elemento de la lista que el usuario seleccionó
            content = interactive_object["list_reply"]["id"]
        else:
            print("sin mensaje")
    
    else:
        # Maneja otros tipos de mensajes que no son texto ni interactivos
        print("sin mensaje")

    return message_type, content