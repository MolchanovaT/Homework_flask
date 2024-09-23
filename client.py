import asyncio
import sys

from aiohttp import ClientSession


async def main():
    async with ClientSession() as session:
        response = await session.post(
            "http://0.0.0.0:8080/user/",
            json={"name": "user_1", "password": '1234'},
            ssl=False
        )
        print(response.status)
        print(await response.text())

        response = await session.get(
            "http://0.0.0.0:8080/user/1",
        )
        print(response.status)
        print(await response.text())

        # response = await session.post(
        #     "http://0.0.0.0:8080/announcement/",
        #     json={"title": "announcement_1", "description": "description_1", "user_id": 1},
        # )
        # print(response.status)
        # print(await response.text())

        # response = await session.patch(
        #     "http://0.0.0.0:8080/announcement/1",
        #     json={"title": "new_title", "description": "new_description"}
        #
        # )
        # print(response.status)
        # print(await response.text())

        # response = await session.get(
        #     "http://0.0.0.0:8080/announcement/1",
        # )
        # print(response.status)
        # print(await response.text())
        #
        # response = await session.delete(
        #     "http://0.0.0.0:8080/announcement/1",
        #
        # )
        # print(response.status)
        # print(await response.text())

if sys.platform == "win32":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(main())

# import asyncio
# from aiohttp import ClientSession
#
#
# async def main():
#     url = "https://stackoverflow.com/"
#
#     async with ClientSession(trust_env=True) as session:
#         async with session.get(url) as resp:
#             print(resp.status)
#
# asyncio.run(main())
