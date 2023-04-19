import asyncio
import re
from EdgeGPT import Chatbot, ConversationStyle

async def main():
    while True:
        bot = Chatbot(cookiePath='pages/api/cookies.json')
        response = await bot.ask(prompt=input("Ask Bing AI a Question..."), conversation_style=ConversationStyle.creative)
        # Extract URL references from the response and print them along with the bot response
        for message in response["item"]["messages"]:
            if message["author"] == "bot":
                bot_response = message["text"]
                url_references = re.findall(r'\[(\d+)\]', bot_response)
                if url_references:
                    for ref in url_references:
                        url = f"URL {ref}: https://{ref}"
                        bot_response = bot_response.replace(f'[{ref}]', url)
                print("Bot's response:", bot_response)
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())





# import asyncio
# import re
# from EdgeGPT import Chatbot, ConversationStyle

# async def main():
#     while True:
#         bot = Chatbot(cookiePath='pages/api/cookies.json')
#         response = await bot.ask(prompt=input ("Ask Bing AI a Question..."), conversation_style=ConversationStyle.creative)
#           # Select only the bot response from the response dictionary
#         for message in response["item"]["messages"]:
#             if message["author"] == "bot":
#                 bot_response = message ["text"]
#         # Remove [^#^] citations in response
#         bot_response = re.sub('\[\^\d+\^\]', '', bot_response)
#         print ("Bot's response:", bot_response)
#         await bot.close()

# if __name__ == "__main__":
#     asyncio.run(main())

