from aiogram.fsm.context import FSMContext

async def push_state(state: FSMContext, fsm_state):
    data = await state.get_data()
    history = data.get("history", [])

    history.append(fsm_state)
    await state.update_data(history=history)


async def pop_state(state: FSMContext) -> str | None:
    data = await state.get_data()
    history = data.get("history", [])

    if len(history) < 2:
        return None  # некуда возвращаться

    history.pop()          # убираем текущий
    prev_state = history[-1]

    await state.update_data(history=history)
    return prev_state