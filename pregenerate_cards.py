from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

PATH = r"data/durak_templates"
OUTPUT = r"data/cards"

CARD_SYMBOLS = True

os.makedirs(OUTPUT, exist_ok=True)

def generate(suit_name: str, value: str, symbol: str):
    background = Image.open(os.path.join(PATH, "template.png")).convert("RGBA")

    card = Image.new("RGBA", background.size)
    card.paste(background,(0,0))

    symbol_path = os.path.join(PATH, f"{value}.png")

    if os.path.exists(symbol_path) and CARD_SYMBOLS:
        symbol_card = Image.open(symbol_path).convert("RGBA")
        card.paste(symbol_card, (0,0), mask=symbol_card)
    else:
        suit_img = Image.open(os.path.join(PATH, f"{suit_name}.png")).convert("RGBA")
        card.paste(suit_img,(0,0), mask=suit_img)
           

    # MASK: Uses alpha channel to control what pixels are pasted. Keeps transparent parts invisible
    color = "black" if suit_name in ["Club", "Spade"] else "red"

    def draw_text(image):
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", 45)

        drawing_text = value + ("." if value in ["6", "9"] else "") 
        draw.text((5,2), drawing_text, font=font, fill=color)

        drawing_text = symbol
        font = ImageFont.truetype("arial.ttf", 30)
        draw.text((10,35), drawing_text, font=font, fill=color)

        drawing_text = symbol
        font = ImageFont.truetype("arial.ttf", 50)
        x = 50 if value in ["10"] else 40
        draw.text((x,1), drawing_text, font=font, fill=color)
    
    draw_text(card)
    text_img2 = Image.new("RGBA", background.size, (0,0,0,0)) # 0 0 0 0 (RGBA) fully transperent
    draw_text(text_img2)

    text_rotated = text_img2.rotate(180, expand=True) # need expand to not fuck edges idk

    card.paste(text_rotated, (0,0), mask=text_rotated)

    # mask = Image.new("L", card.size, 0) #L - 8bit gray scale
    # draw = ImageDraw.Draw(mask)
    # draw.rounded_rectangle((0, 0, *card.size), radius=25, fill=255)
    # mask = mask.filter(ImageFilter.GaussianBlur(3))
    # card.putalpha(mask)

    card.save(os.path.join(OUTPUT, f"{value}_{suit_name}.png"))

suit_symbols = {
    "Heart": {"symbol": "♥", "emoji": "♥️"},
    "Diamond": {"symbol": "♦", "emoji": "♦️"},
    "Club": {"symbol": "♣", "emoji": "♣️"},
    "Spade": {"symbol": "♠", "emoji": "♠️"}
}

for suit in ["Heart", "Diamond", "Spade", "Club"]:
    for value in ["1","2","3","4","5","6","7","8","9","10","J","Q","K","A"]:
        generate(suit, value, suit_symbols[suit]["symbol"])

print("Succes")