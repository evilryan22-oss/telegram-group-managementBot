"""Quiz command — sends a random trivia question as a Telegram quiz poll."""
from __future__ import annotations

import logging
import random
from typing import List, Tuple

from telegram import Update
from telegram.ext import ContextTypes

log = logging.getLogger(__name__)

# (question, [options], correct_index, explanation)
QUIZZES: List[Tuple[str, List[str], int, str]] = [
    ("Capital of France?", ["Berlin", "Madrid", "Paris", "Rome"], 2, "Paris is the capital of France."),
    ("Largest planet in our solar system?", ["Earth", "Jupiter", "Saturn", "Neptune"], 1, "Jupiter is the largest."),
    ("Who wrote 'Hamlet'?", ["Dickens", "Shakespeare", "Twain", "Austen"], 1, "William Shakespeare."),
    ("Chemical symbol for gold?", ["Go", "Gd", "Au", "Ag"], 2, "Au, from Latin 'aurum'."),
    ("Fastest land animal?", ["Lion", "Cheetah", "Horse", "Greyhound"], 1, "Cheetah, up to ~120 km/h."),
    ("How many continents are there?", ["5", "6", "7", "8"], 2, "7 continents."),
    ("Square root of 144?", ["10", "11", "12", "14"], 2, "12 × 12 = 144."),
    ("Largest ocean?", ["Atlantic", "Indian", "Arctic", "Pacific"], 3, "Pacific is the largest."),
    ("Currency of Japan?", ["Yuan", "Won", "Yen", "Ringgit"], 2, "The Japanese Yen."),
    ("Who painted the Mona Lisa?", ["Van Gogh", "Da Vinci", "Picasso", "Monet"], 1, "Leonardo da Vinci."),
    ("Speed of light (approx, km/s)?", ["300,000", "150,000", "1,000,000", "30,000"], 0, "~299,792 km/s."),
    ("H2O is the formula for?", ["Salt", "Water", "Oxygen", "Hydrogen"], 1, "Water."),
    ("Tallest mountain on Earth?", ["K2", "Everest", "Kilimanjaro", "Denali"], 1, "Mount Everest."),
    ("How many sides does a hexagon have?", ["5", "6", "7", "8"], 1, "Six sides."),
    ("Year WWII ended?", ["1943", "1944", "1945", "1946"], 2, "1945."),
    ("Largest desert in the world?", ["Sahara", "Gobi", "Antarctic", "Arabian"], 2, "Antarctic Desert."),
    ("Who discovered penicillin?", ["Newton", "Fleming", "Curie", "Edison"], 1, "Alexander Fleming, 1928."),
    ("Chemical symbol for sodium?", ["So", "Sd", "Na", "S"], 2, "Na, from 'natrium'."),
    ("How many bones in adult human body?", ["196", "206", "216", "256"], 1, "206 bones."),
    ("What gas do plants absorb?", ["O2", "N2", "CO2", "H2"], 2, "Carbon dioxide."),
    ("Smallest prime number?", ["0", "1", "2", "3"], 2, "2 is the smallest prime."),
    ("Author of '1984'?", ["Huxley", "Orwell", "Tolkien", "Asimov"], 1, "George Orwell."),
    ("Capital of Australia?", ["Sydney", "Melbourne", "Canberra", "Perth"], 2, "Canberra."),
    ("How many players on a football (soccer) team?", ["9", "10", "11", "12"], 2, "11 per side."),
    ("Largest mammal?", ["Elephant", "Blue Whale", "Giraffe", "Orca"], 1, "Blue whale."),
    ("What language is spoken in Brazil?", ["Spanish", "Portuguese", "French", "Italian"], 1, "Portuguese."),
    ("How many colors in a rainbow?", ["5", "6", "7", "8"], 2, "Seven (ROYGBIV)."),
    ("Boiling point of water at sea level (°C)?", ["50", "90", "100", "120"], 2, "100 °C."),
    ("Which planet is known as the Red Planet?", ["Venus", "Mars", "Jupiter", "Mercury"], 1, "Mars."),
    ("HTML stands for?", ["HyperText Markup Language", "HighTech Modern Lang", "Hyperlinks and Text Markup", "Home Tool Markup"], 0, "HyperText Markup Language."),
    ("Inventor of the telephone?", ["Edison", "Bell", "Tesla", "Marconi"], 1, "Alexander Graham Bell."),
    ("Largest country by area?", ["Canada", "China", "USA", "Russia"], 3, "Russia."),
    ("Smallest country in the world?", ["Monaco", "Vatican City", "Malta", "San Marino"], 1, "Vatican City."),
    ("Which element has symbol 'O'?", ["Osmium", "Oxygen", "Olivine", "Ozone"], 1, "Oxygen."),
    ("How many strings does a standard guitar have?", ["4", "5", "6", "7"], 2, "Six strings."),
    ("Who painted the ceiling of the Sistine Chapel?", ["Raphael", "Michelangelo", "Donatello", "Da Vinci"], 1, "Michelangelo."),
    ("Pi to two decimals?", ["3.12", "3.14", "3.16", "3.18"], 1, "3.14."),
    ("Which organ pumps blood?", ["Liver", "Lung", "Heart", "Kidney"], 2, "The heart."),
    ("How many legs does a spider have?", ["6", "8", "10", "12"], 1, "Eight."),
    ("Sun rises in which direction?", ["North", "South", "East", "West"], 2, "East."),
    ("Hottest planet in our solar system?", ["Mercury", "Venus", "Mars", "Jupiter"], 1, "Venus, due to greenhouse effect."),
    ("What does CPU stand for?", ["Central Processing Unit", "Computer Personal Unit", "Central Power Unit", "Control Process Unit"], 0, "Central Processing Unit."),
    ("Which sea is the saltiest?", ["Dead Sea", "Red Sea", "Black Sea", "Caspian"], 0, "Dead Sea."),
    ("Author of 'Harry Potter'?", ["Tolkien", "Rowling", "Pullman", "Lewis"], 1, "J. K. Rowling."),
    ("Which is a noble gas?", ["Oxygen", "Hydrogen", "Helium", "Nitrogen"], 2, "Helium."),
    ("DNA stands for?", ["Deoxyribonucleic Acid", "Dinucleic Acid", "Double Nucleic Atom", "Diatomic Nucleic Acid"], 0, "Deoxyribonucleic Acid."),
    ("Which country has the most population?", ["USA", "India", "China", "Russia"], 1, "India recently overtook China."),
    ("Capital of Canada?", ["Toronto", "Vancouver", "Ottawa", "Montreal"], 2, "Ottawa."),
    ("What's the freezing point of water (°F)?", ["0", "16", "32", "100"], 2, "32 °F."),
    ("Which planet has the most moons?", ["Jupiter", "Saturn", "Uranus", "Neptune"], 1, "Saturn (with recent discoveries)."),
    ("First man on the moon?", ["Aldrin", "Gagarin", "Armstrong", "Glenn"], 2, "Neil Armstrong, 1969."),
    ("Currency of the UK?", ["Euro", "Pound", "Dollar", "Franc"], 1, "Pound sterling."),
    ("Which is the largest internal organ?", ["Heart", "Lung", "Liver", "Kidney"], 2, "Liver."),
    ("How many teeth does an adult have?", ["28", "30", "32", "34"], 2, "32 including wisdom teeth."),
    ("Which is the longest river?", ["Amazon", "Nile", "Yangtze", "Mississippi"], 1, "The Nile (traditionally)."),
    ("Number of players in a basketball team on court?", ["4", "5", "6", "7"], 1, "5 per side."),
    ("Element with atomic number 1?", ["Helium", "Hydrogen", "Oxygen", "Carbon"], 1, "Hydrogen."),
    ("Capital of Germany?", ["Munich", "Hamburg", "Berlin", "Frankfurt"], 2, "Berlin."),
    ("Which programming language is named after a snake?", ["Cobra", "Python", "Viper", "Anaconda"], 1, "Python."),
    ("Total number of keys on a standard piano?", ["76", "82", "88", "92"], 2, "88 keys."),
    ("Who developed the theory of relativity?", ["Newton", "Einstein", "Hawking", "Galileo"], 1, "Albert Einstein."),
    ("Largest island in the world?", ["Australia", "Greenland", "Borneo", "Madagascar"], 1, "Greenland (Australia is a continent)."),
    ("Which vitamin is produced by sun exposure?", ["A", "B12", "C", "D"], 3, "Vitamin D."),
    ("Speed unit 'knot' is used for?", ["Cars", "Ships/Planes", "Bikes", "Trains"], 1, "Ships and aircraft."),
    ("Capital of Spain?", ["Barcelona", "Madrid", "Seville", "Valencia"], 1, "Madrid."),
    ("How many minutes in a full day?", ["1200", "1440", "1600", "2400"], 1, "24×60 = 1440."),
    ("What does GPU stand for?", ["Graphics Processing Unit", "General Power Unit", "Graphic Power Unit", "Game Processing Unit"], 0, "Graphics Processing Unit."),
    ("Which is the smallest planet?", ["Mercury", "Mars", "Venus", "Pluto"], 0, "Mercury (Pluto is dwarf)."),
    ("Largest hot desert?", ["Sahara", "Gobi", "Kalahari", "Arabian"], 0, "Sahara."),
    ("Largest organ of the human body?", ["Liver", "Skin", "Heart", "Brain"], 1, "The skin."),
    ("In what year did the Titanic sink?", ["1905", "1912", "1918", "1923"], 1, "1912."),
    ("Sound travels fastest in?", ["Air", "Water", "Steel", "Vacuum"], 2, "Steel (solids)."),
    ("Which country gifted the Statue of Liberty to the US?", ["UK", "France", "Spain", "Italy"], 1, "France, 1886."),
    ("Most spoken native language?", ["English", "Spanish", "Mandarin", "Hindi"], 2, "Mandarin Chinese."),
    ("Capital of Italy?", ["Milan", "Rome", "Naples", "Venice"], 1, "Rome."),
    ("How many sides does a dodecagon have?", ["10", "12", "14", "20"], 1, "12 sides."),
    ("'CSS' stands for?", ["Cascading Style Sheets", "Computer Style System", "Creative Style Source", "Custom Sheet Style"], 0, "Cascading Style Sheets."),
    ("Continent of Egypt?", ["Asia", "Africa", "Europe", "Oceania"], 1, "Africa."),
    ("Which fruit is high in potassium?", ["Apple", "Banana", "Pear", "Grape"], 1, "Banana."),
    ("Pythagoras theorem: a²+b²=?", ["c", "c²", "2c", "c³"], 1, "c² (hypotenuse squared)."),
    ("Which animal is known as the 'King of the Jungle'?", ["Tiger", "Lion", "Elephant", "Bear"], 1, "Lion."),
    ("Inventor of light bulb?", ["Tesla", "Edison", "Bell", "Marconi"], 1, "Thomas Edison (commercial)."),
    ("Largest bird that cannot fly?", ["Penguin", "Kiwi", "Ostrich", "Emu"], 2, "Ostrich."),
    ("First president of the USA?", ["Lincoln", "Adams", "Washington", "Jefferson"], 2, "George Washington."),
    ("How many planets in our solar system?", ["7", "8", "9", "10"], 1, "8 (Pluto reclassified)."),
    ("Common name for sodium chloride?", ["Sugar", "Salt", "Baking soda", "Vinegar"], 1, "Salt."),
    ("Which year did humans first land on the moon?", ["1959", "1965", "1969", "1972"], 2, "1969."),
    ("Where is the Great Pyramid?", ["Mexico", "Egypt", "China", "Iraq"], 1, "Egypt."),
    ("Which famous scientist proposed 3 laws of motion?", ["Galileo", "Newton", "Einstein", "Hawking"], 1, "Isaac Newton."),
    ("How many faces does a cube have?", ["4", "6", "8", "12"], 1, "6 faces."),
    ("Capital of Russia?", ["St. Petersburg", "Moscow", "Kazan", "Sochi"], 1, "Moscow."),
    ("Largest organ of digestion?", ["Stomach", "Small intestine", "Liver", "Pancreas"], 1, "Small intestine."),
    ("Currency of India?", ["Rupee", "Rupiah", "Ringgit", "Riyal"], 0, "Indian Rupee."),
    ("'WWW' stands for?", ["World Wide Web", "Wide World Web", "World Web Wide", "Web World Wide"], 0, "World Wide Web."),
    ("What is 7 × 8?", ["54", "56", "58", "64"], 1, "56."),
    ("Number of zeros in one million?", ["5", "6", "7", "9"], 1, "6."),
    ("Most abundant gas in Earth's atmosphere?", ["Oxygen", "Nitrogen", "Argon", "CO2"], 1, "Nitrogen (~78%)."),
    ("Color of chlorophyll?", ["Red", "Yellow", "Green", "Blue"], 2, "Green."),
    ("How many hours in a week?", ["120", "144", "168", "192"], 2, "7×24 = 168."),
    ("Which country invented paper?", ["Egypt", "China", "Greece", "India"], 1, "China."),
]


async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question, options, correct, explanation = random.choice(QUIZZES)
    chat = update.effective_chat
    try:
        await context.bot.send_poll(
            chat_id=chat.id,
            question=question,
            options=options,
            type="quiz",
            correct_option_id=correct,
            explanation=explanation,
            is_anonymous=False,
        )
    except Exception as e:  # noqa: BLE001
        log.warning("send_poll failed (%s), falling back to text", e)
        text = "❓ " + question + "\n" + "\n".join(
            f"{i+1}. {o}" for i, o in enumerate(options)
        ) + f"\n\nAnswer: ||{correct+1}. {options[correct]}||"
        await update.effective_message.reply_text(text)
