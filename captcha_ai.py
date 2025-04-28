from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# File path of the text file you want to process
file_path = "captcha_debug.png"  # Replace with the path to your file

# Read file content
file_content = read_file(file_path)

completion = client.chat.completions.create(
  extra_body={},
  model="openai/gpt-4o-search-preview",
  messages=[
    {
      "role": "user",
      "content":
    }
  ]
)
print(completion.choices[0].message.content)