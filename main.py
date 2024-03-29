import asyncio
import os
import time
import discord  # type: ignore
from config import config
import re

client = discord.Client()

NOT_ALLOWED = [
    "import os"
]

if not os.path.exists("temp"):
    os.mkdir("temp")

def time_took(st: float) -> float:
    return round(time.time() - st, 2)

def stdembed(title: str, time: float, resp: str, color: int) -> discord.Embed:
    if len(resp) >= 1024:
        resp = "Response too long. Truncated."

    embed=discord.Embed(title=title, description=f"Took {time_took(time)} seconds to complete.", color=color)
    embed.add_field(name="Response", value=f"```\n{resp}```", inline=True)
    return embed

@client.event
async def on_ready()  -> None:
    print(f"Logged in as {client.user.name} ({client.user.id})")

@client.event
async def on_message(message: discord.Message)  -> None:
    if message.author.bot:
        return

    asyncio.create_task(handle(message))

async def handle(message: discord.Message) -> None:
    msg = message.content.split("\n")

    is_v = False

    with open((file := f"temp/{message.id}.v"), "w+") as f:
        for m in msg:
            if m == "```v":
                is_v = True
                continue
        
            if not is_v:
                continue

            if m in NOT_ALLOWED:
                await message.reply("Something in your code isn't allowed. Most likely a blacklisted import.")
                return
            
            if m == "```":
                break

            f.write(m + "\n")

    if not is_v:
        os.remove(file)
        return

    cmd = f"v run {file}"

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
            resp = re.sub(r"temp\/\d*.v:\d*:\d*:\s", "", stderr.decode("utf-8"))
        else:
            resp = "Timed out."

        if config["log"]:
            print(f"{message.author.name} executed a {len(msg) - 2} line code, that \u001b[31mfailed\u001b[0m")

        await message.reply(embed=stdembed(title="Failed", time=st, resp=resp, color=0xf50000))
        return

    if not stdout:
        resp = "No output"
    else:
        try:
            resp = stdout.decode("utf-8")
        except:
            await message.reply(embed=stdembed(title="Failed", time=st, resp="Unknown error.", color=0xf50000))
            return

    if config["log"]:
        print(f"{message.author.name} executed a {len(msg) - 2} line code, that was \u001b[32msuccessful\u001b[0m and took {time_took(st)} seconds")

    await message.reply(embed=stdembed(title="Success", time=st, resp=resp, color=0x4ef500))
        

client.run(config["secret"])
