# m2cat.py (Mandarin to CAntonese Translator)

Given a file with Mandarin text, this script adds in a cantonese translation and jyutping for each paragraph.
Any non-Chinese text is also preserved.

## Installation
pip install regex
pip install azure-ai-translation-text

Setup the following environment variables after registering for an Azure Translator Key (https://learn.microsoft.com/en-us/azure/ai-services/translator/create-translator-resource):

* AZURE_TRANSLATOR_KEY_1
* AZURE_TRANSLATOR_REGION
* AZURE_TRANSLATOR_TEXT_URL

## Usage

python m2cat.py INPUT_FILE
