import asyncio
import os
import time
import discord  # type: ignore
from config import config


client = discord.Client()

NOT_ALLOWED = [
    "import os"
]

def time_took(st: float):
    return round(time.time() - st, 2)

def stdembed(title: str, time: float, resp: str, color: int):
    embed=discord.Embed(title=title, description=f"Took {time_took(time)} seconds to complete.", color=color)
    embed.add_field(name="Response", value=f"```\n{resp}```", inline=True)
    return embed

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} ({client.user.id})")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not message.content.startswith("```"):
        return

    asyncio.create_task(handle(message))

async def handle(message: discord.Message):
    msg = message.content.split("\n")

    with open((file := f"temp/{message.id}.v"), "w+") as f:
        for m in msg:
            if m.startswith("```"):
                continue

            if m in NOT_ALLOWED:
                await message.reply("Something in your code isn't allowed. Most likely a blacklisted import.")
                return

            f.write(m + "\n")

    cmd = f"v -gc boehm run {file}"

    st = time.time()

    proc = await asyncio.create_subprocess_shell(cmd, 
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = None, None
    timed_out = False

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
    except asyncio.TimeoutError:
        timed_out = True

    os.remove(file)

    if stderr or timed_out:
        if stderr:
            resp = "".join(stderr.decode("utf-8").split(": ", 1)[1:])
        else:
            resp = "Timed out."

        if config["log"]:
            print(f"{message.author.name} executed a {len(msg) - 2} line code, that \u001b[31mfailed\u001b[0m")

        await message.reply(embed=stdembed(title="Failed", time=st, resp=resp, color=0xf50000))
        return

    if not stdout:
        resp = "No output"
    else:
        resp = stdout.decode("utf-8")

    if config["log"]:
        print(f"{message.author.name} executed a {len(msg) - 2} line code, that was \u001b[32msuccessful\u001b[0m and took {time_took(st)} seconds")

    await message.reply(embed=stdembed(title="Success", time=st, resp=resp, color=0x4ef500))
        

client.run(config["secret"])
