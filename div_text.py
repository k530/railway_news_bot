def div_text_by_utf8_len(text, max_length):
    sentences = []
    current_utf8_len = 0
    current_start = 0
    current_pos = 0
    while current_pos < len(text):
        if len(text[current_pos].encode('utf-8')) + current_utf8_len > max_length:
            sentences.append(text[current_start: current_pos].encode('utf-8'))
            current_start = current_pos
            current_utf8_len = 0
        current_utf8_len += len(text[current_pos].encode('utf-8'))
        current_pos += 1
    if text[current_start:] != '':
        sentences.append(text[current_start: ].encode('utf-8'))
    return sentences


def div_text_by_marks(text, max_length, marks):
    sentences = []
    current_pos = 0
    current_string_start = 0
    while current_pos < len(text):
        if text[current_pos] in marks:
            current_utf8_string = text[current_string_start:current_pos + 1].encode('utf-8')
            if len(current_utf8_string) <= max_length:
                sentences.append(current_utf8_string)
            else:
                sentences += div_text_by_utf8_len(text[current_string_start:current_pos + 1], max_length)
            current_string_start = current_pos + 1
        current_pos += 1
    if current_string_start != len(text):
        sentences.append(text[current_string_start:].encode('utf-8'))
    text_list = []
    current_pos = 0
    current_string = ''.encode('utf-8')
    while current_pos < len(sentences):
        if len(current_string) + len(sentences[current_pos]) <= max_length:
            current_string += sentences[current_pos]
        else:
            text_list.append(current_string.decode('utf-8'))
            current_string = sentences[current_pos]
        current_pos += 1
    if len(current_string) > 0:
        text_list.append(current_string.decode('utf-8'))
    return text_list
