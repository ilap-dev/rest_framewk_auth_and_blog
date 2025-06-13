import bleach
import re

def sanitize_string(string):
    if string is None:
        return ""
    #Sanitizar usando bleach para remover cualqueir tag que no deseamos
    cleaned_string = bleach.clean(string, tags=[], strip=True)

    #Permitir letras, numeros, espacios, apostrofes, comillas, camas y puntos
    pattern = re.compile(r"[^a-zA-Z0-9\s',:.?-ÁÉÍÓÚáéíóúÑñÜü]")
    #Remover caracteres indeseados
    sanitized_string = pattern.sub("", cleaned_string)

    return sanitized_string

