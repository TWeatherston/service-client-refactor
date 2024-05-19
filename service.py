import httpx

from utils import inject_client
from main import Service


@inject_client(service=Service.DATA_CATALOGUE)
async def make_request(client: httpx.Client, **kwargs) -> dict:
    resp = client.get("/endpoint", **kwargs)
    return resp.json()


async def main():
    await make_request()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
