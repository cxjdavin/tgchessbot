import chess # https://github.com/niklasf/python-chess
from renderer import *

class Match():
    '''Class to handle match related stuff and interface with python-chess'''
    def __init__(self, chat_id):
        ''' Set up local variables'''
        self.board = chess.Board()
        self.chat_id = chat_id
        self.white_id = None
        self.black_id = None
        self.white_name = None
        self.black_name = None
        self.draw_offer = None
        self.imgurid = None
        self.drawoffer = None

    def joinw(self, pid, pname):
        '''Player joins as White'''
        self.white_id, self.white_name = pid, pname

    def joinb(self, pid, pname):
        '''Player joins as Black'''
        self.black_id, self.black_name = pid, pname

    def join(self, pid, pname):
        '''Handle joining of the match'''
        if self.white_id == None:
            self.joinw(pid, pname)
        else:
            self.joinb(pid, pname)

    def get_players(self):
        '''Get player id and colors'''
        return [self.white_id, self.white_name, self.black_id, self.black_name]

    # Note:
    # self.board.turn == True if it's White's turn
    # self.board.turn == False if it's Black's turn
    def get_turn_id(self):
        '''Return id of current moving player'''
        return self.white_id if self.board.turn else self.black_id

    def get_opp_id(self, pid):
        '''Return id of opponent'''
        if self.white_id == self.black_id:
            # If solo play, return based on turn
            return self.white_id if not self.board.turn else self.black_id
        else:
            # Return based on sender id
            return self.white_id if self.black_id == pid else self.black_id

    def get_color(self, pid):
        '''Return color of player based on pid'''
        if self.white_id == self.black_id:
            # If solo play, return based on turn
            return 'White' if self.board.turn else 'Black'
        else:
            # Return based on sender id
            return 'White' if self.white_id == pid else 'Black'

    def get_opp_color(self, pid):
        '''Return color of opponent based on pid'''
        if self.white_id == self.black_id:
            # If solo play, return based on turn
            return 'White' if not self.board.turn else 'Black'
        else:
            # Return based on sender id
            return 'White' if self.black_id == pid else 'Black'

    def get_name(self, pid):
        '''Return name of player based on pid'''
        if pid == self.white_id:
            return self.white_name
        elif pid == self.black_id:
            return self.black_name
        else:
            return None

    def parse_move(self, m):
        '''Feed move into python-chess to simulate'''
        # python-chess uses O instead of 0
        m = m.replace('0', 'O')

        # Check if move is in SAN.
        # python-chess: Raises ValueError if the SAN is invalid or ambiguous.
        try:
            move = self.board.parse_san(m)
        except ValueError:
            # Check if move is in UCI notation
            # python-chess Raises ValueError if the move is invalid or illegal in the current position (but not a null move).
            try:
                move = self.board.parse_uci(m)
            except ValueError:
                # If neither forms or illegal, the move is invalid
                return None
        return move

    def make_move(self, m):
        move = self.parse_move(m)
        if not move:
            return "Invalid"
        
        # Making a move invalidates any existing draw offers
        if self.drawoffer != None:
            self.reject_draw()
            
        # At this point, "move" is bound to be valid and legal.
        # i.e. (move in self.board.legal_moves) == True
        self.board.push(move)
        # The order of testing for check and checkmate is important here!
        # That is because Board.is_check() will also return true if the game position is actually checkmate.
        # See https://github.com/niklasf/python-chess/blob/0d007c23f593957f049b16df105d82d447e5833b/chess/__init__.py#L1659
        if self.board.is_checkmate(): return "Checkmate"
        elif self.board.is_check(): return "Check"
        elif self.board.is_stalemate(): return "Stalemate"

    def offer_draw(self, sender_id):
        '''Offer a draw'''
        self.drawoffer = sender_id

    def reject_draw(self):
        '''Offer rejected either explicitly or when a move is made'''
        self.drawoffer = None

    # Return an image
    def print_board(self, chat_id):
        '''Sends fen to renderer class to draw current chessboard'''
        renderer = Renderer(self.board.turn)
        filename = './matches/{}.jpg'.format('tgchessbot_'+str(chat_id))
        fen = self.board.fen().split()[0]
        img = renderer.draw_fen(fen).save(filename, "JPEG")
        return filename
