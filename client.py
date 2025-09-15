import asyncio
import aiohttp


async def main():
    async with aiohttp.ClientSession() as session:
        # # Регистрация
        # response = await session.post("http://localhost:8080/register",
        #                               json={"name": "pupkina",
        #                                     "password": "123fd54sa",
        #                                     }
        #                               )
        # print(response.status)
        # print(await response.text())
        #
        # Авторизация
        login_response = await session.post("http://localhost:8080/login",
                                      json={"name": "pupkina",
                                            "password": "123fd54sa",
                                            }
                                      )
        if login_response.status in (200, 201):
            token_data = await login_response.json()
            token = token_data["token"]  # Извлекаем токен из ответа
            user_id = 1

        #     # Создание объявления
        #     adv_response = await session.post("http://localhost:8080/advs",
        #                                   json={"name": "adv_5",
        #                                         "description": "rent2",
        #                                         "owner_id": user_id
        #                                         },
        #                                   headers={"Authorization": f"Bearer {token}"}
        #                                   )
        #     print(adv_response.status)
        #     print(await adv_response.text())
        # else:
        #     print(f"Ошибка авторизации: {login_response.status}")
        #     print(await login_response.text())

        #     # Получение объявления
        #     response = await session.get("http://localhost:8080/advs/5")
        #     print(response.status)
        #     if response.content_type == 'application/json':
        #         print(await response.json())
        #     else:
        #         print(await response.text())
        # else:
        #     print(f"Ошибка авторизации: {login_response.status}")
        #     print(await login_response.text())

        #     # Изменение объявления
        #     adv_response = await session.patch("http://localhost:8080/advs/5",
        #                                       json={"name": "adv_5",
        #                                             "description": "rent10",
        #                                             "owner_id": user_id
        #                                             },
        #                                       headers={"Authorization": f"Bearer {token}"}
        #                                       )
        #     print(adv_response.status)
        #     print(await adv_response.text())
        # else:
        #     print(f"Ошибка авторизации: {login_response.status}")
        #     print(await login_response.text())

            # Удаление объявления
            adv_response = await session.delete("http://localhost:8080/advs/5",
                                               headers={"Authorization": f"Bearer {token}"}
                                               )
            print(adv_response.status)
            print(await adv_response.text())
        else:
            print(f"Ошибка авторизации: {login_response.status}")
            print(await login_response.text())

        await session.close()

asyncio.run(main())