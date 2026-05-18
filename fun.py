"""Fun commands: jokes, riddles, truth or dare, sticker-style reactions, puzzles."""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Dict, List, Tuple

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.helpers import mention_html, safe_call, safe_html

log = logging.getLogger(__name__)

# ---------------- JOKES (100+) ----------------
JOKES: List[str] = [
    "Why don't scientists trust atoms? Because they make up everything.",
    "I told my computer I needed a break — it said: 'No problem, I'll go to sleep.'",
    "Why did the developer go broke? He used up all his cache.",
    "There are 10 kinds of people: those who understand binary and those who don't.",
    "Debugging: being the detective in a crime movie where you are also the murderer.",
    "Why do programmers prefer dark mode? Light attracts bugs.",
    "I would tell you a UDP joke, but you might not get it.",
    "A SQL query walks into a bar, sees two tables and asks: 'May I join you?'",
    "Why was the JavaScript developer sad? Because he didn't know how to 'null' his feelings.",
    "How many programmers does it take to change a light bulb? None — that's a hardware problem.",
    "I'd tell you a joke about an empty array, but there's nothing in it.",
    "Why did the function break up with the variable? Too many arguments.",
    "What's a programmer's favorite hangout? The Foo Bar.",
    "Why do Java developers wear glasses? Because they don't C#.",
    "Real programmers count from 0.",
    "There are two hard things in computer science: cache invalidation and naming things.",
    "Why did the developer quit his job? He didn't get arrays.",
    "Knock knock. — Who's there? — Very long pause… Java.",
    "I changed my password to 'incorrect' so when I forget, the computer tells me.",
    "Algorithm: word used by programmers when they don't want to explain what they did.",
    "Why was the math book sad? It had too many problems.",
    "Parallel lines have so much in common — it's a shame they'll never meet.",
    "I'm reading a book about anti-gravity. It's impossible to put down.",
    "Did you hear about the claustrophobic astronaut? He just needed a little space.",
    "I used to play piano by ear, now I use my hands.",
    "I'm on a seafood diet. I see food and I eat it.",
    "Why don't skeletons fight each other? They don't have the guts.",
    "What do you call cheese that isn't yours? Nacho cheese.",
    "What did the ocean say to the shore? Nothing, it just waved.",
    "Why did the scarecrow win an award? He was outstanding in his field.",
    "I'd tell you a chemistry joke, but I know I wouldn't get a reaction.",
    "Time flies like an arrow. Fruit flies like a banana.",
    "What do you call fake spaghetti? An impasta.",
    "Why did the bicycle fall over? It was two-tired.",
    "I'm terrified of elevators, so I take steps to avoid them.",
    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    "Why did the coffee file a police report? It got mugged.",
    "What's orange and sounds like a parrot? A carrot.",
    "I asked the librarian if the library had books on paranoia. She whispered, 'They're right behind you.'",
    "I only know 25 letters of the alphabet. I don't know y.",
    "I'm reading a book about mazes. I got lost in it.",
    "I wasn't originally going to get a brain transplant, but then I changed my mind.",
    "Why don't oysters share their pearls? Because they're shellfish.",
    "I have a joke about construction, but I'm still working on it.",
    "I have a joke about time travel, but you didn't like it.",
    "What do you call a fish wearing a crown? Your royal halibut.",
    "Why did the cookie cry? Because his mom was a wafer too long.",
    "What did the buffalo say when his son left? Bison.",
    "I once got fired from a calendar factory. All I did was take a day off.",
    "Two atoms are walking down the street. One says, 'I think I lost an electron.' The other asks, 'Are you sure?' 'Yes, I'm positive.'",
    "Why did the tomato turn red? It saw the salad dressing.",
    "How does a penguin build its house? Igloos it together.",
    "I bought shoes from a drug dealer. Don't know what he laced them with, but I was tripping all day.",
    "Why did the man put his money in the freezer? He wanted cold hard cash.",
    "Why couldn't the bicycle stand by itself? It was two tired.",
    "What did one wall say to the other? I'll meet you at the corner.",
    "Why don't scientists trust stairs? They're always up to something.",
    "Why are elevator jokes so funny? They work on so many levels.",
    "I tried to catch fog yesterday. Mist.",
    "Why did the golfer wear two pairs of pants? In case he got a hole in one.",
    "I used to be addicted to soap, but I'm clean now.",
    "Why did the picture go to jail? It was framed.",
    "What's brown and sticky? A stick.",
    "What's the best thing about Switzerland? I don't know, but the flag is a big plus.",
    "I told a chemistry joke. There was no reaction.",
    "I'm friends with 25 letters of the alphabet. I don't know y.",
    "I gave all my dead batteries away today. Free of charge.",
    "Why don't eggs tell jokes? They'd crack each other up.",
    "Want to hear a joke about paper? Never mind — it's tearable.",
    "I'm reading a horror book in braille. Something bad is about to happen, I can feel it.",
    "Why are frogs so happy? They eat whatever bugs them.",
    "What did the grape do when it got stepped on? Nothing — it just let out a little wine.",
    "Did you hear about the Italian chef who died? He pasta way.",
    "Why was the broom late? It over-swept.",
    "I tried to write a pun about wind, but it blew.",
    "What did one hat say to the other? You stay here, I'll go on ahead.",
    "I'm not a fan of stairs. They're always up to something.",
    "Why did the cookie go to the doctor? It was feeling crummy.",
    "I told my dog a joke about tails. He thought it was wagical.",
    "Why was Cinderella bad at football? Her coach was a pumpkin.",
    "Why do bees have sticky hair? Because they use honeycombs.",
    "Why couldn't the leopard play hide and seek? He was always spotted.",
    "Why are ghosts bad liars? You can see right through them.",
    "I told my suitcase there'd be no vacation this year. Now I'm dealing with emotional baggage.",
    "I lost my mood ring and I don't know how to feel about it.",
    "I bought the world's worst thesaurus. Not only is it terrible, it's also terrible.",
    "I asked my dog what's two minus two. He said nothing.",
    "Why did the math teacher break up with the science teacher? They had no chemistry and lots of problems.",
    "What do you call a snowman with a six-pack? An abdominal snowman.",
    "Why don't crabs share? They're shellfish.",
    "I named my horse Mayo. Sometimes Mayo neighs.",
    "What's a vampire's favorite fruit? A neck-tarine.",
    "What do you call a bear with no teeth? A gummy bear.",
    "Why do seagulls fly over the sea? Because if they flew over the bay they'd be bagels.",
    "What did the zero say to the eight? Nice belt.",
    "What did the left eye say to the right eye? Between us, something smells.",
    "I'm reading a book on the history of glue. I just can't seem to put it down.",
    "Why did the developer go to therapy? Too many issues unresolved.",
    "I have a stepladder because my real ladder left when I was a kid.",
    "What's the difference between a hippo and a Zippo? One is really heavy, the other is a little lighter.",
    "What kind of music do mummies listen to? Wrap.",
    "What do you call a sleeping bull? A bulldozer.",
    "I tried to sue the airline for losing my luggage. I lost my case.",
    "How do you organize a space party? You planet.",
    "Why did the stadium get hot after the game? All the fans left.",
    "What did the ocean say to the boat? Nothing, it just waved.",
    "I have a fear of speed bumps. I'm slowly getting over it.",
    "I'm reading a book about teleportation. It's bound to take me places.",
    "Why don't programmers like nature? Too many bugs.",
    "Why was the equal sign humble? It knew it wasn't less than or greater than anyone else.",
]

# ---------------- RIDDLES (100) ----------------
RIDDLES: List[Tuple[str, str]] = [
    ("I speak without a mouth and hear without ears. I have nobody, but I come alive with wind. What am I?", "An echo"),
    ("The more of me you take, the more you leave behind. What am I?", "Footsteps"),
    ("What has keys but can't open locks?", "A piano"),
    ("What has hands but cannot clap?", "A clock"),
    ("What gets wetter the more it dries?", "A towel"),
    ("I have cities, but no houses; mountains, but no trees; water, but no fish. What am I?", "A map"),
    ("What can travel around the world while staying in the corner?", "A stamp"),
    ("The more you take, the more you leave behind. What are they?", "Footsteps"),
    ("What has a head and a tail but no body?", "A coin"),
    ("What has to be broken before you can use it?", "An egg"),
    ("I'm tall when I'm young and short when I'm old. What am I?", "A candle"),
    ("What month of the year has 28 days?", "All of them"),
    ("What is full of holes but still holds water?", "A sponge"),
    ("What goes up but never comes down?", "Your age"),
    ("If two's company, and three's a crowd, what are four and five?", "Nine"),
    ("What has many teeth but cannot bite?", "A comb"),
    ("What word becomes shorter when you add two letters to it?", "Short"),
    ("I have branches, but no fruit, trunk or leaves. What am I?", "A bank"),
    ("What invention lets you look right through a wall?", "A window"),
    ("What can you catch but not throw?", "A cold"),
    ("What kind of band never plays music?", "A rubber band"),
    ("What has one eye but cannot see?", "A needle"),
    ("What can fill a room but takes up no space?", "Light"),
    ("Where does today come before yesterday?", "In the dictionary"),
    ("What goes through cities and fields but never moves?", "A road"),
    ("I'm light as a feather, yet the strongest man can't hold me for five minutes. What am I?", "Breath"),
    ("What has a neck but no head?", "A bottle"),
    ("What runs but never walks, has a mouth but never talks?", "A river"),
    ("What can you keep after giving to someone?", "Your word"),
    ("What has legs but doesn't walk?", "A table"),
    ("What's black and white and read all over?", "A newspaper"),
    ("I have lakes with no water, mountains with no stone, and cities with no buildings. What am I?", "A map"),
    ("What has many keys but can't open a single lock?", "A keyboard"),
    ("Forward I'm heavy, backward I'm not. What am I?", "The word ton"),
    ("What gets bigger when more is taken away?", "A hole"),
    ("I am an odd number; take away a letter and I become even. What am I?", "Seven"),
    ("What has 13 hearts, but no other organs?", "A deck of cards"),
    ("What word contains 26 letters but only has three syllables?", "Alphabet"),
    ("What can be cracked, made, told and played?", "A joke"),
    ("What has a thumb and four fingers but is not alive?", "A glove"),
    ("What kind of room has no doors or windows?", "A mushroom"),
    ("I am taken from a mine and shut up in a wooden case from which I am never released. What am I?", "Pencil lead"),
    ("What's always in front of you but can't be seen?", "The future"),
    ("There's a one-story house where everything is yellow. What color are the stairs?", "There are no stairs — it's one story"),
    ("How many letters are in 'the alphabet'?", "Eleven"),
    ("If you drop me I'm sure to crack, but give me a smile and I'll always smile back. What am I?", "A mirror"),
    ("What occurs once in a minute, twice in a moment and never in a thousand years?", "The letter M"),
    ("What has roots that nobody sees, is taller than trees, up it goes and yet never grows?", "A mountain"),
    ("I have keys but no locks. I have space but no room. You can enter but can't go inside. What am I?", "A keyboard"),
    ("What can run but never walks, has a bed but never sleeps?", "A river"),
    ("Take off my skin — I won't cry, but you will. What am I?", "An onion"),
    ("What 5-letter word becomes shorter when you add two letters?", "Short(er)"),
    ("Which word in the dictionary is spelled incorrectly?", "Incorrectly"),
    ("What has 88 keys but can't open a single door?", "A piano"),
    ("Two fathers and two sons go fishing, each catches one fish. They bring home three. How?", "Grandfather, father, son"),
    ("I have hands but no arms, a face but no eyes. What am I?", "A clock"),
    ("What word looks the same upside down and backwards?", "SWIMS"),
    ("What gets sharper the more you use it?", "Your brain"),
    ("Mary's father has five daughters: Nana, Nene, Nini, Nono. What's the fifth's name?", "Mary"),
    ("What has four wheels and flies?", "A garbage truck"),
    ("What begins with T, ends with T, and has T in it?", "A teapot"),
    ("What is at the end of a rainbow?", "The letter W"),
    ("I follow you all the time and copy your every move, but you can't touch me or catch me. What am I?", "Your shadow"),
    ("What goes up and down but doesn't move?", "Stairs"),
    ("If you have me, you want to share me. If you share me, you don't have me. What am I?", "A secret"),
    ("What has cities but no houses, forests but no trees, and rivers without water?", "A map"),
    ("Poor people have it. Rich people need it. If you eat it, you die. What is it?", "Nothing"),
    ("The more you have of it, the less you see. What is it?", "Darkness"),
    ("What can you hold without ever touching?", "Your breath"),
    ("What kind of coat is best put on wet?", "A coat of paint"),
    ("What has 21 spots but isn't always visible?", "A dice"),
    ("Throw me out of the window, you'll leave a grieving wife. Throw me out of a door, you'll start a wonderful life. What am I?", "The letter N"),
    ("What never asks questions but is often answered?", "A doorbell"),
    ("What can be heard and caught, but never seen?", "A remark"),
    ("What goes around the world but stays in a corner?", "A stamp"),
    ("What kind of tree can you carry in your hand?", "A palm"),
    ("If I drink, I die. If I eat, I'm fine. What am I?", "Fire"),
    ("I have a heart that doesn't beat. What am I?", "An artichoke"),
    ("What word starts with E, ends with E, and contains only one letter?", "Envelope"),
    ("What is so fragile that saying its name breaks it?", "Silence"),
    ("People buy me to eat but never eat me. What am I?", "A plate"),
    ("I have one head, one foot and four legs. What am I?", "A bed"),
    ("I can be long or short. I can be grown or bought. I can be painted or left bare. What am I?", "Fingernails"),
    ("Two in a corner, one in a room, zero in a house, but one in a shelter. What am I?", "The letter R"),
    ("I have branches, but no leaves, no trunk, and no fruit. What am I?", "A bank"),
    ("What goes up when the rain comes down?", "An umbrella"),
    ("What can you break, even if you never pick it up?", "A promise"),
    ("What disappears as soon as you say its name?", "Silence"),
    ("What does this say: YYUR YYUB ICUR YY4ME?", "Too wise you are, too wise you be, I see you are, too wise for me"),
    ("Three doctors said Robert was their brother. Robert said he had no brothers. Who lied?", "Nobody — the doctors are his sisters"),
    ("A man rode in on Friday, stayed three days, and rode out on Friday. How?", "His horse is named Friday"),
    ("I am odd. Remove a letter and I become even. What am I?", "Seven"),
    ("What does a cloud wear under his raincoat?", "Thunderwear"),
    ("What kind of cup doesn't hold water?", "A cupcake"),
    ("What is brown, hairy and wears sunglasses?", "A coconut on vacation"),
    ("How can a leopard change its spots?", "By moving"),
    ("What grows up while growing down?", "A goose"),
    ("I'm full of holes but I hold a lot of weight. What am I?", "A net"),
    ("What has a bottom at the top?", "Your legs"),
    ("I can be cracked, I can be made, I can be told, I can be played. What am I?", "A joke"),
    ("If you're running in a race and pass the person in second place, what place are you in?", "Second"),
    ("What can travel the world without leaving its corner?", "A stamp"),
]

# ---------------- TRUTH OR DARE (100 each) ----------------
TRUTHS: List[str] = [
    "What's the most embarrassing thing you've ever done?",
    "What's a secret you've never told your best friend?",
    "What's the biggest lie you ever told?",
    "Have you ever cheated on a test?",
    "What's your biggest fear?",
    "Who was your first crush?",
    "What's the most childish thing you still do?",
    "What's the worst gift you've ever received?",
    "Have you ever pretended to be sick to skip something?",
    "What's the weirdest dream you've ever had?",
    "What's the longest you've gone without a shower?",
    "What's a habit you have that you're not proud of?",
    "Have you ever stolen anything?",
    "What's the most embarrassing song on your playlist?",
    "Who do you secretly admire in this group?",
    "What's the strangest food combo you actually enjoy?",
    "What was your worst haircut?",
    "Have you ever lied to your parents about where you were?",
    "What's the most awkward date you've been on?",
    "What's something you wish you were better at?",
    "What's a fashion trend you don't understand?",
    "Have you ever ghosted someone?",
    "What's the silliest thing you've cried over?",
    "What's the most embarrassing thing in your search history?",
    "Have you ever fallen in public?",
    "What's the longest you've stayed awake?",
    "What's a movie that always makes you cry?",
    "What's the dumbest argument you've had?",
    "What's the weirdest thing you've Googled?",
    "Have you ever sent a text to the wrong person?",
    "What's your guilty pleasure show?",
    "Who is your celebrity crush?",
    "What was your most cringey social-media post?",
    "Have you ever lied to get out of a hangout?",
    "What's a compliment you can't accept gracefully?",
    "What's an irrational fear of yours?",
    "What's the most useless talent you have?",
    "Have you ever talked badly about a friend behind their back?",
    "What's your most-used emoji and why?",
    "What's the most embarrassing nickname you've been called?",
    "Have you ever re-gifted a present?",
    "What's something you're glad your parents don't know?",
    "Who was the last person you stalked online?",
    "What's the longest you've held a grudge?",
    "Have you ever copied someone's homework?",
    "What's the rudest thing you've ever done?",
    "What's a song you secretly love but pretend to hate?",
    "Have you ever lied about your age?",
    "What's the worst thing you've said in anger?",
    "Have you ever had a crush on a friend's partner?",
    "What's your worst kitchen disaster?",
    "What's a small thing that always cheers you up?",
    "Have you ever pretended to know something you didn't?",
    "What's the strangest place you've fallen asleep?",
    "What's something you do when nobody's watching?",
    "Have you ever broken something and blamed someone else?",
    "What's your most embarrassing childhood memory?",
    "Who is the most annoying person you know?",
    "What's something you'd never want your parents to see?",
    "Have you ever forgotten a friend's birthday?",
    "What's a rumor you started?",
    "What's the most ridiculous thing you've cried about as an adult?",
    "Have you ever been jealous of a friend?",
    "What's your worst public speaking moment?",
    "What's something you're embarrassed about your family?",
    "Have you ever pretended to like a gift?",
    "What's a secret skill you have?",
    "What's the most petty reason you've stopped talking to someone?",
    "Have you ever sent a screenshot to the wrong group?",
    "What's a food everyone loves that you secretly hate?",
    "What's the worst thing you've done at school?",
    "Have you ever lied in this game?",
    "What's something you do to look smart?",
    "What's an opinion you'd never share online?",
    "Have you ever cried at work or school?",
    "What's your weirdest fear about the future?",
    "What's a TV show you've finished in less than 48 hours?",
    "Who was the last person you blocked and why?",
    "What's your weirdest dating story?",
    "Have you ever crushed on a teacher?",
    "What's the longest you've kept a phone on 1%?",
    "What's something you'd never admit while sober?",
    "What's the messiest your room has ever been?",
    "Have you ever pretended to be busy to avoid plans?",
    "What's a moment that still makes you cringe?",
    "What's the cheapest gift you've ever given?",
    "What's something you'd change about yourself if you could?",
    "Have you ever lied during a job interview?",
    "What's a secret talent of a close friend?",
    "What's the meanest prank you've pulled?",
    "Have you ever read someone's diary or journal?",
    "What's the most embarrassing thing you've worn in public?",
    "What's a moment you wish you handled differently?",
    "Have you ever pretended a gift was new?",
    "What's the worst grade you've ever gotten?",
    "What's a weird thing you've eaten?",
    "Have you ever lied to a doctor?",
    "What's the cringiest thing in your camera roll?",
    "Have you ever liked a really old photo by accident?",
    "What's a habit of yours that annoys your family?",
    "Have you ever been kicked out of somewhere?",
    "What's the wildest dream you remember vividly?",
]

DARES: List[str] = [
    "Send the last selfie in your gallery.",
    "Speak in an accent for the next 10 minutes.",
    "Send a voice note singing the chorus of any song.",
    "Change your profile picture to whatever the group picks for 1 hour.",
    "Text your crush a single emoji.",
    "Send the last screenshot you took.",
    "Do 10 push-ups and send a video.",
    "Send a message in all caps for the next 5 minutes.",
    "DM a compliment to the last person who messaged you.",
    "Tell a really bad joke and send it as a voice note.",
    "Eat a spoonful of something spicy and react on camera.",
    "Send a photo making the silliest face you can.",
    "Change your status to 'I love bananas' for 24 hours.",
    "Send the third photo in your gallery.",
    "Record yourself doing your best dance move.",
    "Tell us your most-used password (the structure, not the actual one).",
    "Speak only in questions for the next 5 messages.",
    "Send the last emoji you used + use it 10 times.",
    "Send a screenshot of your home screen.",
    "Sing happy birthday to your phone in a voice note.",
    "Talk like a pirate for the next 5 minutes.",
    "Send a baby photo of yourself.",
    "Imitate any animal in a voice note.",
    "Text 'I miss you' to the 7th contact in your list.",
    "Send the funniest meme in your gallery.",
    "Do your best impression of a teacher / boss.",
    "Send a poem you write in 60 seconds.",
    "Change your bio to a quote of the group's choice for an hour.",
    "Send the last YouTube video you watched.",
    "Try to lick your elbow and send a photo.",
    "Send your last 3 searches.",
    "Sing a children's song in a voice note.",
    "Set your ringtone to a meme sound for the day.",
    "Send a video of you doing your best runway walk.",
    "Tell a 60-second story with no preparation.",
    "Try to do a tongue twister 3 times fast on voice note.",
    "Send a screenshot of your most-used app.",
    "Wear socks on your hands for the rest of the chat.",
    "Send a picture of your fridge interior.",
    "Compose a haiku about the person to your right (in the chat).",
    "Do 20 jumping jacks and send proof.",
    "Send a voice note imitating a celebrity.",
    "Make up a song about cheese, 30 seconds.",
    "Send the contact name of the last person you texted.",
    "Send a photo of your workspace right now.",
    "Pick a random group member and write them a love letter.",
    "Take a sip of water with no hands.",
    "Send a sentence using only emojis to describe your day.",
    "Try to balance a spoon on your nose; send video.",
    "Make up a fake news headline.",
    "Send the last book you read or want to read.",
    "Wear something on your head for the next hour and send a pic.",
    "Send a screenshot of your battery + brightness.",
    "Try to whistle a popular song; voice note.",
    "Send the longest word you can spell without Google.",
    "Tell the group your most overused phrase.",
    "Send a tongue-out selfie.",
    "Sing the alphabet backwards.",
    "Send a photo of your shoes right now.",
    "Imitate the last person who spoke in the group.",
    "Send the last 3 photos you posted online.",
    "Compose a poem using everyone's first letter of their name.",
    "Type the next message with your nose.",
    "Send a 5-second video of your view right now.",
    "Hum a song; group has to guess.",
    "Send the funniest video in your gallery.",
    "Reveal your dream job at 8 years old.",
    "Send a heartfelt 'thank you' to a random group member.",
    "Use no vowels for the next 3 messages.",
    "Pretend to be the bot for the next 2 messages.",
    "Tell a 30-second motivational speech.",
    "Send your current step count.",
    "Send the most recent screenshot you took.",
    "Text a random contact 'Do you remember me?' and screenshot.",
    "Sing in a high-pitched voice; voice note.",
    "Send a picture of a stranger's pet you've taken.",
    "Reveal the first item in your shopping cart online.",
    "Speak in third person for 5 minutes.",
    "Imitate a dramatic movie scene; voice note.",
    "Wear sunglasses indoors for 30 minutes and send a pic.",
    "Send your zodiac and how accurate you think it is.",
    "Try to draw a self-portrait in 10 seconds; send pic.",
    "Make up a recipe with 3 random items from your kitchen.",
    "Send the last gif you used.",
    "Type without your thumbs for the next message.",
    "Sing one line in opera style.",
    "Send your top 3 apps.",
    "Pretend to interview yourself for 30 seconds.",
    "Reveal what you'd buy with a million dollars first.",
    "Send a photo of the inside of your wallet (no card numbers!).",
    "Speak only in song lyrics for 3 messages.",
    "Send a video saying tongue twister: 'She sells seashells.'",
    "Write a 1-star review of your morning routine.",
    "Pretend to be a news anchor for 30 seconds.",
    "Send the most random photo in your gallery.",
    "Demonstrate your best superhero pose.",
    "Send a screenshot of the weather where you are.",
    "Read aloud a random text from a stranger; voice note.",
    "Compliment yourself out loud for 30 seconds.",
    "Send the most embarrassing autocorrect you've ever sent.",
    "Take a photo of your reflection in something other than a mirror.",
    "Sing your favorite ad jingle in a voice note.",
]

# ---------------- STICKER-STYLE REACTIONS ----------------
# We send emoji-rich text messages mentioning the target (and optionally the actor),
# which is universally reliable and avoids depending on third-party sticker file_ids.
REACTIONS: Dict[str, List[str]] = {
    "hug":   ["🤗 {a} gives {b} a warm hug!", "🫂 {a} squeezes {b} tight!", "💞 {a} wraps {b} in a cozy hug."],
    "kiss":  ["😘 {a} blows {b} a kiss!", "💋 {a} kisses {b} on the cheek!", "💕 {a} sends {b} all the love."],
    "slap":  ["👋😤 {a} slaps {b}!", "🖐️💥 {a} delivers a clean slap to {b}!", "😾 {a} smacks {b} into next week!"],
    "kill":  ["☠️ {a} eliminates {b}!", "🔪 {a} sends {b} to the shadow realm!", "💀 RIP {b}, killed by {a}."],
    "cry":   ["😭 {a} bursts into tears!", "🥺 {a} sobs uncontrollably…", "💧 {a} cries on {b}'s shoulder."],
    "smile": ["😄 {a} smiles brightly at {b}.", "😊 {a} gives {b} the warmest smile!", "🥰 {a} can't stop smiling at {b}."],
    "run":   ["🏃💨 {a} runs away from {b}!", "🏃‍♂️💥 {a} sprints into the distance!", "🚶➡️💨 {a} dashes for the exit!"],
    "laugh": ["🤣 {a} laughs at {b}!", "😂 {a} can't stop laughing!", "😹 {a} bursts out laughing!"],
    "punch": ["👊 {a} punches {b}!", "🥊 {a} throws a haymaker at {b}!", "💥 {a} lands a clean punch on {b}!"],
    "bite":  ["🦷 {a} bites {b}!", "🧛 {a} sinks teeth into {b}!", "😈 {a} takes a bite out of {b}!"],
    "poke":  ["👉 {a} pokes {b}.", "🤭 {a} pokes {b} repeatedly!", "👆 {a} pokes {b} just to annoy them."],
    "pat":   ["🫳 {a} pats {b} on the head.", "🥹 {a} gives {b} a comforting pat.", "💗 {a} pats {b} gently."],
    "wave":  ["👋 {a} waves at {b}!", "🙋 {a} waves enthusiastically!", "🤚 {a} waves hi to {b}."],
    "dance": ["💃 {a} pulls {b} onto the dance floor!", "🕺 {a} starts dancing!", "🪩 {a} and {b} dance the night away!"],
    "wink":  ["😉 {a} winks at {b}.", "🤭 {a} sends {b} a sly wink.", "😏 {a} throws a wink at {b}."],
    "highfive": ["🙌 {a} high-fives {b}!", "✋💥 {a} smacks a high-five with {b}!", "🤚🤚 {a} & {b} high-five!"],
    "shoot": ["🔫 {a} shoots {b}!", "💥 {a} takes a shot at {b}!", "🎯 {a} aims and fires at {b}!"],
    "yawn":  ["🥱 {a} yawns dramatically.", "😴 {a} can't stop yawning.", "🛏️ {a} is about to fall asleep."],
    "shrug": ["🤷 {a} shrugs.", "🤷‍♂️ {a} has no idea.", "🤷‍♀️ {a} couldn't care less."],
    "facepalm": ["🤦 {a} facepalms at {b}.", "🤦‍♂️ {a} cannot believe {b}!", "😩 {a} facepalms hard."],
}


async def _send(update: Update):
    return update.effective_message


# ---------------- COMMAND HANDLERS ----------------

async def cmd_joke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(random.choice(JOKES))


async def cmd_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q, a = random.choice(RIDDLES)
    text = (
        f"🧩 <b>Riddle:</b> {safe_html(q)}\n\n"
        f"<tg-spoiler>Answer: {safe_html(a)}</tg-spoiler>"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_truth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        f"🔵 <b>Truth:</b> {safe_html(random.choice(TRUTHS))}",
        parse_mode=ParseMode.HTML,
    )


async def cmd_dare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        f"🔴 <b>Dare:</b> {safe_html(random.choice(DARES))}",
        parse_mode=ParseMode.HTML,
    )


async def cmd_truthordare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if random.random() < 0.5:
        await cmd_truth(update, context)
    else:
        await cmd_dare(update, context)


def _make_reaction_handler(action: str):
    templates = REACTIONS[action]

    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message
        actor = update.effective_user
        if not msg or not actor:
            return
        target_id = None
        target_name = None
        if msg.reply_to_message and msg.reply_to_message.from_user:
            t = msg.reply_to_message.from_user
            target_id = t.id
            target_name = t.first_name or t.username
        elif context.args:
            arg = context.args[0].lstrip("@")
            target_name = arg
        if target_id:
            b = mention_html(target_id, target_name)
        elif target_name:
            b = f"@{safe_html(target_name)}"
        else:
            b = "themselves"
        a = mention_html(actor.id, actor.first_name or actor.username)
        await msg.reply_text(
            random.choice(templates).format(a=a, b=b),
            parse_mode=ParseMode.HTML,
        )

    handler.__name__ = f"cmd_{action}"
    return handler


REACTION_HANDLERS = {name: _make_reaction_handler(name) for name in REACTIONS}


# ---------------- SIMPLE PUZZLE ----------------
PUZZLES: List[Tuple[str, str]] = [
    ("If you have 3 apples and you take away 2, how many do you have?", "2 (the ones you took)"),
    ("A farmer has 17 sheep. All but 9 die. How many are left?", "9"),
    ("How many times can you subtract 5 from 25?", "Once — after that it's not 25"),
    ("What's the next number: 2, 4, 8, 16, ?", "32"),
    ("If a plane crashes on the border of US and Canada, where do you bury the survivors?", "You don't bury survivors"),
    ("A bat and a ball cost $1.10. The bat costs $1 more than the ball. How much is the ball?", "5 cents"),
    ("Which is heavier: a pound of feathers or a pound of bricks?", "Same — both a pound"),
    ("I add 5 to 9 and get 2. The answer is correct. How?", "Clock arithmetic: 9 AM + 5 hours = 2 PM"),
    ("How many months have 28 days?", "All 12"),
    ("Next in series: J, F, M, A, M, J, J, ?", "A (August)"),
]


async def cmd_puzzle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q, a = random.choice(PUZZLES)
    await update.effective_message.reply_text(
        f"🧠 <b>Puzzle:</b> {safe_html(q)}\n\n<tg-spoiler>Answer: {safe_html(a)}</tg-spoiler>",
        parse_mode=ParseMode.HTML,
    )
