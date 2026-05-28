import time

import fluxer
from fluxer import Cog

# avatar CDN base -- adjust if Fluxer changes their CDN path
CDN_BASE = "https://cdn.fluxer.app"


def _parse_id(raw: str) -> int:
    return int(raw.strip().lstrip("<@!").rstrip(">"))


class Utility(Cog):
    def __init__(self, bot: fluxer.Bot):
        self.bot = bot
        super().__init__()

    # -------------------------------------------------------------------------
    # ping
    # -------------------------------------------------------------------------
    @Cog.command(name="ping")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.channel.send(f"Pong! `{latency}ms`")

    # -------------------------------------------------------------------------
    # uptime
    # -------------------------------------------------------------------------
    @Cog.command(name="uptime")
    async def uptime(self, ctx):
        elapsed = int(time.monotonic() - self.bot.launch_time)
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        await ctx.channel.send(f"Uptime: `{h}h {m}m {s}s`")

    # -------------------------------------------------------------------------
    # serverinfo
    # -------------------------------------------------------------------------
    @Cog.command(name="serverinfo")
    async def serverinfo(self, ctx):
        if not ctx.guild:
            await ctx.channel.send("Use this command inside a server.")
            return
        g = ctx.guild
        embed = fluxer.Embed(title=g.name, color=0x5865F2)
        embed.add_field(name="ID", value=str(g.id), inline=True)
        embed.add_field(name="Owner", value=f"<@{g.owner_id}>", inline=True)
        embed.add_field(name="Members", value=str(g.member_count), inline=True)
        if getattr(g, "icon", None):
            embed.set_thumbnail(url=f"{CDN_BASE}/icons/{g.id}/{g.icon}.png")
        await ctx.channel.send(embed=embed)

    # -------------------------------------------------------------------------
    # userinfo  -- defaults to the caller if no target is given
    # -------------------------------------------------------------------------
    @Cog.command(name="userinfo")
    async def userinfo(self, ctx, target: str = None):
        if not ctx.guild:
            await ctx.channel.send("Use this command inside a server.")
            return
        uid = _parse_id(target) if target else ctx.author.id
        try:
            member = await self.bot.http.get_guild_member(ctx.guild.id, uid)
        except fluxer.FluxerException:
            await ctx.channel.send("Could not find that member.")
            return
        user = member.get("user", {})
        username = user.get("username", str(uid))
        discriminator = user.get("discriminator", "0")
        joined_at = member.get("joined_at", "Unknown")
        display = f"{username}#{discriminator}" if discriminator != "0" else username
        embed = fluxer.Embed(title=display, color=0x5865F2)
        embed.add_field(name="ID", value=str(uid), inline=True)
        embed.add_field(name="Joined Server", value=joined_at[:10] if joined_at != "Unknown" else joined_at, inline=True)
        avatar_hash = user.get("avatar")
        if avatar_hash:
            embed.set_thumbnail(url=f"{CDN_BASE}/avatars/{uid}/{avatar_hash}.png")
        await ctx.channel.send(embed=embed)

    # -------------------------------------------------------------------------
    # avatar  -- show full-size avatar for a user
    # -------------------------------------------------------------------------
    @Cog.command(name="avatar")
    async def avatar(self, ctx, target: str = None):
        if not ctx.guild:
            await ctx.channel.send("Use this command inside a server.")
            return
        uid = _parse_id(target) if target else ctx.author.id
        try:
            member = await self.bot.http.get_guild_member(ctx.guild.id, uid)
        except fluxer.FluxerException:
            await ctx.channel.send("Could not find that member.")
            return
        user = member.get("user", {})
        avatar_hash = user.get("avatar")
        if not avatar_hash:
            await ctx.channel.send(f"<@{uid}> has no avatar set.")
            return
        url = f"{CDN_BASE}/avatars/{uid}/{avatar_hash}.png?size=512"
        embed = fluxer.Embed(color=0x5865F2)
        embed.set_author(name=user.get("username", str(uid)))
        embed.set_image(url=url)
        await ctx.channel.send(embed=embed)

    # -------------------------------------------------------------------------
    # membercount
    # -------------------------------------------------------------------------
    @Cog.command(name="membercount")
    async def membercount(self, ctx):
        if not ctx.guild:
            await ctx.channel.send("Use this command inside a server.")
            return
        await ctx.channel.send(f"Members: **{ctx.guild.member_count}**")

    # -------------------------------------------------------------------------
    # help
    # -------------------------------------------------------------------------
    @Cog.command(name="help")
    async def help_cmd(self, ctx):
        p = self.bot.command_prefix
        # command_prefix can be a string, list, or callable
        if callable(p):
            p = "!"
        elif isinstance(p, list):
            p = p[0]

        embed = fluxer.Embed(title="Commands", color=0x5865F2)

        embed.add_field(
            name="Moderation (staff only)",
            value=(
                f"`{p}kick <user> [reason]` — kick a member\n"
                f"`{p}ban <user> [reason]` — ban a member\n"
                f"`{p}unban <user>` — unban by ID\n"
                f"`{p}mute <user> [reason]` — assign Muted role\n"
                f"`{p}unmute <user>` — remove Muted role\n"
                f"`{p}warn <user> [reason]` — log a warning\n"
                f"`{p}warns <user>` — list a user's warnings\n"
                f"`{p}clearwarns <user>` — wipe all warnings\n"
                f"`{p}purge <1-100>` — delete recent messages\n"
                f"`{p}lock` — lock the current channel\n"
                f"`{p}unlock` — unlock the current channel\n"
                f"`{p}slowmode <seconds>` — set slowmode (0 disables)"
            ),
            inline=False,
        )
        embed.add_field(
            name="Utility",
            value=(
                f"`{p}ping` — gateway latency\n"
                f"`{p}uptime` — bot uptime\n"
                f"`{p}serverinfo` — server details\n"
                f"`{p}userinfo [user]` — member info\n"
                f"`{p}avatar [user]` — full-size avatar\n"
                f"`{p}membercount` — total member count"
            ),
            inline=False,
        )
        embed.add_field(
            name="Fun",
            value=(
                f"`{p}8ball <question>` — magic 8-ball\n"
                f"`{p}coinflip` — heads or tails\n"
                f"`{p}roll [NdN]` — roll dice (default 1d6)\n"
                f"`{p}choose <a | b | ...>` — pick between options\n"
                f"`{p}reverse <text>` — reverse text\n"
                f"`{p}mock <text>` — SpOnGeBoB cAsE"
            ),
            inline=False,
        )
        await ctx.channel.send(embed=embed)


async def setup(bot: fluxer.Bot):
    await bot.add_cog(Utility(bot))
