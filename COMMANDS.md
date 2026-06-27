# Lamarque Bot — Command Reference

> **Prefix:** `!` | **Slash commands:** available via `/` for most commands

---

## 🔧 Setup & Config
> Admin only

| Command | Description |
|---------|-------------|
| `!setup` | Guided setup flow — configure all channels and settings in one session |
| `!status` | Show current bot config in one embed (channels, interval, pinned users, quote count) |
| `!setquoteboard #channel` | Set where quotes get saved |
| `!setechofeed #channel` | Set where auto quotes get posted |
| `!setquoterole @role` | Restrict who can save/pull quotes (admins always bypass) |
| `!setquotestream <minutes>` | Set how often auto quotes fire |
| `!quotestop` | Stop the auto quote feed |
| `!quotestart` | Start the auto quote feed |
| `!setwelcome #channel [message]` | Set welcome channel and optional custom message |
| `!setqotd #channel` | Set channel for daily Quote of the Day |
| `!setspam <threshold> <window>` | Set anti-spam threshold (e.g. `!setspam 5 5` = 5 msgs in 5s) |

---

## 📌 Quoteboard — Saving
> Requires quote role if set, otherwise open to everyone

| Command | Description |
|---------|-------------|
| `!savequote` | Reply to a message to save it as a quote |
| `!pull @user` | Pull a random message from a user in the current channel |
| `!pull @user #channel` | Pull a random message from a user in a specific channel |
| `!pullid <user_id>` | Pull a random message by user ID (works for users who left) |
| `!pullid <user_id> #channel` | Pull by user ID from a specific channel |
| `!pullmsg <message_id>` | Save a specific message by its ID |
| `!pullmsg <message_id> #channel` | Save a specific message from a specific channel |

---

## 📖 Quoteboard — Viewing

| Command | Description |
|---------|-------------|
| `!quote` | Post a random saved quote |
| `!randomquote @user` | Post a random saved quote from a specific user |
| `!quoteleaderboard` | Show top 5 most quoted users |
| `!quotecount` | Show how many times you've been quoted |
| `!quotecount @user` | Show how many times a specific user has been quoted |
| `!quoteboardstats` | Show total quotes, most quoted user, and last quote saved |

---

## 🛠️ Quoteboard — Management
> Admin only

| Command | Description |
|---------|-------------|
| `!deletequote <message_id>` | Delete a specific quote from the quoteboard |
| `!resetquotes` | Clear the saved quote ID list (with confirmation prompt) |
| `!exportquotes` | DM you a text file of all saved quotes |
| `!quoteoftheday` | Manually trigger a quote of the day post |

---

## 👤 Pinned Users
> Admin only

| Command | Description |
|---------|-------------|
| `!pinuser @user` | Track a user's messages everywhere in real time |
| `!pinuser @user #channel` | Track a user only in a specific channel |
| `!unpinuser @user` | Stop tracking a user |
| `!unpinuser @user #channel` | Stop tracking a user in a specific channel |
| `!pinnedusers` | Show all currently pinned users |

---

## 🔒 Lockdown
> Requires Manage Channels permission

| Command | Description |
|---------|-------------|
| `!lockdown channel` | Lock the current channel |
| `!lockdown channel 10m` | Lock current channel and auto-unlock after duration |
| `!lockdown user @user` | Mute a specific user |
| `!lockdown user @user 30m` | Mute a user and auto-unmute after duration |
| `!lockdown role @role` | Mute everyone with a specific role |
| `!lockdown server` | Lock the entire server *(requires confirmation)* |
| `!unlock channel` | Unlock the current channel |
| `!unlock user @user` | Unmute a specific user |
| `!unlock role @role` | Unmute everyone with a specific role |
| `!unlock server` | Unlock the entire server *(requires confirmation)* |

**Duration formats:** `10m` = 10 minutes, `1h` = 1 hour, `30s` = 30 seconds

---

## 📊 Stats & Admin

| Command | Description |
|---------|-------------|
| `!ping` | Show bot latency and uptime |
| `!auditlog` | Show last 20 bot actions in this server |
| `!auditlog 50` | Show last N actions (max 50) |

---

## 🎉 Fun

| Command | Description |
|---------|-------------|
| `!poll "Question?" "Option 1" "Option 2"` | Create a poll with up to 10 options |

---

## 🔐 Security (Owner Only)

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
| **Anti-spam** | Auto-mutes users who exceed the message threshold. Logs to log channel and DMs bot owner. |
| **Server join/leave alerts** | Bot owner gets a DM when the bot joins or is removed from a server. |
| **Rate limit alerts** | Bot owner gets a DM when a user is hammering commands. |
| **Permission bypass alerts** | Bot owner gets a DM when someone tries to use a command they don't have access to. |
| **Lockdown abuse alerts** | Bot owner gets a DM if `!lockdown server` is triggered by multiple users within 5 minutes. |

---

## 🌐 Slash Commands
> Available via `/` in Discord

| Command | Description |
|---------|-------------|
| `/quote` | Post a random saved quote |
| `/pull @user` | Pull a random message from a user |
| `/pull @user #channel` | Pull from a specific channel |
| `/pinuser @user` | Pin a user for real-time tracking |
| `/pinuser @user #channel` | Pin a user in a specific channel |
| `/pinnedusers` | Show all pinned users |
| `/lockdown <target>` | Lock a channel/user/role/server |
| `/unlock <target>` | Unlock a channel/user/role/server |

---

## 📝 Notes

- Config is stored in SQLite (`bot.db`) and persists across Railway redeploys when a volume is mounted at `/app`.
- `!pullid` and `!pullmsg` work even for users who have left the server.
- The Muted role must be **below** the bot's role in the server role hierarchy for lockdown to work on users/roles.
- `!lockdown server` and `!unlock server` require typing `confirm` before executing.
- Welcome message supports `{user}` and `{server}` placeholders.
- Rate limits reset on bot restart.
