from aiogram import Router, types

collector_router = Router()

@collector_router.message()
async def collector_stub(message: types.Message):
    pass
