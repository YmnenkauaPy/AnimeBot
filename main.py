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

async def search_anime_link(another_search_url, english_name):
    response = requests.get(another_search_url, headers=headers)
    soup = bs(response.text, "html.parser")
    anime_links = soup.find_all("a", class_="film-poster-ahref")
    film_names = soup.find_all("h3", class_="film-name")
    titles = [name.find('a').text.strip() for name in film_names]
    title_to_url = {titles[i]: anime_links[i]["href"] for i in range(len(anime_links))}

    query_parts = english_name.split()
    season_number = next((int(part) for part in query_parts if part.isdigit()), None)
    best_score = 0
    for title in titles:
        if english_name.lower() == title.lower():
            best_match = title
            best_score = 100
            break
    else:
        match, score = process.extractOne(english_name, titles, scorer=fuzz.partial_ratio)
        if score > best_score:
            best_match, best_score = match, score

    if season_number:
        for title in titles:
            if f"season {season_number}" in title.lower():
                best_match = title
                best_score += 15
                break

    if best_match and best_score >= 70:
        return f"https://9animetv.to{title_to_url[best_match]}"

async def search_anime_info(query):
    search_url = f"https://myanimelist.net/search/all?q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    soup = bs(response.text, "html.parser")

    anime_header = soup.find("h2", id="anime")
    article = anime_header.find_next_sibling("article") if anime_header else []

    anime_cards = article.find_all("a", class_="hoverinfo_trigger")
    if not anime_cards:
        return "Anime haven't been found"

    title_to_url = {card.text.strip(): card["href"] for card in anime_cards}
    titles = list(title_to_url.keys())
    query_parts = query.split()
    for i in query_parts:
        if i.isdigit():
            season = i
            break
        season = None

    similar_titles = []
    for i in titles:
        if season:
            if season in i:
                similar_titles.append(i)

        else:
            res = any(char.isdigit() for char in i)
            if not res:
                similar_titles.append(i)

    try:
        similar_titles.remove('')
    except:
        pass

    titles = []
    options = []
    for title in similar_titles:
        card = article.find('a', class_="hoverinfo_trigger", string = title)
        link = card["href"]
        soup = bs((requests.get(link, headers=headers)).text, 'html.parser')
        english_tag = soup.find("span", class_="dark_text", string="English:")
        english_name = english_tag.parent.text.replace("English:", "").strip() if english_tag else "Unknown"
        options.append(english_name.lower())
        titles.append(title)

    match, score = process.extractOne(query, options, scorer=fuzz.ratio)
    best_match = match
    best_title = titles[options.index(match)]

    card = article.find('a', class_="hoverinfo_trigger", string = best_title)
    link = card["href"]
    soup = bs((requests.get(link, headers=headers)).text, 'html.parser')
    description = soup.find("p", itemprop="description").text
    clean_text = re.sub(r"\[.*?\]", "", description).strip()
    studio = soup.find("span", class_ = "information studio author").text
    studio = " ".join(studio.split())
    episodes_tag = soup.find("span", class_="dark_text", string="Episodes:")
    episodes = episodes_tag.parent.text.replace("Episodes:", "").strip() if episodes_tag else "Unknown"

    img_tag = soup.find("img", alt = best_title)

    another_search_url = f"https://9animetv.to/search?keyword={best_match.replace(' ', '+')}"
    another_link = await search_anime_link(another_search_url, best_match.lower())

    if img_tag:
        img_url = img_tag.get("data-src")
        if img_url:
            img_data = requests.get(img_url, headers=headers).content
            with open("anime_poster.jpg", "wb") as f:
                f.write(img_data)

    return [img_url, best_title, clean_text, studio, episodes, another_link,]


@dp.message(F.text & ~F.text.startswith("/") & ~F.text.in_(["🇬🇧 English", "🇺🇦 Українська"]))
async def anime_name(message:Message):
    query = message.text
    try:
        img_url, title, clean_text, studio, episodes, another_link, = await search_anime_info(query)
    except:
        anime_doesnt_found = await search_anime_info(query)
        await message.answer(text=anime_doesnt_found)

    if img_url:
        await bot.send_photo(chat_id=message.chat.id, photo=img_url, caption=f'<b>Title</b>: {title}\n<b>Studio</b>: {studio}\n<b>Episodes</b>: {episodes}', parse_mode='HTML')
        await message.answer(text=f'<b>Full description</b>: {clean_text}', parse_mode="HTML")
        await message.answer(text=f'<b>You can see it here</b>: {another_link}',  parse_mode="HTML")
    else:
        await message.answer(text=f"<b>Title:</b> {title}\n\n<b>Description:</b> {clean_text}\n\n<b>Studio:</b> {studio}\n<b>Episodes</b>: {episodes}", parse_mode="HTML")
        await message.answer(text=f'<b>You can see it here</b>: {another_link}', parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())