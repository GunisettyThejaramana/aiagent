from docx import Document


def load_word(file_path):

    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:

        text += paragraph.text + "\n"

    return text