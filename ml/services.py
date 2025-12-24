from typing import List, Type, Optional, Any
from database.crud import save_analysis_results
from ml.ml import analyze_items


async def process_items_pipeline(
        all_items: List[Any],
        item_type: str,
        model_class: Type
) -> Optional[List[Any]]:
    """
    Универсальный конвейер:
    1. Находит непроверенные элементы.
    2. Отправляет их в ML.
    3. Обновляет объекты в памяти.
    4. Сохраняет изменения в БД.
    5. Возвращает итоговый список ВАЖНЫХ элементов.

    Возвращает None, если произошла ошибка API OpenAI.
    """

    new_items = [i for i in all_items if not i.is_checked]

    if new_items:
        analyzed_data = await analyze_items(new_items, item_type=item_type)

        if analyzed_data is None:
            return None

        important_map = {item['original'].id: item['about'] for item in analyzed_data}
        results_to_save = []

        for item in new_items:
            is_imp = item.id in important_map
            about_text = important_map.get(item.id, None)

            results_to_save.append({
                'id': item.id,
                'is_important': is_imp,
                'about': about_text
            })

            item.is_checked = True
            item.is_important = is_imp
            item.about = about_text

        await save_analysis_results(model_class, results_to_save)

    items_to_show = [i for i in all_items if i.is_important]

    return items_to_show
