import asyncio
import json
import logging
import os

import fluxer
from fluxer import Cog
from fluxer import Permissions
from fluxer.checks import has_permission
from fluxer.enums import Permissions

log = logging.getLogger(__name__)
WARNS_FILE = "warns.json"


def _load_warns() -> dict:
    if not os.path.exists(WARNS_FILE):
        return {}
    with open(WARNS_FILE) as f:
        return json.load(f)


def _save_warns(data: dict) -> None:
    with open(WARNS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _parse_id(raw: str) -> int:
    # handles plain snowflake IDs and mention formats <@123> / <@!123>
    return int(raw.strip().lstrip("<@!").rstrip(">"))


class Moderation(Cog):
    def __init__(self, bot: fluxer.Bot):
        self.bot = bot
        super().__init__(bot)

    # -------------------------------------------------------------------------
    # kick
    # -------------------------------------------------------------------------
    @Cog.command(name="kick")
    @has_permission(Permissions.KICK_MEMBERS)
    async def kick(self, ctx, target: str, *, reason: str = "No reason provided"):
        uid = _parse_id(target)
        try:
            await ctx.guild.kick(uid, reason=reason)
            await ctx.channel.send(f"Kicked <@{uid}>. Reason: {reason}")
        except fluxer.FluxerException as exc:
            await ctx.channel.send(f"Failed to kick: {exc}")

    # -------------------------------------------------------------------------
    # ban
    # -------------------------------------------------------------------------
    @Cog.command(name="ban")
    @has_permission(Permissions.BAN_MEMBERS)
    async def ban(self, ctx, target: str, *, reason: str = "No reason provided"):
        uid = _parse_id(target)
        try:
            await ctx.guild.ban(uid, reason=reason)
            await ctx.channel.send(f"Banned <@{uid}>. Reason: {reason}")
        except fluxer.FluxerException as exc:
            await ctx.channel.send(f"Failed to ban: {exc}")

    # -------------------------------------------------------------------------
    # unban
    # -------------------------------------------------------------------------
    @Cog.command(name="unban")
    @has_permission(Permissions.BAN_MEMBERS)
    async def unban(self, ctx, target: str):
        uid = _parse_id(target)
        try:
            await ctx.guild.unban(uid)
            await ctx.channel.send(f"Unbanned <@{uid}>.")
        except fluxer.FluxerException as exc:
            await ctx.channel.send(f"Failed to unban: {exc}")

    # -------------------------------------------------------------------------
    # mute  (role-based: requires a "Muted" role with restricted send perms)
    # -------------------------------------------------------------------------
    @Cog.command(name="mute")
    @has_permission(Permissions.MANAGE_ROLES)
    async def mute(self, ctx, target: str, *, reason: str = "No reason provided"):
        uid = _parse_id(target)
        roles = await self.bot._http.get_guild_roles(ctx.guild.id)
        muted_role = next((r for r in roles if r.get("name") == "Muted"), None)
        if not muted_role:
            await ctx.channel.send(
                "No 'Muted' role found. Create one and deny Send Messages on it."
            )
            return
        try:
            await self.bot._http.add_guild_member_role(
                ctx.guild.id, uid, int(muted_role["id"])
            )
            await ctx.channel.send(f"Muted <@{uid}>. Reason: {reason}")
        except fluxer.FluxerException as exc:
            await ctx.channel.send(f"Failed to mute: {exc}")

    # -------------------------------------------------------------------------
    # unmute
    # -------------------------------------------------------------------------
    @Cog.command(name="unmute")
    @has_permission(Permissions.MANAGE_ROLES)
    async def unmute(self, ctx, target: str):
        uid = _parse_id(target)
        roles = await self.bot._http.get_guild_roles(ctx.guild.id)
        muted_role = next((r for r in roles if r.get("name") == "Muted"), None)
        if not muted_role:
            await ctx.channel.send("No 'Muted' role found.")
            return
        try:
            await self.bot._http.remove_guild_member_role(
                ctx.guild.id, uid, int(muted_role["id"])
            )
            await ctx.channel.send(f"Unmuted <@{uid}>.")
        except fluxer.FluxerException as exc:
            await ctx.channel.send(f"Failed to unmute: {exc}")

    # -------------------------------------------------------------------------
    # warn  -- persisted to warns.json, keyed per guild+user
    # -------------------------------------------------------------------------
    @Cog.command(name="warn")
    @has_permission(Permissions.KICK_MEMBERS)
    async def warn(self, ctx, target: str, *, reason: str = "No reason provided"):
        uid = _parse_id(target)
        data = _load_warns()
        key = f"{ctx.guild.id}.{uid}"
        data.setdefault(key, []).append({
            "reason": reason,
            "mod": str(ctx.author.id),
        })
        _save_warns(data)
        count = len(data[key])
        await ctx.channel.send(f"Warned <@{uid}> (#{count}). Reason: {reason}")

    # -------------------------------------------------------------------------
    # warns  -- list warnings for a user
    # -------------------------------------------------------------------------
    @Cog.command(name="warns")
    @has_permission(Permissions.KICK_MEMBERS)
    async def warns_cmd(self, ctx, target: str):
        uid = _parse_id(target)
        data = _load_warns()
        entries = data.get(f"{ctx.guild.id}.{uid}", [])
        if not entries:
            await ctx.channel.send(f"<@{uid}> has no warnings.")
            return
        lines = [f"**Warnings for <@{uid}>** ({len(entries)} total):"]
        for i, w in enumerate(entries, 1):
            lines.append(f"`{i}.` {w['reason']} — by <@{w['mod']}>")
        await ctx.channel.send("\n".join(lines))

    # -------------------------------------------------------------------------
    # clearwarns  -- wipe all warnings for a user
    # -------------------------------------------------------------------------
    @Cog.command(name="clearwarns")
    @has_permission(Permissions.BAN_MEMBERS)
    async def clearwarns(self, ctx, target: str):
        uid = _parse_id(target)
        data = _load_warns()
        key = f"{ctx.guild.id}.{uid}"
        removed = len(data.pop(key, []))
        _save_warns(data)
        await ctx.channel.send(f"Cleared {removed} warning(s) for <@{uid}>.")

    # -------------------------------------------------------------------------
    # purge  -- bulk delete up to 100 messages in the current channel
    # -------------------------------------------------------------------------
    @Cog.command(name="purge")  
    @has_permission(Permissions.MANAGE_MESSAGES)  
    async def purge(self, ctx, amount: int):  
        if not 1 <= amount <= 100:  
            await ctx.channel.send("Amount must be between 1 and 100.")  
            return  
        try:    
            messages = await self.bot._http.get_messages(  
                ctx.channel.id, limit=amount + 1  
            )  
            ids = [  
                str(m["id"]) 
                for m in messages  
                if str(m["id"]) != str(ctx.id)
            ][:amount]  
  
            if not ids:  
                await ctx.channel.send("Nothing to delete.")  
                return  
  
            if len(ids) == 1:  
                await self.bot._http.delete_message(ctx.channel.id, ids[0])  
            else:  
                await self.bot._http.delete_messages(ctx.channel.id, ids)  
  
            note = await ctx.channel.send(f"Deleted {len(ids)} message(s).")  
            await asyncio.sleep(4)  
            await note.delete()  
  
        except fluxer.FluxerException as exc:  
            await ctx.channel.send(f"Purge failed: {exc}")

    # -------------------------------------------------------------------------
    # lock  -- deny SEND_MESSAGES for @everyone in the current channel
    # -------------------------------------------------------------------------
    @Cog.command(name="lock")
    @has_permission(Permissions.MANAGE_CHANNELS)
    async def lock(self, ctx):  
        everyone_role_id = ctx.guild.id    
        channel_data = await self.bot._http.request(  
            self.bot._http._route("GET", "/channels/{channel_id}", channel_id=ctx.channel.id)  
        )  

        current_overwrite = None  
        for overwrite in channel_data.get("permission_overwrites", []):  
            if int(overwrite["id"]) == everyone_role_id:  
                current_overwrite = overwrite  
                break  

        current_deny = int(current_overwrite["deny"]) if current_overwrite else 0  
        new_deny = current_deny | Permissions.SEND_MESSAGES  
        current_allow = int(current_overwrite["allow"]) if current_overwrite else 0  
      
        await self.bot._http.edit_channel_permissions(  
            ctx.channel.id,  
            everyone_role_id,  
            allow=str(current_allow),  
            deny=str(new_deny),  
            type=0  
        )  
        await ctx.reply("Channel locked.")  

    # -------------------------------------------------------------------------
    # unlock  -- restore SEND_MESSAGES for @everyone
    # -------------------------------------------------------------------------
    @Cog.command(name="unlock")
    @has_permission(Permissions.MANAGE_CHANNELS)
    async def unlock(self, ctx):
        everyone_role_id = ctx.guild.id  
        channel_data = await self.bot._http.request(  
            self.bot._http._route("GET", "/channels/{channel_id}", channel_id=ctx.channel.id)  
        )  

        current_overwrite = None  
        for overwrite in channel_data.get("permission_overwrites", []):  
            if int(overwrite["id"]) == everyone_role_id:  
                current_overwrite = overwrite  
                break  
      
        if not current_overwrite:  
            await ctx.reply("🔓 Channel was not locked.")  
            return  

        current_deny = int(current_overwrite["deny"])  
        new_deny = current_deny & ~Permissions.SEND_MESSAGES  
        current_allow = int(current_overwrite["allow"])  

        if new_deny == 0 and current_allow == 0:  
            await self.bot._http.edit_channel_permissions(  
                ctx.channel.id,  
                everyone_role_id,  
                allow="0",  
                deny="0",  
                type=0  
            )  
        else:  
            await self.bot._http.edit_channel_permissions(  
                ctx.channel.id,  
                everyone_role_id,  
                allow=str(current_allow),  
                deny=str(new_deny),  
                type=0  
            )  
      
        await ctx.reply("Channel unlocked.")

    # -------------------------------------------------------------------------
    # slowmode  -- set channel slowmode in seconds (0 to disable)
    # -------------------------------------------------------------------------
    @Cog.command(name="slowmode")  
    @has_permission(Permissions.MANAGE_CHANNELS)  
    async def slowmode(self, ctx, seconds: int):  
        if not 0 <= seconds <= 21600:  
            await ctx.channel.send("Slowmode must be 0-21600 seconds.")  
            return  
        try:  
            await self.bot._http.modify_channel(  
                ctx.channel.id, rate_limit_per_user=seconds  
            )  
            if seconds == 0:  
                await ctx.channel.send("Slowmode disabled.")  
            else:  
                await ctx.channel.send(f"Slowmode set to {seconds}s.")  
        except fluxer.FluxerException as exc:  
            await ctx.channel.send(f"Failed to set slowmode: {exc}")


async def setup(bot: fluxer.Bot):
    await bot.add_cog(Moderation(bot))