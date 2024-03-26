import argparse
import os
import pycantonese
import regex
from argparse import (
  ArgumentParser
)

# pip install azure-ai-translation-text
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
  parser = setup_parser()
  args = parser.parse_args()

  translator_credential = TranslatorCredential(
    os.getenv("AZURE_TRANSLATOR_KEY_1"),
    os.getenv("AZURE_TRANSLATOR_REGION")
  )

  text_translator = TextTranslationClient(
    credential=translator_credential,
    endpoint=os.getenv("AZURE_TRANSLATOR_TEXT_URL")
  )

  #get_supported_languages(text_translator)

  input_file_name = args.files[0]

  if len(args.files) == 2:
    output_file_name = args.files[1]
  else:
    output_file_name = input_file_name.replace('.txt', '_canto.txt')

  print("Converting to Cantonesish...\n")

  with open(input_file_name, 'r', encoding='utf-8') as input_file:
    with open(output_file_name, 'w', encoding='utf-8') as output_file:
      chinese_lines = []
      cantonese_lines = []
      jyutping_lines = []
      n_jyutping_lines = 0

      lines = input_file.readlines()
      last_line_index = len(lines) - 1
      for i, line in enumerate(lines):
        processed_line = False
        is_last_line = (i == last_line_index)

        if(args.regenerate_jyutping):
          # Line is not jyutping and we have found one or more lines of jyutping already
          if not regex.match(r".*[a-z][1-6].*", line) and n_jyutping_lines > 0:
            # If there are X lines of jyutping, then redo it based on the last X lines of chinese.
            # This assumes that there is either only Cantonese before, or alternatively, first Mandarin, then Cantonese
            for n in range(-1*n_jyutping_lines, 0):
              if n < -1:
                print(f"jyutpinging {chinese_lines[n]}")
              output_file.write(get_jyutping_line(chinese_lines[n]))
            output_file.write("\n")
            chinese_lines.clear()
            n_jyutping_lines = 0
          # It's chinese, store it in the chinese 
          if regex.match(r".*\p{Han}+.*", line):
            chinese_lines.append(line)
          # It's jyutping, track how many jyutping linese there are
          if regex.match(r".*[a-z][1-6].*", line):
            if n_jyutping_lines > 1:
              print("Found jyutping!")
            n_jyutping_lines += 1
            processed_line = True
        else:
          # Contains chinese characters
          if regex.match(r".*\p{Han}+.*", line):
            # Print the Mandarin "as is"
            output_file.write(line)
            # Store the translated Cantonese
            cantonese_line = translate(text_translator, line)
            cantonese_lines.append(cantonese_line)
            # Store the Annotated Jyutping
            jyutping_lines.append(get_jyutping_line(cantonese_line))
            processed_line = True

          # Reached a blank line or end of file
          if regex.match(r"^\s*$", line) or is_last_line is True:
            for cantonese_line in cantonese_lines:
              output_file.write(cantonese_line)
            for jyutping_line in jyutping_lines:
              output_file.write(jyutping_line)
              output_file.write("\n")
            cantonese_lines = []
            jyutping_lines = [] 
            output_file.write("\n")
            processed_line = True

        if processed_line is not True:
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

def setup_parser() -> ArgumentParser:
  parser = argparse.ArgumentParser(description='Translate existing to mandarin to cantonese and add jyutping')
  parser.add_argument("files", nargs="+")
  parser.add_argument('--regenerate_jyutping', action='store_true', help='Regenerate Jyutping')
  return parser

if __name__ == "__main__":
  main()
