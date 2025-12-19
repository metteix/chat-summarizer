from aiogram import Router, types
from aiogram.filters import Command
import html
import asyncio
from database.crud import get_daily_data, get_chat_settings
from database.models import Task, Link, Document, Mention, Hashtag

# Наш универсальный конвейер
from ml.services import process_items_pipeline

router = Router()


@router.message(Command("summary"))
async def cmd_summary(message: types.Message):
    # 1. Проверки настроек
    settings = await get_chat_settings(message.chat.id)
    if not settings:
        await message.answer("❌ Бот не активирован. Напишите /on")
        return

    # 2. Получаем ВСЕ данные за сутки (сырые)
    data = await get_daily_data(message.chat.id)

    if not any(data.values()):
        await message.answer("📭 За последние 24 часа данных не найдено.")
        return

    status_msg = await message.answer("🧠 Собираю полную сводку (анализирую всё сразу)...")

    # 3. Подготовка задач для параллельного запуска
    # Мы создаем список задач (coroutine), но не запускаем их (await) прямо сейчас
    tasks_map = {}

    if settings.include_tasks and data.get("tasks"):
        tasks_map["tasks"] = process_items_pipeline(data["tasks"], "task", Task)

    if settings.include_links and data.get("links"):
        tasks_map["links"] = process_items_pipeline(data["links"], "link", Link)

    if settings.include_docs and data.get("documents"):
        tasks_map["docs"] = process_items_pipeline(data["documents"], "doc", Document)

    if settings.include_mentions and data.get("mentions"):
        tasks_map["mentions"] = process_items_pipeline(data["mentions"], "mention", Mention)

    if settings.include_hashtags and data.get("hashtags"):
        tasks_map["hashtags"] = process_items_pipeline(data["hashtags"], "hashtag", Hashtag)

    if not tasks_map:
        await status_msg.edit_text("🤷‍♂️ Данные есть, но все категории отключены в настройках.")
        return

    # 4. ЗАПУСК ВСЕГО ОДНОВРЕМЕННО (Parallel Execution)
    # keys сохраняем, чтобы потом понять, какой результат к чему относится
    keys = list(tasks_map.keys())
    coroutines = list(tasks_map.values())

    # asyncio.gather вернет список результатов в том же порядке
    results_list = await asyncio.gather(*coroutines)

    # Собираем словарь результатов {category: [items]}
    processed_data = dict(zip(keys, results_list))

    # Если везде вернулся None (упал OpenAI), сообщаем
    if all(res is None for res in results_list):
        await status_msg.edit_text("⚠️ Временная ошибка мозга (OpenAI). Попробуйте позже.")
        return

    # 5. Формирование отчета
    report = [f"<b>📊 СВОДКА ЗА 24 ЧАСА</b>\n"]

    chat_username = message.chat.username
    clean_id = str(message.chat.id).replace("-100", "")

    def get_msg_link(msg_id):
        if chat_username:
            return f"https://t.me/{chat_username}/{msg_id}"
        return f"https://t.me/c/{clean_id}/{msg_id}"

    # --- ЗАДАЧИ ---
    tasks = processed_data.get("tasks")
    if tasks:  # Если не None и не пустой список
        report.append("📝 <b>Задачи:</b>")
        for t in tasks:
            # Ссылка на сообщение с задачей
            url = get_msg_link(t.message_id)
            about = html.escape(t.about or t.task_name)
            report.append(f"▫️ <a href='{url}'>{about}</a>")
        report.append("")

    # --- ССЫЛКИ ---
    links = processed_data.get("links")
    if links:
        report.append("🔗 <b>Ссылки:</b>")
        for l in links:
            # Тут ссылка ведет на URL ресурса
            about = html.escape(l.about or "Ссылка")
            report.append(f"🔹 <a href='{l.url}'>{about}</a>")
        report.append("")

    # --- ДОКУМЕНТЫ ---
    docs = processed_data.get("docs")
    if docs:
        report.append("📂 <b>Файлы:</b>")
        for d in docs:
            url = get_msg_link(d.message_id)
            about = html.escape(d.about or d.document_name)
            report.append(f"📄 <a href='{url}'>{about}</a>")
        report.append("")

    # --- УПОМИНАНИЯ ---
    mentions = processed_data.get("mentions")
    if mentions:
        report.append("🔔 <b>Важные вызовы:</b>")
        # Группировка по тегу (@user)
        m_map = {}
        for m in mentions:
            tag = m.mention
            if tag not in m_map: m_map[tag] = []

            url = get_msg_link(m.message_id)
            about = html.escape(m.about or "Вызов")
            m_map[tag].append(f"<a href='{url}'>{about}</a>")

        for user, links_list in m_map.items():
            # Вывод: @user: Сделать презентацию, Прийти на пару
            links_str = "; ".join(links_list)
            report.append(f"👤 <b>{user}</b>: {links_str}")
        report.append("")

    # --- ХЭШТЕГИ ---
    hashtags = processed_data.get("hashtags")
    if hashtags:
        report.append("Wait... #️⃣ <b>Темы дня:</b>")
        # Группируем, чтобы не спамить
        h_map = {}
        for h in hashtags:
            tag = h.hashtag
            if tag not in h_map: h_map[tag] = []
            url = get_msg_link(h.message_id)
            about = html.escape(h.about or "Тема")
            h_map[tag].append(f"<a href='{url}'>{about}</a>")

        for tag, items in h_map.items():
            report.append(f"<b>{tag}</b>")
            for item in items:
                report.append(f"  └ {item}")
        report.append("")

    # Финальная проверка на пустоту (вдруг ML всё отфильтровал как мусор)
    if len(report) <= 1:
        await status_msg.edit_text(
            "🤷‍♂️ За сутки было много активности, но нейросеть посчитала всё это неважным (оффтоп).")
        return

    final_text = "\n".join(report)
    await status_msg.edit_text(final_text, disable_web_page_preview=True, parse_mode="HTML")
