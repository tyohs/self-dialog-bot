import openai

client = openai.OpenAI(
    api_key="4_sxMJ6ob3J4lhehdWvmS88Kz2dRUW7gJIw3Li2kAZ-6AfJamyGeyoE9nvejt0fbcPzrQQut9RrLSYIPOqQWmLg",
    base_url="https://api.openai.iniad.org/api/v1",
)

question = input('Question: ')

response = client.chat.completions.create(
    model='gpt-o4-mini',
    messages=[
        {'role': 'user', 'content': question},
    ]
)

print(response.choices[0].message.content)
