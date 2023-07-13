import random
import string

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from redis import asyncio as aioredis


app = FastAPI()
redis = aioredis.Redis()


def generate_link(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.sample(alphabet, length))


async def create_link(long_link: str) -> str:
    short = generate_link()
    async with redis.pipeline(transaction=True) as pipe:
        while (await pipe.exists(short).execute()) == 1:
            short = generate_link()
        await pipe.set(short, long_link).execute()
    return short


async def get_link(short_link: str) -> str | None:
    async with redis.pipeline() as pipe:
        result = await pipe.get(short_link).execute()
    if not result:
        return None
    return result[0].decode()


class LongLink(BaseModel):
    long_link: str


class ShortLinkCreated(LongLink):
    short_link: str



@app.post("/create")
async def create(long: LongLink) -> ShortLinkCreated:
    short = await create_link(long.long_link)
    response = ShortLinkCreated(long_link=long.long_link, short_link=short)
    return JSONResponse(response.json(), status_code=status.HTTP_201_CREATED)


@app.get("/{link}")
async def getlink(link: str):
    long = await get_link(link)
    if not long:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return RedirectResponse(long)
