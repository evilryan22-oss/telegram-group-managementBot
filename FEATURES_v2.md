# v2 Feature Additions

## Fun
- `/joke` – 110+ jokes
- `/riddle` – 100+ riddles with hidden-spoiler answers
- `/puzzle` – brain teasers
- `/truth`, `/dare`, `/tod` (a.k.a. `/truthordare`) – 100 prompts each
- `/quiz` – random trivia delivered as a native Telegram quiz poll (100+ questions)
- `/weather <city>` – live weather via wttr.in (no API key required)
- `/ttt [bot]` – Tic-Tac-Toe with inline-keyboard board, 2-player or vs bot AI

## Sticker-style reactions (reply to a user or pass @username)
`/hug /kiss /slap /kill /cry /smile /run /laugh /punch /bite /poke /pat /wave /dance /wink /highfive /shoot /yawn /shrug /facepalm`

## Group control (admins)
- `/promote` – grant admin to replied/targeted user
- `/demote` – revoke admin
- `/lock` / `/lockgroup` – mute the whole group (only admins can speak)
- `/unlock` / `/unlockgroup` – restore default speaking permissions
- `/antilink on|off` – auto-delete any message containing a URL or t.me invite (admins exempt)
- `/tagadmins` (alias `/admins`) – ping all human admins of the chat

## Direct-message brain
- The bot now holds real DM conversations: greetings, thanks, "how are you", "who are you", "what time is it", help, love, etc.
- **Insult-back**: in DMs the bot always claps back at insults; in groups it only fires when @mentioned or directly replied to.

## Storage
A new `chat_flags` table backs per-chat toggles (antilink today, extensible later). Existing tables are unchanged.
