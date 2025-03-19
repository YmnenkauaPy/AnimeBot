import asyncio, re
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from typing import Final
from aiogram.fsm.storage.memory import MemoryStorage
import requests
from bs4 import BeautifulSoup as bs
from thefuzz import fuzz
from thefuzz import process

import commands

TOKEN : Final = '7827932477:AAEJhhSuRLk11lors5UyGgUYk6ilNMkXxWI'
bot = Bot(token = TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_router(commands.router)

headers = {"User-Agent": "Mozilla/5.0"}

async def search_anime(query):
    search_url = f"https://myanimelist.net/search/all?q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    soup = bs(response.text, "html.parser")

    anime_card = soup.find("a", class_="hoverinfo_trigger")
    if not anime_card:
        return "Anime haven't been found"

    link = anime_card["href"]
    soup = bs((requests.get(link, headers=headers)).text, 'html.parser')
    title = soup.find("h1", class_="title-name h1_bold_none").text
    description = soup.find("p", itemprop="description").text
    clean_text = re.sub(r"\[.*?\]", "", description).strip()
    studio = soup.find("span", class_ = "information studio author").text
    episodes_tag = soup.find("span", class_="dark_text", string="Episodes:")
    episodes = episodes_tag.parent.text.replace("Episodes:", "").strip() if episodes_tag else "Unknown"
    img_tag = soup.find("img", alt = title)

    another_search_url = f"https://9animetv.to/search?keyword={query.replace(' ', '+')}"
    response = requests.get(another_search_url, headers=headers)
    soup = bs(response.text, "html.parser")
    anime_links = soup.find_all("a", class_="film-poster-ahref")
    film_names = soup.find_all("h3", class_="film-name")
    titles = [name.find('a').text.strip() for name in film_names]
    title_to_url = {titles[i]: anime_links[i]["href"] for i in range(len(anime_links))}

    best_match, score = process.extractOne(query, titles, scorer=fuzz.token_sort_ratio)

    if score >= 70:
        another_link = f"https://9animetv.to{title_to_url[best_match]}"
        print(f"Found: {best_match} (coincidence: {score}%)")

    if img_tag:
        img_url = img_tag.get("data-src")
        if img_url:
            img_data = requests.get(img_url, headers=headers).content
            with open("anime_poster.jpg", "wb") as f:
                f.write(img_data)

    return [img_url, title, clean_text, studio, link, episodes,another_link,]

@dp.message(F.text & ~F.text.startswith("/") & ~F.text.in_(["🇬🇧 English", "🇺🇦 Українська"]))
async def anime_name(message:Message):
    query = message.text
    try:
        img_url, title, clean_text, studio, link, episodes, another_link, = await search_anime(query)
    except:
        anime_doesnt_found = await search_anime(query)
        await message.answer(text=anime_doesnt_found)

    if img_url:
        await bot.send_photo(chat_id=message.chat.id, photo=img_url, caption=f'<b>Title</b>: {title}\n<b>Studio</b>: {studio}\n<b>Episodes</b>: {episodes}', parse_mode='HTML')
        await message.answer(text=f'<b>Full description</b>: {clean_text}', parse_mode="HTML")
        await message.answer(text=f'<b>You can see it here</b>: {another_link}',  parse_mode="HTML")
    else:
        await message.answer(text=f"<b>Title:</b> {title}\n\n<b>Description:</b> {clean_text}\n\n<b>Studio:</b> {studio}\n<b>Episodes</b>: {episodes} \n\n {link}", parse_mode="HTML")
        await message.answer(text=f'<b>You can see it here</b>: {another_link}', parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())