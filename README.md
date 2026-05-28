# fluxerbot

A multipurpose Fluxer bot built with [fluxer.py](https://github.com/akarealemil/fluxer.py).

---

## Requirements

- Python 3.10 or higher
- A Fluxer bot token (create one in User Settings on Fluxer)

---

## Setup

```bash
# 1. clone or download this project, then cd into it

# 2. create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. install dependencies
pip install -r requirements.txt

# 4. copy the env template and fill it in
cp .env.example .env

# 5. run
python main.py
```

---

## Configuration

All configuration lives in `.env`.

| Variable | Default | Description |
|----------|---------|-------------|
| `FLUXER_BOT_TOKEN` | *(required)* | Your bot token from the Fluxer developer portal |
| `PREFIX` | `!` | Command prefix |
| `LOG_LEVEL` | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## File layout

```
main.py              bot entry point
cog_moderation.py    moderation commands
cog_utility.py       utility commands
cog_fun.py           fun commands
warns.json           auto-created; stores per-guild warning records
requirements.txt
.env.example
```

---

## Commands

### Moderation

All moderation commands require the corresponding Fluxer guild permission. Members without the required permission receive an error and the command does not execute.

| Command | Required permission | Description |
|---------|-------------------|-------------|
| `!kick <user> [reason]` | Kick Members | Remove a member from the server |
| `!ban <user> [reason]` | Ban Members | Permanently ban a member |
| `!unban <user>` | Ban Members | Unban by user ID |
| `!mute <user> [reason]` | Manage Roles | Assign the "Muted" role |
| `!unmute <user>` | Manage Roles | Remove the "Muted" role |
| `!warn <user> [reason]` | Kick Members | Add a warning to a user |
| `!warns <user>` | Kick Members | List all warnings for a user |
| `!clearwarns <user>` | Ban Members | Delete all warnings for a user |
| `!purge <1-100>` | Manage Messages | Bulk-delete recent messages in the channel |
| `!lock` | Manage Channels | Deny Send Messages for @everyone in the channel |
| `!unlock` | Manage Channels | Remove the Send Messages override |
| `!slowmode <seconds>` | Manage Channels | Set channel slowmode (0 to disable, max 21600) |

`<user>` accepts a plain snowflake ID or a mention (`@user`).

#### Mute setup

The mute/unmute commands rely on a role named exactly `Muted`. Create the role manually and deny **Send Messages** on every channel where you want it to apply. The bot will find the role by name and assign or remove it.

#### Warning storage

Warnings are stored in `warns.json` at the project root. Each entry is scoped to the guild and user so multi-server deployments are safe. Back this file up if you want to preserve warn history.

---

### Utility

| Command | Description |
|---------|-------------|
| `!ping` | Gateway round-trip latency in ms |
| `!uptime` | How long the bot has been running |
| `!serverinfo` | Name, ID, owner, and member count for the current server |
| `!userinfo [user]` | ID, username, and join date for a member (defaults to yourself) |
| `!avatar [user]` | Full-size avatar embed (defaults to yourself) |
| `!membercount` | Total member count for the server |
| `!help` | Lists all commands |

---

### Fun

| Command | Description |
|---------|-------------|
| `!8ball <question>` | Magic 8-ball response |
| `!coinflip` | Heads or tails |
| `!roll [NdN]` | Roll dice in NdN notation (e.g. `!roll 2d20`, default `1d6`) |
| `!choose <a \| b \| ...>` | Pick one option from a pipe-separated list |
| `!reverse <text>` | Reverse a string |
| `!mock <text>` | AlTeRnAtInG cAsE |

---

## Permission model

Permission checks are enforced by fluxer.py's `@has_permission()` decorator, which computes the member's effective guild permissions via bitfield (guild owner and admins pass all checks automatically). The check runs before the command body, so there is no path for a member to execute a gated command without the required permission.

Warns are keyed by `{guild_id}.{user_id}` so a user's warn count in one server cannot bleed into another.

---

## Notes

- Voice commands are not included. fluxer.py has full `VoiceClient` support with `FFmpegPCMAudio` if you want to add a music cog later.
- The `purge` command calls the raw HTTP client (`get_channel_messages` + `bulk_delete_messages`). If the Fluxer API enforces a message-age limit on bulk deletes, messages older than that threshold will need to be deleted individually.
- `lock`/`unlock` use channel permission overrides on the `@everyone` role. If a channel already has overrides you want to preserve, use `unlock` only to remove the deny override added by `lock`; it calls `delete_channel_permissions` rather than editing the full override set.
