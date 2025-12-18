from aiogram import Router, types, F
from sqlalchemy import select, update
from database.session import async_session
from database.models import Link
import datetime
import html

from ml.ml import analyze_items

router = Router()

async def save_analysis_results(model, analysis_results: list[dict]):
    """Сохраняет результаты (is_checked, is_important, about) в БД."""
    if not analysis_results:
        return
    async with async_session() as session:
        for item in analysis_results:
            stmt = (
                update(model)
                .where(model.id == item['id'])
                .values(
                    is_checked=True,
                    is_important=item['is_important'],
                    about=item['about']
                )
            )
            await session.execute(stmt)
        await session.commit()

async def get_daily_links(chat_id: int) -> list[Link]:
    """
    Достаем ссылки за последние 24 часа.
    """
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    
    async with async_session() as session:
        query = select(Link).where(
            Link.chat_id == chat_id,
            Link.created_at >= yesterday
        ).order_by(Link.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()


@router.message(F.text == "/links")
async def get_links_handler(message: types.Message):
    all_links = await get_daily_links(chat_id=message.chat.id)

    if not all_links:
        await message.answer("📭 Ссылок за последние сутки не было.")
        return

    status_msg = await message.answer("🔎 Проверяю ссылки...")

    # 2. Ищем, что из этого новое (еще не проверяли)
    new_links = [link for link in all_links if not link.is_checked]

    # 3. Если есть новые — анализируем
    if new_links:
        analyzed_data = await analyze_items(new_links, item_type="link")

        # ЗАЩИТА: Если ML вернул None (ошибка), прекращаем работу, чтобы не испортить данные
        if analyzed_data is None:
            await status_msg.edit_text("⚠️ Временная ошибка мозга (OpenAI). Попробуй через минуту.")
            return

        # Словарь важных ID для быстрого поиска: {id: 'About text'}
        important_map = {item['original'].id: item['about'] for item in analyzed_data}

        results_to_save = []

        # Проходим по всем НОВЫМ ссылкам
        for link in new_links:
            # Если ID есть в ответе ML — значит важно. Нет — мусор.
            is_imp = link.id in important_map
            about_text = important_map.get(link.id, None)

            # Подготовка для БД
            results_to_save.append({
                'id': link.id,
                'is_important': is_imp,
                'about': about_text
            })

            # Обновление в памяти (чтобы показать юзеру прямо сейчас)
            link.is_checked = True
            link.is_important = is_imp
            link.about = about_text

        # Сохраняем пачкой
        await save_analysis_results(Link, results_to_save)

    links_to_show = [link for link in all_links if link.is_important]

    # <--- ВОТ ЭТА ПРОВЕРКА, КОТОРОЙ НЕ ХВАТАЛО --->
    if not links_to_show:
        await status_msg.edit_text("🤷‍♂️ Ссылки за сутки были, но ничего важного (мемы, спам или оффтоп).")
        return
    # <--------------------------------------------->

    # 5. Вывод (сюда мы дойдем, только если список не пустой)
    text = "<b>🔗 Важные ссылки за 24 часа:</b>\n\n"
    for link in links_to_show:
        about = html.escape(link.about or link.context or "Ссылка")
        text += f"🔹 <b>{about}</b>\n   └ {link.url}\n\n"

    await status_msg.edit_text(text, disable_web_page_preview=True, parse_mode="HTML")

