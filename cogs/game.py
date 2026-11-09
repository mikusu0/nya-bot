import time, asyncio, random, discord, os
from discord.ext import commands
from discord import app_commands, User, Member
from core.db import Database
import core.db as db
from core.utils import (get_user_id, get_user_by_id, auto_complete)
from typing import List, Dict, Tuple, Optional, Type, cast
from io import BytesIO
from PIL import Image
from core.logger import logger
from config import GUILD
from bot import MyBot

CARDS_PATH = r"data/cards"
DURAKE_TEMPLATES_PATH = r"data/durak_templates"

os.makedirs(CARDS_PATH, exist_ok=True)
os.makedirs(DURAKE_TEMPLATES_PATH, exist_ok=True)

class Player():
    def __init__(self, member: User | Member, index: int):
        self.member = member
        self.index = index
        

class Game(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, db: Database, player1: Player, player2: Player):
        super().__init__(timeout=30)
        self.player1 = player1
        self.player2 = player2
        self.db: Database = db
        self.turn: Player | DurakPlayer = random.choice([self.player1, self.player2])
        self.running = False
        self.description = ""
        self.title = "Unknown game"
        self.game_name = "Unknown game"
        self.interaction = interaction
        self.player2_interaction: Optional[discord.Interaction] = None
    
    async def start(self, *args, **kwargs):
        pass

    async def disable_childs(self):
        for child in self.children:
            if isinstance(child, (discord.ui.Button, discord.ui.Select)):
                child.disabled = True

    async def on_timeout(self):
        await self.disable_childs()
        self.clear_items()

class TicTacToe(Game):
    def __init__(self, interaction: discord.Interaction, db: Database, player1: Player, player2: Player):
        super().__init__(interaction, db, player1, player2)
        self.game_name = "Tic Tac Toe"
        self.title = f"{self.game_name} **                          **"
        self.board = [" "] * 9

    async def start(self, player2_interaction = None):
        self.running = True
        for i in range(0,9):
            self.add_item(TicTacToeButton(self, i))

        embed = discord.Embed(
            title=self.title,
            description=f"{self.turn.member.mention}'s move."
        )
        updated_field = await self.update_field()
        embed.add_field(name="Board",value=updated_field)
        await self.interaction.edit_original_response(embed=embed, view=self)

    async def make_move(self, interaction: discord.Interaction, button: discord.ui.Button, index: int):
        await interaction.response.defer()
        if interaction.user.id != self.turn.member.id: return
        if self.board[index] != " ": return

        mark = "1" if self.turn.member == self.player1.member else "2"
        self.board[index] = mark

        button.label = "⭕" if mark == "1" else "❌"
        button.disabled = True
        self.turn = self.player2 if self.turn == self.player1 else self.player1
        description=f"{self.turn.member.mention}'s move."

        winner = await self.check_winner()
        if winner:
            await self.disable_childs()
            description = f"🎮 Game has ended.\n🏆 {interaction.user.mention} has won the game!"
            self.running = False
            self.clear_items()
            await self.db.add_value_user_data(interaction.user.id, "exp", 10)
            await self.db.add_value_user_data(interaction.user.id, "balance", 100)

            restart_button = RestartButton(self)
            self.add_item(restart_button)
                         
        if " " not in self.board:
            await self.disable_childs()
            description = f"🎮 Game has ended.\n👾 Nobody has won, a draw."
            self.running = False
            self.clear_items()

            restart_button = RestartButton(self)
            self.add_item(restart_button)

        embed = discord.Embed(
            title=self.title,
            description=description
        )
        self.description = description
        updated_field = await self.update_field()
        embed.add_field(name="Board",value=updated_field)

        await self.interaction.edit_original_response(embed=embed, view=self)

    async def update_field(self):
        field = ''
        for i in range(0,9):
            v = self.board[i]

            if v == "1": field += "⭕"
            elif v == "2": field += "❌"
            else: field += "⬛"

            if (i+1) % 3 == 0: field += "\n"
            
        return field

    async def check_winner(self):
        wins = [
            [0,1,2],
            [3,4,5],
            [6,7,8],

            [0,3,6],
            [1,4,7],
            [2,5,8],

            [0,4,8],
            [2,4,6],
        ]
        for a,b,c in wins:
            if self.board[a] != " " and self.board[a] == self.board[b] == self.board[c]:
                return True
        return False 

    async def on_timeout(self):
        await super().on_timeout()

        if self.running:
            description = f"🎮 Game has ended.\n⏱️ {self.turn.member.mention} didn't respond in time."
        else:
            description = self.description

        embed = discord.Embed(
            title=self.title,
            description = description,
        )
        updated_field = await self.update_field()
        embed.add_field(name="Board",value=updated_field)
        await self.interaction.edit_original_response(embed=embed, view=self)
        self.stop()

class TicTacToeButton(discord.ui.Button):
    def __init__(self, ttt: TicTacToe, index: int):
        super().__init__(label="⬛", style=discord.ButtonStyle.secondary, row=(index)//3)
        self.index = index
        self.ttt = ttt

    async def callback(self, interaction: discord.Interaction):
        await self.ttt.make_move(interaction, self, self.index)

#----RESTART BUTTON----
class RestartButton(discord.ui.Button):
    def __init__(self, ttt: TicTacToe):
        super().__init__(label="Restart 0/2", style=discord.ButtonStyle.green, emoji="🎮")
        self.ttt = ttt
        self.voted = []
        self.voted_numb = 0
    
    async def callback(self, interaction: discord.Interaction):
        interacted_user_id = interaction.user.id
        await interaction.response.defer()

        if interacted_user_id not in [self.ttt.player1.member.id, self.ttt.player2.member.id]:
            await interaction.response.send_message("You ur player of game do !ttt", ephemeral=True)
            return
        
        if interacted_user_id not in self.voted:
            self.voted.append(interacted_user_id)
            self.voted_numb += 1
            self.label = f"Restart {self.voted_numb}/2"
            await self.ttt.interaction.edit_original_response(view=self.view) # updating button
        
        if len(self.voted) < 2: return
        
        
        new_game = TicTacToe(interaction, self.ttt.db, self.ttt.player1, self.ttt.player2)        
        await self.ttt.disable_childs()
        self.ttt.clear_items()
        self.ttt.stop()

        await self.ttt.interaction.edit_original_response(view=self.view) #need to update, clear items just on py fucks it
        await new_game.start()

# ----DURAK----

class DurakPlayer(Player):
    def __init__(self, member, index):
        super().__init__(member, index)
        self.cards = []
        self.state = ""
        self.interaction: Optional[discord.Interaction] = None
        self.own_message: Optional[discord.Message] = None
        self.afk_fines = 0

class Card():
    def __init__(self, power: int, rank: str, suit: str, image_path: str, label: str, emoji: str):
        self.power = power
        self.rank = rank
        self.suit = suit
        self.labal = label
        self.emoji = emoji
        self.image_path = image_path
        self.random_angle = 0
    
    def get_random_angle(self, n1 = -5, n2 = 5):
        self.random_angle = random.randint(n1, n2)

class Durak(Game):
    _cahced_images = None
    
    @staticmethod
    async def validate_durak_params(interaction: discord.Interaction, mode: str, deck_size: int) -> bool:
        text = None
        if not mode: text = "You must give mode."
        if mode not in ["throw-in", "transfer"]: text = "Wrong mode."
        if not isinstance(deck_size, int): text = "Deck size must be a number."
        if deck_size not in [12,24,36,52]: text = "Deck size must be one of: 12, 24, 36, 52."
        if text: await interaction.response.send_message(text, ephemeral=True); return True
        return False  

    def __init__(self, *args, mode: str, deck_size: int):
        super().__init__(*args)
        self.player1: DurakPlayer
        self.player2: DurakPlayer
        self.game_name = "Durak"
        self.title = f"{self.game_name} **                          **"
        self.deck_size = deck_size     # 52 36 24 12
        self.mode = mode

        self.card_list = [
            {"short": "1", "power": 1, "name": "One"},
            {"short": "2", "power": 2, "name": "Two"},
            {"short": "3", "power": 3, "name": "Three"},
            {"short": "4", "power": 4, "name": "Four"},
            {"short": "5", "power": 5, "name": "Five"},
            {"short": "6", "power": 6, "name": "Six"},
            {"short": "7", "power": 7, "name": "Seven"},
            {"short": "8", "power": 8, "name": "Eight"},
            {"short": "9", "power": 9, "name": "Nine"},
            {"short": "10", "power": 10, "name": "Ten"},
            {"short": "J", "power": 11, "name": "Jack"},
            {"short": "Q", "power": 12, "name": "Queen"},
            {"short": "K", "power": 13, "name": "King"},
            {"short": "A", "power": 14, "name": "Ace"}
        ]

        self.suit = {
            "Heart": {"symbol": "♥", "emoji": "♥️"},
            "Diamond": {"symbol": "♦", "emoji": "♦️"},
            "Club": {"symbol": "♣", "emoji": "♣️"},
            "Spade": {"symbol": "♠", "emoji": "♠️"}
        }
        
        self.card_bank: List[Card] = self._set_cards_in_bank()
        self.trump_suit: str = self.card_bank[-1].suit
        self.table: List[Tuple[Card, Optional[Card]]] = []
        
        self.attacker: Optional[DurakPlayer] = None
        self.defender: Optional[DurakPlayer] = None
        self.action_lock = asyncio.Lock()
        self.move_timeout = 30
        self._timer_task = None
        self._start_time = time.time()

        if Durak._cahced_images is None:
            Durak._cahced_images = self._get_cached_images()

        self._card_images: Dict[str, Image.Image] = Durak._cahced_images
        self._template_table = Image.open(os.path.join(DURAKE_TEMPLATES_PATH, "table.png")).convert("RGBA")
        self._template_background = Image.open(os.path.join(DURAKE_TEMPLATES_PATH, "background.png")).convert("RGBA")
        self._template_card = Image.open(os.path.join(CARDS_PATH, "A_Heart.png")).convert("RGBA")
        self._last_card_image = self._card_images[self.card_bank[-1].image_path]
        self._side_image: Optional[Image.Image] = None
        self._table_cards_canvas: Optional[Image.Image] = None

        self._setup_images()

    def _set_cards_in_bank(self):
        result = []
        for suit_name, suit_info in self.suit.items():
            for card_data in self.card_list[-(self.deck_size//4):]:
                image_path = os.path.join(CARDS_PATH, f"{card_data['short']}_{suit_name}.png")
                card = Card(
                    card_data["power"],
                    card_data["short"],
                    suit_name, image_path,
                    card_data["short"] + suit_info["emoji"],
                    suit_info["emoji"]
                    )
                result.append(card)
        random.shuffle(result)
        return result

    def _get_cached_images(self):
        multiply = 1.7
        # if without (), it'll try call resize()(image.open)...
        return {
            card.image_path: (
                lambda img: img.resize(
                    (
                    round(img.width * multiply),
                    round(img.height * multiply)
                    ),
                    resample = Image.Resampling.LANCZOS
                    )
                ) (Image.open(card.image_path).convert("RGBA"))
            for card in self.card_bank
        }
    
    def _setup_images(self):
        adding_bounds = 170
        x_gap = 90
        y_gap = 90

        self._side_image = Image.new(
            "RGBA",
            (self._last_card_image.width + adding_bounds, self._last_card_image.height + adding_bounds),
            (0,0,0,0)
        )
        self._side_image.paste(self._last_card_image, (0,0), mask = self._last_card_image)

        self._template_background = self._template_background.resize(
            self._last_card_image.size, resample = Image.Resampling.LANCZOS
        )

        self._template_card = self._template_card.resize(
            self._last_card_image.size, resample = Image.Resampling.LANCZOS
        )

        canvas_x = x_gap + (self._template_card.width + x_gap) * 3
        canvas_y = y_gap + (self._template_card.height + y_gap) * 2 
        self._table_cards_canvas = Image.new("RGBA", (canvas_x, canvas_y), (0,0,0,0))

    def _compose_side_stack(self):
        assert self._side_image is not None
        background_image = self._template_background.copy()
        side_image = self._side_image.copy()

        for i in range((len(self.card_bank) + 5) // 6):
            rotated = background_image.rotate(-i*3, expand=True, fillcolor=(0,0,0,0))
            offset_x = -i
            offset_y = 95 + (i*1)
            side_image.paste(rotated, (offset_x, offset_y), mask=rotated)

        return side_image

    def _compose_table_cards(self):
        gap = 90
        defend_x_gap = 45
        defend_y_gap = 45
        assert self._table_cards_canvas is not None
        canvas = self._table_cards_canvas.copy()

        def convertor(cards_on_table: List[Optional[Card]], x_offset=0, y_offset=0):
            for i, card in enumerate(cards_on_table):
                if not card: continue
                col = i % 3
                row = i // 3
                x = col * (self._template_card.width + gap) + x_offset
                y = (row * (self._template_card.height + gap)) + y_offset

                card_img = self._card_images[card.image_path].copy().rotate(card.random_angle, expand=True, fillcolor=(0,0,0,0))
                canvas.paste(card_img, (x,y), card_img)
        
        convertor([attack for attack, _ in self.table])
        convertor([defend for _, defend in self.table], defend_x_gap, defend_y_gap)
        return canvas

    def get_table_image(self):
        table_image = self._template_table.copy()
        last_card = self.card_bank[-1] if self.card_bank else None

        if last_card:
            side_stack = self._compose_side_stack()
            table_image.paste(side_stack, (10, round(table_image.height / 3.4)), mask=side_stack)

        table_cards = self._compose_table_cards()
        x = (table_image.width - table_cards.width) // 2
        y = (table_image.height - table_cards.height) // 2
        table_image.paste(table_cards, (x + 70, y + 30), table_cards)    
        return table_image

    def buffer_image(self, image: Image.Image, name):
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        file = discord.File(fp=buffer, filename=f"{name}.png")
        return file

    def get_next_cards(self, player: DurakPlayer):
        for _ in range(min(6 - len(player.cards), len(self.card_bank))):
            player.cards.append(self.card_bank.pop(0))

    async def update_hand(self, player: DurakPlayer, first_time = False):
        if not self.running: return
        
        embed = discord.Embed(title=f"You're {'⚔️ attacker' if player == self.attacker else '🛡️ defender'}**                              **",
                            description=f"You have {player.afk_fines} afk fine points.\n Your hand:"
                            
                            
                              )
        view = PlayerView()
        await self.update_control_bar(player, view)

        for i, card in enumerate(player.cards):
            view.add_item(DurakHandButton(self, card, i))

        if first_time:
            assert player.interaction is not None
            player.own_message = await player.interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            try:
                assert player.own_message is not None
                await player.own_message.edit(embed=embed, view=view)
            except Exception as e:
                logger.warning(f"We couldn't edit message to update hand: {e}")

    async def update_table(self):
        if not self.running: return
        assert self.attacker is not None and self.defender is not None
        table_image = self.get_table_image()  
        file = self.buffer_image(table_image, "table")
        mode_emoji = "🎯" if self.mode == "throw-in" else "🔄"
        embed = discord.Embed(
            title=self.title,
            description=f'''⚔️ {self.attacker.member.mention} attacks! ({len(self.attacker.cards)}🃏)
            🛡️ {self.defender.member.mention} defends! ({len(self.defender.cards)}🃏)
            Current trump: {self.suit[self.trump_suit]["emoji"]}
            Mode: {self.mode.capitalize()} {mode_emoji}'''
        )
        embed.set_image(url="attachment://table.png")
        await self.interaction.edit_original_response(embed=embed, attachments=[file], view=self)

    #----START-------------------
    async def start(self, player2_interaction):
        self.player1.interaction = self.interaction
        self.player2.interaction = player2_interaction
        assert self.attacker is not None
        assert self.defender is not None
        self.attacker = self.turn
        self.defender = self.player1 if self.turn == self.player2 else self.player2
        self.running = True

        await self.refill_hands()
        await self.refresh_state(True)
    
    async def stop(self, state: int):
        self.running = False
        logger.debug("Stopping game, state: " + str(state))
        assert self.attacker is not None
        assert self.defender is not None

        for player in (self.attacker, self.defender):
            if hasattr(player, "own_message") and player.own_message:
                await player.own_message.delete()

        match state:
            case 1: # draw
                text = "Nobody has won."
                await self.db.add_value_user_data(self.attacker.member.id, "exp", 100)
                await self.db.add_value_user_data(self.defender.member.id, "exp", 100)

            case 2: # attacker won
                text = f"🏆 {self.attacker.member.mention} has won!\n 🤡 {self.defender.member.mention} is Fool!"
                await self.db.add_value_user_data(self.attacker.member.id, "exp", 500)
                await self.db.add_value_user_data(self.defender.member.id, "exp", 50)               

            case 3: # defender won
                text = f"🏆 {self.defender.member.mention} has won!\n 🤡 {self.attacker.member.mention} is Fool!"
                await self.db.add_value_user_data(self.defender.member.id, "exp", 500)
                await self.db.add_value_user_data(self.attacker.member.id, "exp", 50)

            case 4: # somebody afk
                fined_player = self.attacker if self.attacker.afk_fines >= 2 else self.defender
                other_player = self.defender if fined_player == self.attacker else self.attacker
                
                text = f"🏆 {other_player.member.mention} has won!\n 🤡 {fined_player.member.mention} didn't responded in time."
                await self.db.add_value_user_data(other_player.member.id, "exp", 225)
                await self.db.add_value_user_data(fined_player.member.id, "exp", -100)

        elapsed = time.time() - self._start_time
        min, sec = divmod(int(elapsed), 60)
        text += f"\n⌛ Game lasted for {min:02d}:{sec:02d}" #formating, 0 - empty, max 2, decimel

        embed = discord.Embed(
            title=self.title,
            description=f"🎮 Game has ended.\n" + text
        )

        embed.set_image(url="attachment://table.png")
        await self.interaction.edit_original_response(embed=embed, view=self)

        return True

    async def check_for_winning(self, fined_player = None):
        if len(self.attacker.cards) == 0 and len(self.defender.cards) == 0:
            return await self.stop(1)
        elif len(self.attacker.cards) == 0:
            return await self.stop(2)
        elif len(self.defender.cards) == 0:
            return await self.stop(3)
        elif fined_player:
            return await self.stop(4)

        return False
        
    def can_beat_card(self, card1: Card, card2: Card) -> bool:
        if card1.suit == card2.suit:
            return card1.power > card2.power

        if card1.suit == self.trump_suit and card2.suit != self.trump_suit:
            return True
        
        return False

    def can_add_attack_card(self, card: Card) -> bool:
        if self.table and all(card.power != a.power and (d is None or card.power != d.power) for a,d in self.table):
            return False
        return True

    def can_transfer(self, transfer_card: Card) -> bool:
        if self.table and all(a.power == transfer_card.power and (d is None or transfer_card.power == d.power) for a,d in self.table):
            return True
        return False

    async def add_attack_card(self, card: Card):
        assert self.attacker is not None
        assert self.defender is not None
        if len(self.table) > 6: return "Table is full."
        if not self.defender.cards: return "Defender has no cards."
        if card not in self.attacker.cards: return "Card not is hand."
        if not self.can_add_attack_card(card): return "Card cant be added."

        self.attacker.cards.remove(card)
        self.table.append((card, None))
        card.get_random_angle()
        await self.refresh_state()

        return True

    async def choose_card_to_beat(self, card: Card):
        assert self.attacker is not None
        assert self.defender is not None
        if len(self.table) == 0: return
        if self.defender.state == "Taking": return

        self.defender.state = "choos_card_to_beat"
        view = PlayerView()
        embed = discord.Embed(
            title="Choose card to beat! **                          **",
            color=discord.Colour.blue()
        )
        for i, (attack_card, defend_card) in enumerate(self.table):
            if defend_card: continue
            can_beat = self.can_beat_card(card, attack_card)
            view.add_item(DurakChooseDefendBeatCard(self, attack_card, i, can_beat, card))
        
        if self.mode == "transfer" and self.can_transfer(card):
            view.add_item(DurakTransferDefenderCards(self, card))

        await self.update_control_bar(self.defender, view)
        await self.defender.own_message.edit(embed=embed, view=view)
    
    async def add_defend_card(self, card_to_beat: Card, defending_card: Card):
        assert self.attacker is not None
        assert self.defender is not None
        if self.defender.state == "Taking": return
        if not self.can_beat_card(defending_card, card_to_beat): return "Cannot beat card."
        
        for i, (a,d) in enumerate(self.table):
            if a == card_to_beat and d is None:
                self.table[i] = (a, defending_card)
                defending_card.get_random_angle(-5,-2)
                self.defender.cards.remove(defending_card)
                self.defender.state = ""
                await self.refresh_state()
                return
        
        return "Card not found on table."

    async def transfer_move(self, card_to_transfer: Card):
        assert self.attacker is not None
        assert self.defender is not None
        if self.mode != "transfer": return
        if len(self.table) >= 6: return
        if not self.attacker.cards: return "Attacker has no cards."
        if card_to_transfer not in self.defender.cards: return "Card not in hand."
        if not self.can_transfer(card_to_transfer): return "Card cant be added."
        
        card_to_transfer.get_random_angle()
        self.defender.cards.remove(card_to_transfer)
        self.table.append((card_to_transfer, None))
        self.defender.state = ""
        self.attacker, self.defender = self.defender, self.attacker 
        self.turn = self.attacker

        await self.refresh_state()
        
        return True

    async def end_turn(self, fined_player: DurakPlayer=None):
        if fined_player:
            await self.apply_afk_fine(fined_player)

        for p in [self.attacker, self.defender]:
            if p != fined_player:
                p.afk_fines = max(0, p.afk_fines - 1)


    async def pre_take_cards(self):
        self.defender.state = "Taking"
        await self.update_hand(self.attacker)

    async def take_cards(self, fined_player = None):
        for attack_card, defend_card in self.table:
            if attack_card: self.defender.cards.append(attack_card)
            if defend_card: self.defender.cards.append(defend_card)
        
        self.defender.state = ""
        self.table.clear()

        await self.end_turn(fined_player)
        await self.refill_hands()
        await self.update_hand(self.attacker)
        await self.update_hand(self.defender)
        if await self.check_for_winning(): return
        await self.update_table()
    
    async def pre_pass_move(self):
        self.attacker.state = "Beaten"
        await self.update_hand(self.defender)

    async def pass_move(self, fined_player = None):
        self.table.clear()
        self.attacker.state = ""
        self.attacker, self.defender = self.defender, self.attacker 
        self.turn = self.attacker

        await self.end_turn(fined_player)
        await self.refill_hands()
        await self.update_hand(self.attacker)
        await self.update_hand(self.defender)
        if await self.check_for_winning(): return
        await self.update_table()

    def can_take(self):
        return any(defense is None for _, defense in self.table)

    def can_pass(self):
        return all(defense is not None for attack, defense in self.table)

    async def update_control_bar(self, player: DurakPlayer, view: discord.ui.View):
        if player == self.attacker:
            if len(self.table) > 0 and self.can_pass():
                view.add_item(DurakControlButton(self, "Pass", discord.ButtonStyle.danger))
            if self.defender.state == "Taking":
                view.add_item(DurakControlButton(self, "Done", discord.ButtonStyle.success))

        if player == self.defender:
            if player.state == "choos_card_to_beat":
                view.add_item(DurakControlButton(self, "Back", discord.ButtonStyle.secondary))
            if len(self.table) > 0 and self.can_take():
                view.add_item(DurakControlButton(self, "Take", discord.ButtonStyle.danger))
            if self.attacker.state == "Beaten":
                view.add_item(DurakControlButton(self, "Beaten", discord.ButtonStyle.success))
    
    async def _reset_timer(self):
        if not self.running: return
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()

        self._timer_task = asyncio.create_task(self._timer())

    async def _timer(self):
        try:
            await asyncio.sleep(self.move_timeout)
            await self._round_on_timeout()
        except Exception as e:
            logger.error(e)
    
    async def _round_on_timeout(self):
        if self.defender.state == "Taking" or len(self.table) > 0 and self.can_take():
            await self.take_cards(self.defender)
        elif self.attacker.state == "Beaten" or len(self.table) > 0 and self.can_pass():
            await self.pass_move(self.attacker)
        elif not self.table:
            await self.pass_move(self.attacker)
        
        await self._reset_timer()

    async def apply_afk_fine(self, player: DurakPlayer):
        player.afk_fines += 2
        if player.afk_fines >= 3:
            return await self.check_for_winning(player)


    async def refresh_state(self, first_time = False):
        await asyncio.gather(
            self.update_hand(self.attacker, first_time),
            self.update_hand(self.defender, first_time),
            self._reset_timer(),
            self.update_table(),
        )

    async def refill_hands(self):
        for p in [self.attacker, self.defender]:
            self.get_next_cards(p)


class PlayerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.clear_items()
        
class DurakControlButton(discord.ui.Button):
    def __init__(self, durak: Durak, label: str, style: discord.ButtonStyle):
        super().__init__(label=label, style=style, row=4)
        self.durak = durak
        self._clicked = False

    async def callback(self, interaction: discord.Interaction):
        async with self.durak.action_lock:
            await interaction.response.defer()
            if self._clicked: return

            self._clicked = True
            self.disabled = True

            try:
                await interaction.edit_original_response(view=self.view)
            except Exception as e:
                logger.warning("Exception has occured", e)

            if self.label == "Back" and interaction.user.id == self.durak.defender.member.id:
                self.durak.defender.state = ""
                await self.durak.update_hand(self.durak.defender)
            elif self.label == "Take" and interaction.user.id == self.durak.defender.member.id:
                await self.durak.pre_take_cards()
            elif self.label == "Done" and interaction.user.id == self.durak.attacker.member.id:
                await self.durak.take_cards()
            elif self.label == "Pass" and interaction.user.id == self.durak.attacker.member.id:
                await self.durak.pre_pass_move()
            elif self.label == "Beaten" and interaction.user.id == self.durak.defender.member.id:
                await self.durak.pass_move()

            self._clicked = False

class DurakTransferDefenderCards(discord.ui.Button):
    def __init__(self, durak: Durak, card: Card):
        super().__init__(label="Transfer", style=discord.ButtonStyle.blurple)
        self.durak = durak
        self.card = card

    async def callback(self, interaction):
        await interaction.response.defer() 
        await self.durak.transfer_move(self.card)
        self.disabled = True

class DurakChooseDefendBeatCard(discord.ui.Button):
    def __init__(self, durak: Durak, card: Card, index, can_beat: bool, defending_card: Card):
        style = discord.ButtonStyle.green if can_beat else discord.ButtonStyle.red
        super().__init__(label=card.labal, style=style, row=index//3)
        self.durak = durak
        self.card_to_beat = card
        self.can_beat = can_beat
        self.disabled = not can_beat
        self.defending_card = defending_card

    async def callback(self, interaction):
        await interaction.response.defer()
        await self.durak.add_defend_card(self.card_to_beat, self.defending_card)
        self.disabled = True

class DurakHandButton(discord.ui.Button):
    def __init__(self, durak: Durak, card: Card, index):
        super().__init__(label=card.labal, style=discord.ButtonStyle.grey, row=index//5)
        self.durak = durak
        self.card = card

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        assert self.durak.attacker is not None and self.durak.defender is not None

        if interaction.user == self.durak.attacker.member:
            result = await self.durak.add_attack_card(self.card)
            if not isinstance(result, str):
                self.disabled = True

        elif interaction.user == self.durak.defender.member:
            await self.durak.choose_card_to_beat(self.card)


# ----REQUEST TO PLAY----
class RequestView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, player2: Member | User, game_name: str, game_class: Type[Game], *args, **kwargs):
        super().__init__(timeout=60)
        self.interaction: discord.Interaction = interaction
        self.player1: Member | User = interaction.user
        self.player2: Member | User = player2
        self.game_class: Type[Game] = game_class
        self.game_name: str = game_name
        self.args = args
        self.kwargs = kwargs

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player2.id:
            await interaction.response.send_message("Idi nah", ephemeral=True) #private
            return
        
        await interaction.response.defer()
        await self.game_class(*self.args, **self.kwargs).start(interaction)
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player2.id:
            await interaction.response.send_message("Idi nah", ephemeral=True) #private
            return
        
        self.clear_items()
        embed = discord.Embed(
            title=f"❌ Requst to play {self.game_name} canceled.",
            description = f"{self.player2.mention} canceled request to play.",
            color=discord.Colour.red()
        )
        await self.interaction.edit_original_response(embed=embed, view=self)
        self.stop()

    async def on_timeout(self):
        self.clear_items()
        embed = discord.Embed(
            title=f"⏱️ Request to play {self.game_name} has expired.",
            description = f"{self.player2.mention} didn't respond.",
            color=discord.Colour.red()
        )
        await self.interaction.edit_original_response(embed=embed, view=self)
        self.stop()        


class GameHandler(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.db: Database = bot.database

    @app_commands.command(name="ttt", description="Crazy game with unbeliveable gamepaly.")
    @app_commands.describe(opponent="Mention, ID, name")
    async def ttt(self, interaction: discord.Interaction, opponent: discord.User):
        player2 = await check_invite_player(self.bot, interaction, opponent.id, opponent)
        if not player2: return

        args = (interaction, self.db, Player(interaction.user, 1), Player(player2, 2))
        await request_to_play(interaction, player2, "Tic Tac Toe", TicTacToe, *args)
        
    @app_commands.command(name="durak", description="A respect game for ur mates.")
    @app_commands.describe(mode="Throw-in or transfer", deck_size="Size of deck 12|24|36|52", opponent="Mention, ID, name")
    @app_commands.autocomplete(mode=auto_complete(["throw-in", "transfer"]), deck_size = auto_complete([str(n) for n in [12,24,36,52]]))
    async def durak(self, interaction: discord.Interaction, mode: str, deck_size: int, opponent: discord.User):
        player2 = await check_invite_player(self.bot, interaction, opponent.id, opponent)
        if not player2: return
        if await Durak.validate_durak_params(interaction, mode, deck_size): return await interaction.response.defer()
       
        args = (interaction, self.db, DurakPlayer(interaction.user, 1), DurakPlayer(player2, 2))
        await request_to_play(interaction, player2, "Durak", Durak, *args, mode=mode, deck_size=deck_size)  

#----HELPFULL SHIT----
async def request_to_play(interaction: discord.Interaction, player2: Member | User, game_name: str, game_class: Type[Game], *args, **kwargs):
    embed = discord.Embed(
        title=f"Request to play {game_name}",
        description=f"User {interaction.user.mention} has invited {player2.mention} to play!"
    )
    view = RequestView(interaction, player2, game_name, game_class, *args, **kwargs)
    await interaction.response.send_message(embed=embed, view=view)

async def check_invite_player(bot: MyBot, interaction: discord.Interaction, player2_id: int, user):
    if not player2_id:
        await interaction.response.send_message(f"❌ Wrong user. User {user} is not found.", ephemeral=True)
        await interaction.response.defer()
        return False
    
    # if player2_id == interaction.user.id:
    #         await interaction.response.send_message(f"❌ You can't play with yourself.")
    #             await interaction.response.defer()        
    #             return False

    try:
        return await bot.fetch_user(player2_id)
    except Exception as e:
         await interaction.response.send_message(f"❌ Wrong user. User {user} is not found.", ephemeral=True)
    return False
    

async def setup(bot: MyBot):
    await bot.add_cog(GameHandler(bot))
