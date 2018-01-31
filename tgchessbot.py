import time, pickle, os.path
import telepot  # https://github.com/nickoala/telepot
from match import *

class tgchessBot(telepot.Bot):
    def __init__(self, *args, **kwargs):
        '''Set up local variables'''
        super(tgchessBot, self).__init__(*args, **kwargs)
        self._answerer = telepot.helper.Answerer(self)
        self.gamelog = {}
        self.msglog = []
        self.statslog = {} # Store player stats [W, D, L]

        self.startsheet, self.helpsheet = self.generate_sheets()

    def generate_sheets(self):
        startsheet = "Hello! This is the Telegram Chess Bot @tgchessbot. \U0001F601\n"
        startsheet += "For the full command list, type `/help`.\n"
        startsheet += "(You may want to use `/help@tgchessbot` instead if there are multiple bots in your chat.)\n\n"
        startsheet += "*About*\n\n"
        startsheet += "You can play chess using @tgchessbot. To play with friends, create a group and invite @tgchessbot into it. If you wish to play alone, talk to @tgchessbot on a 1-on-1 private message.\n\n"
        startsheet += "_How to play_: Someone creates a game and picks a colour (white or black). Someone else (could be the same person) joins and is automatically assigned the other side.\n\n"
        startsheet += "_Make your best move_: Make a move by typing `/move <your move>` or just `<your move>`. @tgchessbot is able to recognise both SAN and UCI notations. E.g. `/move e4` or `/move e2e4`, `/move Nf3` or `g1f3`\n\n"
        startsheet += "Every chat conversation is capped to have only 1 match going on at any point in time to avoid confusion (In case multiple people try to play matches simultaneously in the same group chat). For a more enjoyable experience, you may wish to create a group chat with 3 members: You, your friend/opponent and @tgchessbot\n\n"
        startsheet += "*Inline Commands*\n\n"
        startsheet += "You may also make use of inline commands by typing `@tgchessbot <command>`.\n"
        startsheet += "Currently available commands: `@tgchessbot /start`, `@tgchessbot /help`, `@tgchessbot /stats`.\n\n"
        startsheet += "`@tgchessbot /stats` displays how many wins, draws and losses you accumulated across all games you have played via @tgchessbot. If user base grows sufficiently large, we intend to incorporate a global ELO rating system.\n\n"
        startsheet += "At the moment, we are unable to support inline commands to play your matches unfortunately.\n\n"
        startsheet += "*Contact*\n\n"
        startsheet += "This bot is built with the help of [`telepot`](https://github.com/nickoala/telepot), [`python-chess`](https://github.com/niklasf/python-chess) and [`Pillow`](https://pillow.readthedocs.io/en/3.2.x/), with chess piece images from [Cburnett](https://en.wikipedia.org/wiki/User:Cburnett) on [Wikipedia](https://en.wikipedia.org/wiki/Chess_piece).\n\n"
        startsheet += "For more information, visit https://github.com/cxjdavin/tgchessbot/\n"
        startsheet += "Contact me at `tgchessbot@gmail.com` for bug reports, etc."

        helpsheet = "Allowed commands:\n"
        helpsheet += "`/help`: Display help sheet\n"
        helpsheet += "`/create <white/black>`: Creates a chess match with your preferred colour. E.g. `/create white`\n"
        helpsheet += "`/join`: Join the existing match\n"
        helpsheet += "`/show`: Show current board state\n"
        helpsheet += "`/move <move>` or `<move>`: Make a move using SAN or UCI. E.g. `/move e4` or `/move e2e4`, `/move Nf3` or `g1f3`. To learn more: [https://en.wikipedia.org/wiki/Algebraic_notation_(chess)]\n"
        helpsheet += "`/offerdraw`: Offer a draw. Making a move automatically cancels any existing draw offers.\n"
        helpsheet += "`/rejectdraw`: Reject opponent's draw offer. Making a move automatically rejects any existing draw offers.\n"
        helpsheet += "`/claimdraw`: Accept a draw offer or claim a draw when `fifty-move rule` or `threefold repetition` is met. To learn more: [https://en.wikipedia.org/wiki/Draw_(chess)]\n"
        helpsheet += "`/resign`: Resign from the match\n"
        helpsheet += "`/stats`: View your game stats across all matches\n\n"
        helpsheet += "If there are multiple bots, append `@tgchessbot` behind your commands. E.g. `/move@tgchessbot e4`"

        return startsheet, helpsheet

    def save_state(self):
        '''Saves gamelog, msglog and statslog for persistence'''
        with open("gamelog.txt", "wb") as f:
            pickle.dump(self.gamelog, f)

        with open("msglog.txt", "wb") as f:
            pickle.dump(self.msglog, f)

        with open("statslog.txt", "wb") as f:
            pickle.dump(self.statslog, f)

    def load_state(self):
        '''Loads gamelog, msglog and statslog for persistence'''
        try:
            with open("gamelog.txt", "rb") as f:
                self.gamelog = pickle.load(f)
        except EOFError:
            self.gamelog = {}

        try:
            with open("msglog.txt", "rb") as f:
                self.msglog = pickle.load(f)
        except EOFError:
            self.msglog = []

        try:
            with open("statslog.txt", "rb") as f:
                self.statslog = pickle.load(f)
        except EOFError:
            self.statslog = {}

    def is_in_game(self, players, sender_id):
        '''Checks if message sender is involved in the match'''
        return sender_id == players[0] or sender_id == players[2]

    def game_end(self, chat_id, players, winner):
        '''Handle end of game situation'''
        # Remove match from game logs
        del self.gamelog[chat_id]

        # Update player stats [W, D, L] and print results
        if players[0] not in self.statslog: self.statslog[players[0]] = [0,0,0]
        if players[2] not in self.statslog: self.statslog[players[2]] = [0,0,0]
        white_stats = self.statslog[players[0]]
        black_stats = self.statslog[players[2]]

        # Format and send game outcome
        outcome = ""
        if winner == "White":
            white_stats[0] += 1
            black_stats[2] += 1
            outcome = "White wins! {} (W) versus {} (B) : 1-0".format(players[1], players[3])
        elif winner == "Black":
            white_stats[2] += 1
            black_stats[0] += 1
            outcome = "Black wins! {} (W) versus {} (B) : 0-1".format(players[1], players[3])
        elif winner == "Draw":
            white_stats[1] += 1
            black_stats[1] += 1
            outcome = "It's a draw! {} (W) versus {} (B) : 0.5-0.5".format(players[1], players[3])
        self.statslog[players[0]] = white_stats
        self.statslog[players[2]] = black_stats

        bot.sendMessage(chat_id, outcome)

    def get_sender_details(self, msg):
        '''Extract sender id and name to be used in the match'''
        sender_id = msg["from"]["id"]
        if "username" in msg["from"]:
            sender_username = msg["from"]["username"]
        elif "last_name" in msg["from"]:
            sender_username = msg["from"]["last_name"]
        elif "first_name" in msg["from"]:
            sender_username = msg["from"]["first_name"]
        else:
            sender_username = "Nameless"
        return sender_id, sender_username

    def get_games_involved(self, sender_id):
        return [g for g in self.gamelog.values() if self.is_in_game(g.get_players(), sender_id)]

    def on_chat_message(self, msg):
        self.msglog.append(msg)
        content_type, chat_type, chat_id = telepot.glance(msg)
        sender_id, sender_username = self.get_sender_details(msg)
        print(msg, sender_id, sender_username)

        # Note:
        # if chat_id == sender_id, then it's a human-to-bot 1-on-1 chat
        # if chat_id != sender_id, then chat_id is group chat id
        print('Chat Message:', content_type, chat_type, chat_id, msg[content_type])

        tokens = msg[content_type].split(" ")
        match = self.gamelog[chat_id] if chat_id in self.gamelog.keys() else None
        players = match.get_players() if match != None else None

        if tokens[0] == "/start" or tokens[0] == "/start@tgchessbot":
            bot.sendMessage(chat_id, self.startsheet, parse_mode = "Markdown", disable_web_page_preview = True)
        elif tokens[0] == "/help" or tokens[0] == "/help@tgchessbot":
            bot.sendMessage(chat_id, self.helpsheet, parse_mode = "Markdown", disable_web_page_preview = True)
        elif tokens[0] == "/create" or tokens[0] == "/create@tgchessbot":
            # !create <current player color: white/black>
            if len(tokens) < 2:
                bot.sendMessage(chat_id, "Incorrect usage. `Usage: /create <White/Black>`. E.g. `/create white`", parse_mode='Markdown')
            tokens[1] = tokens[1].lower()
            if tokens[1] != "white" and tokens[1] != "black":
                bot.sendMessage(chat_id, "Incorrect usage. `Usage: /create <White/Black>`. E.g. `/create white`", parse_mode='Markdown')
            elif match != None:
                bot.sendMessage(chat_id, "There is already a chess match going on.")
            else:
                self.gamelog[chat_id] = Match(chat_id)
                match = self.gamelog[chat_id]
                if tokens[1] == "white":
                    match.joinw(sender_id, sender_username)
                else:
                    match.joinb(sender_id, sender_username)
                bot.sendMessage(chat_id, "Chess match created. {} is playing as {}. Waiting for opponent...".format(sender_username, tokens[1]), parse_mode = "Markdown")
        elif tokens[0] == "/join" or tokens[0] == "/join@tgchessbot":
            if match == None:
                bot.sendMessage(chat_id, "There is no chess match going on.")
            elif match.white_id != None and match.black_id != None:
                bot.sendMessage(chat_id, "Game is already full.")
            else:
                match.join(sender_id, sender_username)
                players = match.get_players()
                bot.sendMessage(chat_id, "Chess match joined.\n{} (W) versus {} (B)".format(players[1], players[3]), parse_mode = "Markdown")

                # Print starting game state
                filename = match.print_board(chat_id)
                turn_id = match.get_turn_id()
                bot.sendPhoto(chat_id, open(filename, "rb"), caption = "@{} ({}) to move.".format(match.get_name(turn_id), match.get_color(turn_id)))
        elif tokens[0] == "/show" or tokens[0] == "/show@tgchessbot":
            if match == None:
                bot.sendMessage(chat_id, "There is no chess match going on.")
            elif match.white_id == None or match.black_id == None:
                bot.sendMessage(chat_id, "Game still lacks another player.")
            else:
                filename = match.print_board(chat_id)
                turn_id = match.get_turn_id()
                bot.sendPhoto(chat_id, open(filename, "rb"), caption = "{} ({}) to move.".format(match.get_name(turn_id), match.get_color(turn_id)))
        elif tokens[0] == "/move" or tokens[0] == "/move@tgchessbot" or (match and match.parse_move(tokens[0])): # !move <SAN move>
            if match == None:
                bot.sendMessage(chat_id, "There is no chess match going on.")
            elif not self.is_in_game(players, sender_id):
                bot.sendMessage(chat_id, "You are not involved in the chess match.")
            elif match.get_turn_id() != sender_id:
                bot.sendMessage(chat_id, "It's not your turn.")
            else:
                had_offer = False
                if match.drawoffer != None:
                    had_offer = True
                move = tokens[0] if match.parse_move(tokens[0]) else ''.join(tokens[1:])
                res = match.make_move(move)
                if res == "Invalid":
                    bot.sendMessage(chat_id, "`{}` is not a valid move.".format(move), parse_mode = "Markdown")
                else:
                    if had_offer:
                        bot.sendMessage(chat_id, 'Draw offer cancelled.')
                    filename = match.print_board(chat_id)
                    if res == "Checkmate":
                        bot.sendPhoto(chat_id, open(filename, "rb"), caption = "Checkmate!")
                        self.game_end(chat_id, players, match.get_color(sender_id))
                    elif res == "Stalemate":
                        bot.sendPhoto(chat_id, open(filename, "rb"), caption = "Stalemate!")
                        self.game_end(chat_id, players, "Draw")
                    elif res == "Check":
                        bot.sendPhoto(chat_id, open(filename, "rb"), caption = "Check!")
                    else:
                        turn_id = match.get_turn_id()
                        bot.sendPhoto(chat_id, open(filename, "rb"), caption = "@{} ({}) to move.".format(match.get_name(turn_id), match.get_color(turn_id)))
        elif tokens[0] == "/offerdraw" or tokens[0] == "/offerdraw@tgchessbot": # Offer a draw
            if match == None:
                bot.sendMessage(chat_id, "There is no chess match going on.")
            elif not self.is_in_game(players, sender_id):
                bot.sendMessage(chat_id, "You are not involved in the chess match.")
            elif match.get_turn_id() != sender_id:
                bot.sendMessage(chat_id, "It's not your turn.")
            else:
                match.offer_draw(sender_id)
                bot.sendMessage(chat_id, "{} ({}) offers a draw.".format(sender_username, match.get_color(sender_id)))
        elif tokens[0] == "/rejectdraw" or tokens[0] == "/rejectdraw@tgchessbot": # Reject draw offer
            if match == None:
                bot.sendMessage(chat_id, "There is no chess match going on.")
            elif not self.is_in_game(players, sender_id):
                bot.sendMessage(chat_id, "You are not involved in the chess match.")
            elif match.drawoffer == match.get_opp_id(sender_id):
                match.reject_draw()
                bot.sendMessage(chat_id, 'Draw offer cancelled by {} ({}).'.format(sender_username, match.get_color(sender_id)))
            else:
                bot.sendMessage(chat_id, "There is no draw offer to reject.")
        elif tokens[0] == "/claimdraw" or tokens[0] == "/claimdraw@tgchessbot": # Either due to offer or repeated moves
            if match == None:
                bot.sendMessage(chat_id, "There is no chess matches going on.")
            elif not self.is_in_game(players, sender_id):
                bot.sendMessage(chat_id, "You are not involved in the chess match.")
            elif match.get_turn_id() != sender_id:
                bot.sendMessage(chat_id, "It's not your turn.")
            elif match.board.can_claim_draw() or match.drawoffer == match.get_opp_id(sender_id):
                self.game_end(chat_id, players, "Draw")
            else:
                bot.sendMessage(chat_id, "Current match situation does not warrant a draw.")
        elif tokens[0] == "/resign" or tokens[0] == "/resign@tgchessbot":
            if match == None:
                bot.sendMessage(chat_id, "There is no chess match going on.")
            elif not self.is_in_game(players, sender_id):
                bot.sendMessage(chat_id, "You are not involved in the chess match.")
            else:
                bot.sendMessage(chat_id, "`{} ({}) resigns!`".format(sender_username, match.get_color(sender_id)), parse_mode='Markdown')
                self.game_end(chat_id, players, match.get_opp_color(sender_id))
        elif tokens[0] == "/stats" or tokens[0] == "/stats@tgchessbot":
            if sender_id not in self.statslog:
                bot.sendMessage(chat_id, "You have not completed any games with @tgchessbot.")
            else:
                pstats = self.statslog[sender_id]
                bot.sendMessage(chat_id, "{}: {} wins, {} draws, {} losses.".format(sender_username, pstats[0], pstats[1], pstats[2]))

    def on_callback_query(self, msg):
        '''Just logs the message. Does nothing for now'''
        self.msglog.append(msg)
        print(msg)

    def on_inline_query(self, msg):
        '''Handles online queries by dynamically checking if it matches any keywords in the bank'''
        self.msglog.append(msg)
        print(msg)

        query_id, from_id, query_string = telepot.glance(msg, flavor = "inline_query")
        def compute_answer():
            bank = [{"type": "article", "id": "/start", "title": "/start", "description": "Starts the bot in this chat", "message_text": "/start"},
                    {"type": "article", "id": "/help", "title": "/help", "description": "Displays help sheet for @tgchessbot", "message_text": "/help"},
                    {"type": "article", "id": "/stats", "title": "/stats", "description": "Displays your match statistics with @tgchessbot", "message_text": "/stats"}]
            ans = [opt for opt in bank if query_string in opt["id"]]
            for opt in bank:
                print(query_string, opt["id"], query_string in opt["id"])
            return ans

        self._answerer.answer(msg, compute_answer)

    def on_chosen_inline_result(self, msg):
        '''Just logs the message. Does nothing for now'''
        self.msglog.append(msg)
        print(msg)

############
# AUTO RUN #
############
telegram_bot_token = "<REMOVED>"
bot = tgchessBot(telegram_bot_token)

# For persistence
if not os.path.exists("gamelog.txt"):
    with open("gamelog.txt", "wb") as f:
        pickle.dump({}, f)
if not os.path.exists("msglog.txt"):
    with open("msglog.txt", "wb") as f:
        pickle.dump([], f)
if not os.path.exists("statslog.txt"):
    with open("statslog.txt", "wb") as f:
        pickle.dump({}, f)
bot.load_state()
print("Previous state loaded.")

# For server log
print("Bot is online: ", bot.getMe())
bot.message_loop()
print("Listening...")

# Keep the program running.
while 1:
    time.sleep(10)
    bot.save_state() # Save state periodically
