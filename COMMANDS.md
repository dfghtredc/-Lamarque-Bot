# Lamarque Bot — Command Reference

> **Prefix:** `!` | **Slash commands:** available via `/` for most commands

---

## 🔧 Setup & Config
> Admin only

| Command | Description |
|---------|-------------|
| `!setup` | Opens a native Discord form to configure all channels at once |
| `/setup` | Same as `!setup` — opens the setup modal |
| `!status` | Show current bot config in one embed |
| `/status` | Same as `!status` — ephemeral (only you see it) |
| `!setquoteboard #channel` | Set where quotes get saved |
| `!setechofeed #channel` | Set where auto quotes get posted |
| `!setquoterole @role` | Restrict who can save/pull quotes (admins always bypass) |
| `!setquotestream <minutes>` | Set how often auto quotes fire |
| `!quotestop` | Stop the auto quote feed |
| `!quotestart` | Start the auto quote feed |
| `!setwelcome #channel [message]` | Set welcome channel and optional custom message |
| `!testwelcome` | Preview the welcome message |
| `!setqotd #channel` | Set channel for daily Quote of the Day |
| `!setspam <threshold> <window> [timeout_minutes]` | Set anti-spam config (e.g. `!setspam 5 5 10`) |

---

## 📌 Quoteboard — Saving
> Requires quote role if set, otherwise open to everyone

| Command | Description |
|---------|-------------|
| `!savequote` | Reply to a message to save it as a quote |
| `!pull @user` | Pull a random message from a user in the current channel |
| `!pull @user #channel` | Pull a random message from a user in a specific channel |
| `/pull @user` | Slash version — pull from a user |
| `!pullid <user_id>` | Pull a random message by user ID (works for users who left) |
| `!pullid <user_id> #channel` | Pull by user ID from a specific channel |
| `!pullmsg <message_id>` | Save a specific message by its ID |
| `!pullmsg <message_id> #channel` | Save a specific message from a specific channel |

---

## 📖 Quoteboard — Viewing

| Command | Description |
|---------|-------------|
| `!quote` | Post a random saved quote |
| `/quote` | Slash version of `!quote` |
| `!randomquote @user` | Post a random saved quote from a specific user |
| `!quoteleaderboard` | Show top 5 most quoted users |
| `!quotecount` | Show how many times you've been quoted |
| `!quotecount @user` | Show how many times a specific user has been quoted |
| `!quoteboardstats` | Show total quotes, top quoted users, and last quote saved |

---

## 🛠️ Quoteboard — Management
> Admin only

| Command | Description |
|---------|-------------|
| `!deletequote <message_id>` | Delete a specific quote from the quoteboard |
| `!resetquotes` | Clear the saved quote ID list *(native button confirmation)* |
| `!exportquotes` | DM you a text file of all saved quotes |

---

## 👤 Pinned Users
> Admin only

| Command | Description |
|---------|-------------|
| `!pinuser @user` | Track a user's messages everywhere in real time |
| `!pinuser @user #channel` | Track a user only in a specific channel |
| `/pinuser @user` | Slash version |
| `!unpinuser @user` | Stop tracking a user |
| `!unpinuser @user #channel` | Stop tracking a user in a specific channel |
| `!pinnedusers` | Show all currently pinned users |
| `/pinnedusers` | Slash version |

---

## 🔒 Lockdown
> Requires Manage Channels permission

| Command | Description |
|---------|-------------|
| `!lockdown channel` | Lock the current channel |
| `!lockdown channel 10m` | Lock current channel and auto-unlock after duration |
| `!lockdown user @user` | Timeout a specific user (1h default) |
| `!lockdown user @user 30m` | Timeout a user for a specific duration |
| `!lockdown role @role` | Timeout everyone with a specific role |
| `!lockdown role @role 1h` | Timeout role members for a specific duration |
| `!lockdown server` | Lock the entire server *(native button confirmation)* |
| `!unlock channel` | Unlock the current channel |
| `!unlock user @user` | Remove timeout from a specific user |
| `!unlock role @role` | Remove timeout from everyone with a specific role |
| `!unlock server` | Unlock the entire server *(native button confirmation)* |
| `/lockdown <target>` | Full slash version with dropdown for target type |
| `/unlock <target>` | Full slash version with dropdown for target type |

**Duration formats:** `10m` = 10 minutes · `1h` = 1 hour · `30s` = 30 seconds

> **Note:** User and role lockdowns now use Discord's native **Timeout** feature — no Muted role required.

---

## 📊 Stats & Admin

| Command | Description |
|---------|-------------|
| `!ping` | Show bot latency and uptime |
| `!auditlog` | Show last 20 bot actions in this server |
| `!auditlog 50` | Show last N actions (max 50) |
| `!help` | Show all commands organized by category |

---

## 🎉 Fun

| Command | Description |
|---------|-------------|
| `!poll "Question?" "Option 1" "Option 2" [duration]` | Create a native Discord poll (up to 10 options) |
| `/poll` | Full slash version with individual fields for each option |

**Poll duration formats:** `1d` = 1 day · `12h` = 12 hours · `30m` = 30 minutes (default: 1d)

---

## 🔐 Security
> Owner only

| Command | Description |
|---------|-------------|
| `!allowserver` | Add current server to the allowlist |
| `!allowserver <guild_id>` | Add a specific server to the allowlist |
| `!denyserver <guild_id>` | Remove a server from the allowlist |
| `!allowlist` | Show all allowlisted servers |

---

## 🤖 Auto Features

| Feature | Behavior |
|---------|----------|
| **Auto quote feed** | Every X minutes (set with `!setquotestream`), posts a random saved quote to the echo feed channel. Prioritizes pinned users' quotes first. |
| **Real-time user tracking** | When a pinned user sends a message in a watched channel, it's auto-saved to the quoteboard AND posted to the echo feed instantly. |
| **Quote of the Day** | Posts one random quote every 24 hours to the QOTD channel (set with `!setqotd`). |
| **Anti-spam** | Auto-applies a native Discord timeout to users who exceed the message threshold. Logs to log channel and DMs bot owner. Falls back to Muted role if timeout permission is unavailable. |
| **Server join/leave alerts** | Bot owner gets a DM when the bot joins or is removed from a server. |
| **Rate limit alerts** | Bot owner gets a DM when a user is hammering commands. |
| **Permission bypass alerts** | Bot owner gets a DM when someone tries to use a command they don't have access to. |
| **Lockdown abuse alerts** | Bot owner gets a DM if `!lockdown server` is triggered by multiple users within 5 minutes. |

---

## 🌐 Slash Commands Summary

| Command | Description |
|---------|-------------|
| `/setup` | Open bot setup form (modal) |
| `/status` | Show bot config (ephemeral) |
| `/quote` | Post a random saved quote |
| `/pull @user` | Pull a random message from a user |
| `/pull @user #channel` | Pull from a specific channel |
| `/pinuser @user` | Pin a user for real-time tracking |
| `/pinuser @user #channel` | Pin in a specific channel |
| `/pinnedusers` | Show all pinned users |
| `/lockdown <target>` | Lock with dropdown selection |
| `/unlock <target>` | Unlock with dropdown selection |
| `/poll` | Create a native Discord poll |

---

## 📝 Notes

- Config is stored in SQLite (`bot.db`) — persists across Railway redeploys when a volume is mounted at `/app`.
- `!pullid` and `!pullmsg` work for users who have left the server.
- `!lockdown server` and `!unlock server` use native Discord **buttons** for confirmation — no typing required.
- `!setup` opens a native Discord **modal form** — fill in channel IDs (right-click channel → Copy Channel ID).
- Polls use Discord's native poll system — results are tracked by Discord natively.
- User/role lockdowns use Discord's native **Timeout** — no Muted role needed.
- Welcome message supports `{user}` and `{server}` placeholders.
- Rate limits reset on bot restart.
- Anti-spam timeout duration is configurable via `!setspam <threshold> <window> <timeout_minutes>`.
