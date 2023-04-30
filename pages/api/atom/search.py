import os
import openai
import requests
import json
import config as config

# Replace with your Google API key and Google CSE ID
GOOGLE_API_KEY = config.GOOGLE_API_KEY
GOOGLE_CSE_ID = config.GOOGLE_CSE_ID
# Replace with your OpenAI API key
OPENAI_API_KEY = config.OPENAI_API_KEY

def search_google(query):
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={query}"
    response = requests.get(url)
    results = response.json()
    print("Search results JSON:", results)  # Add this line
    return results

def gpt3_query(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0.5,
        max_tokens=150,
        top_p=1.0,
        frequency_penalty=0,
        presence_penalty=0,
    )
    return response.choices[0].text.strip()

def main():
    query = input("Ask a question: ")
    search_results = search_google(query)

    gpt_prompt = f"Please provide a brief summary of the top search results for '{query}':\n\n"
    for i, result in enumerate(search_results["items"][:3]):
        title = result["title"]
        snippet = result["snippet"]
        link = result["link"]
        gpt_prompt += f"{i + 1}. {title}\n{snippet}\n{link}\n\n"

    summary = gpt3_query(gpt_prompt)
    print("\nGPT-3 Summary:\n", summary)

if __name__ == "__main__":
    main()
