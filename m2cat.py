import os
import pycantonese
import regex
import sys
from azure.ai.translation.text.models import (
  InputTextItem
)

from azure.ai.translation.text import (
  TextTranslationClient,
  TranslatorCredential
)

from azure.core.exceptions import (
  HttpResponseError
)

def main():
  translator_credential = TranslatorCredential(
    os.getenv("AZURE_TRANSLATOR_KEY_1"),
    os.getenv("AZURE_TRANSLATOR_REGION")
  )

  text_translator = TextTranslationClient(
    credential=translator_credential,
    endpoint=os.getenv("AZURE_TRANSLATOR_TEXT_URL")
  )

  #get_supported_languages(text_translator)

  if len(sys.argv) != 2 and len(sys.argv) != 3:
    print("Must specify input file!\n")
    sys.exit(1)

  input_file_name = sys.argv[1]

  if len(sys.argv) == 3:
    output_file_name = sys.argv[2]
  else:
    output_file_name = input_file_name.replace('.txt', '_canto.txt')

  print("Converting to Cantonesish...\n")

  with open(input_file_name, 'r', encoding='utf-8') as input_file:
    with open(output_file_name, 'w', encoding='utf-8') as output_file:
      for line in input_file:
        # If contains chinese characters
        if regex.match(r"\p{Han}+", line):
          # Print the Mandarin "as is"
          output_file.write(f"M: {line}")

          # Print the converted Cantonese
          print("translating:", line)
          #line = translator.translate('zh', 'yue', line) 
          #print(Translator('yue').translator(line))
          output_file.write(translate(text_translator, line))

          # Annotate Jyutping
          output_file.write(get_jyutping_line(line))
          output_file.write("\n")
        else:
          output_file.write(line)

def translate(text_translator: TextTranslationClient, line: str) -> str:
  try:
    source_language = "zh-Hant"
    target_languages = ["yue"]
    input_text_elements = [ InputTextItem(text = line) ]
    response = text_translator.translate(content = input_text_elements, to = target_languages, from_parameter = source_language)
    translation = response[0] if response else None

    if translation:
      for translated_text in translation.translations:
        print(f"Text was translated to: '{translated_text.to}' and the result is: '{translated_text}'.")
        return translated_text.text

  except HttpResponseError as exception:
    if exception.error is not None:
      print(f"Error Code: {exception.error.code}")
      print(f"Message: {exception.error.message}")
    raise

def get_supported_languages(text_translator):
  try:
    response = text_translator.get_languages()

    print(
      f"Number of supported languages for translate operation: {len(response.translation) if response.translation is not None else 0}"
    )
    print(
      f"Number of supported languages for transliterate operation: {len(response.transliteration) if response.transliteration is not None else 0}"
    )
    print(
      f"Number of supported languages for dictionary operations: {len(response.dictionary) if response.dictionary is not None else 0}"
    )

    if response.translation is not None:
      print("Translation Languages:")
      for key, value in response.translation.items():
        print(f"{key} -- name: {value.name} ({value.native_name})")

    if response.transliteration is not None:
      print("Transliteration Languages:")
      for key, value in response.transliteration.items():
        print(f"{key} -- name: {value.name}, supported script count: {len(value.scripts)}")

    if response.dictionary is not None:
      print("Dictionary Languages:")
      for key, value in response.dictionary.items():
        print(f"{key} -- name: {value.name}, supported target languages count: {len(value.translations)}")

  except HttpResponseError as exception:
    if exception.error is not None:
      print(f"Error Code: {exception.error.code}")
      print(f"Message: {exception.error.message}")
    raise

def get_jyutping_line(line: str) -> str:
  return ' '.join(list(map(get_jyutping_word, pycantonese.characters_to_jyutping(line))))

def get_jyutping_word(tuple: tuple) -> str:
  if tuple[1] is not None:
    # put a dash between syllables
    return regex.sub(r'([1-6])([a-z])', r'\1-\2', tuple[1])
  else:
    return tuple[0]

if __name__ == "__main__":
  main()
