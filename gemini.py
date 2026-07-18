from google import genai

client = genai.Client()

interaction = client.interactions.create(
    model="gemini-3.5-flash",
    input="Explain why a deployment was blocked because it touched auth files after business hours."
)

print(interaction.output_text)