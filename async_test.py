import asyncio

async def hello():
    print("Hello")
    await asyncio.sleep(5)
    print("Hi 2")

asyncio.run(hello())

