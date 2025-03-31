import asyncio
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from typing import Final
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
from bs4 import BeautifulSoup as bs
from thefuzz import fuzz, process
import commands

TOKEN : Final = '7827932477:AAEJhhSuRLk11lors5UyGgUYk6ilNMkXxWI'
bot = Bot(token = TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_router(commands.router)

HEADERS = {"User-Agent": "Mozilla/5.0"}

async def fetch(session, url):
    async with session.get(url, headers=HEADERS) as response:
        return await response.text()

async def search_anime_link(session, another_search_url, english_name, season):
    html = await fetch(session, another_search_url)
    soup = bs(html, "html.parser")
    anime_links = soup.find_all("a", class_="film-poster-ahref")
    film_names = soup.find_all("h3", class_="film-name")
    titles = [name.find("a").text.strip() for name in film_names]
    title_to_url = {titles[i]: anime_links[i]["href"] for i in range(len(anime_links))}

    similar_titles = [i for i in titles if season in i] if season else titles
    match, score = process.extractOne(english_name, similar_titles, scorer=fuzz.ratio)

    return f"https://9animetv.to{title_to_url.get(match, '')}"

async def search_anime_info(query):
    search_url = f"https://myanimelist.net/search/all?q={query.replace(' ', '+')}"

    async with aiohttp.ClientSession() as session:
        html = await fetch(session, search_url)
        soup = bs(html, "html.parser")

        anime_header = soup.find("h2", id="anime")
        article = anime_header.find_next_sibling("article") if anime_header else None
        if not article:
            return "Anime haven't been found"

        anime_cards = article.find_all("a", class_="hoverinfo_trigger")
        if not anime_cards:
            return "Anime haven't been found"

        titles = [card.text.strip() for card in anime_cards]
        season = next((i for i in query.split() if i.isdigit()), None)

        best_title = next((i for i in titles if i.lower() == query.lower()), None)
        if not best_title:
            if season:
                similar_titles = [i for i in titles if any(char.isdigit() for char in i) and season in i]
            else:
                similar_titles = [i for i in titles if not any(char.isdigit() for char in i)]
            best_match, score = process.extractOne(query, similar_titles, scorer=fuzz.ratio)
            best_title = best_match

        anime_page_url = article.find("a", class_="hoverinfo_trigger", string=best_title)["href"]
        anime_html = await fetch(session, anime_page_url)
        soup = bs(anime_html, "html.parser")

        english_tag = soup.find("span", class_="dark_text", string="English:")
        best_match = english_tag.parent.text.replace("English:", "").strip() if english_tag else "Unknown"

        description = soup.find("p", itemprop="description")
        clean_text = re.sub(r"\[.*?\]", "", description.text.strip()) if description else "No description available"

        studio_tag = soup.find("span", class_="information studio author")
        studio = " ".join(studio_tag.text.split()) if studio_tag else "Unknown"

        episodes_tag = soup.find("span", class_="dark_text", string="Episodes:")
        episodes = episodes_tag.parent.text.replace("Episodes:", "").strip() if episodes_tag else "Unknown"

        img_tag = soup.find("img", alt=best_title)
        img_url = img_tag.get("data-src") if img_tag else None

        another_search_url = f"https://9animetv.to/search?keyword={best_match.replace(' ', '+')}"
        another_link = await search_anime_link(session, another_search_url, best_match.lower(), season)

        return [img_url, best_title, clean_text, studio, episodes, another_link]

@dp.message(F.text & ~F.text.startswith("/") & ~F.text.in_(["🇬🇧 English", "🇺🇦 Українська"]))
async def anime_name(message: Message):
    query = message.text
    try:
        result = await search_anime_info(query)
        if isinstance(result, str):
            await message.answer(text=result)
            return
        img_url, title, clean_text, studio, episodes, another_link = result
    except Exception:
        await message.answer(text="Anime haven't been found")
        return

    text_message = f"<b>Title</b>: {title}\n<b>Studio</b>: {studio}\n<b>Episodes</b>: {episodes}"

    if img_url:
        await bot.send_photo(chat_id=message.chat.id, photo=img_url, caption=text_message, parse_mode="HTML")
    else:
        await message.answer(text=text_message, parse_mode="HTML")

    await message.answer(text=f"<b>Full description</b>: {clean_text}", parse_mode="HTML")
    await message.answer(text=f"<b>You can see it here</b>: {another_link}", parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())