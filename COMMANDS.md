# Lamarque Bot — Command Reference

---

## Quoteboard Setup
> Admin only

| Command | Description |
|--------|-------------|
| `!setquoteboard #channel` | Set where quotes get saved |
| `!setechofeed #channel` | Set where auto quotes get posted |
| `!setquoterole @role` | Restrict who can save/pull quotes |
| `!setquotestream <minutes>` | Set how often auto quotes fire |
| `!quotestop` | Stop the auto quote feed |
| `!quotestart` | Start the auto quote feed |

---

## Saving Quotes

| Command | Description |
|--------|-------------|
| `!savequote` | Reply to a message to save it as a quote |
| `!pull @user` | Pull a random message from a user in the current channel |
| `!pull @user #channel` | Pull a random message from a user in a specific channel |
| `!pullid <user_id>` | Pull a random message by user ID (works for users who left) |
| `!pullid <user_id> #channel` | Pull by user ID from a specific channel |
| `!pullmsg <message_id>` | Save a specific message by its ID |
| `!pullmsg <message_id> #channel` | Save a specific message from a specific channel |

---

## Viewing Quotes

| Command | Description |
|--------|-------------|
| `!quote` | Post a random saved quote |
| `!randomquote @user` | Post a random saved quote from a specific user |

---

## Quote Stats

| Command | Description |
|--------|-------------|
| `!quotecount` | Show how many times you've been quoted |
| `!quotecount @user` | Show how many times a specific user has been quoted |

---

## Pinned Users
> Admin only

| Command | Description |
|--------|-------------|
| `!pinuser @user` | Track a user's messages everywhere in real time |
| `!pinuser @user #channel` | Track a user only in a specific channel |
| `!unpinuser @user` | Stop tracking a user |
| `!unpinuser @user #channel` | Stop tracking a user in a specific channel |
| `!pinnedusers` | Show all currently pinned users |

---

## Lockdown
> Requires Manage Channels permission

| Command | Description |
|--------|-------------|
| `!lockdown channel` | Lock the current channel |
| `!lockdown user @user` | Mute a specific user |
| `!lockdown role @role` | Mute everyone with a specific role |
| `!lockdown server` | Lock the entire server |
| `!unlock channel` | Unlock the current channel |
| `!unlock user @user` | Unmute a specific user |
| `!unlock role @role` | Unmute everyone with a specific role |
| `!unlock server` | Unlock the entire server |

---

## Slash Commands
> Available via `/` in Discord

| Command | Description |
|--------|-------------|
| `/quote` | Post a random saved quote |
| `/pull @user` | Pull a random message from a user |
| `/pull @user #channel` | Pull from a specific channel |
| `/pinuser @user` | Pin a user for real-time tracking |
| `/pinuser @user #channel` | Pin a user in a specific channel |
| `/pinnedusers` | Show all pinned users |
| `/lockdown <target>` | Lock a channel/user/role/server |
| `/unlock <target>` | Unlock a channel/user/role/server |

---

## Auto Features

| Feature | Description |
|--------|-------------|
| **Auto quote feed** | Every X minutes (set with `!setquotestream`), posts a random saved quote to the echo feed channel. Prioritizes pinned users' quotes first. |
| **Real-time tracking** | When a pinned user sends a message in a watched channel, it's automatically saved to the quoteboard AND posted to the echo feed instantly. |

---

## Notes
- `config.json` stores all channel/role settings. Re-run setup commands after each Railway redeploy.
- `!pullid` and `!pullmsg` work even for users who have left the server.
- The Muted role must be below the bot's role in the server role hierarchy for lockdown to work.
