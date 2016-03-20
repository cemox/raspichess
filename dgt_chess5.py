# -*- coding: utf-8 -*-
# asyncdgt init file modified
# no timer usage, player has to lift the pieces

import asyncio
import asyncdgt
import logging
import sys
import serial
import time
import chess
import chess.uci
import serial.tools.list_ports
from movegentest import getcell

pieceup = piecedown = -1
movedpiece = -1
fromsq = tosq = -1
count = 0

realmove = []

mylist = []
mydict = {}

PIECESET = {
    0x01: "White Pawn",
    0x02: "White Rook",
    0x03: "White Knight",
    0x04: "WHite Bishop",
    0x05: "White King",
    0x06: "White Queen",
    0x07: "Black Pawn",
    0x08: "Balck Rook",
    0x09: "Black Knight",
    0x0a: "Black Bishop",
    0x0b: "Black King",
    0x0c: "Black Queen",
}


def initchess():
    global newgame
    global chess_board
    global engine
    global info_handler
    chess_board = chess.Board()
    engine = chess.uci.popen_engine("./stockfish")
    engine.uci()
    info_handler = chess.uci.InfoHandler()
    engine.info_handlers.append(info_handler)
    print(engine.name)
    engine.setoption({'MultiPV': 3})
    chess_board.reset()
    count = 0

    while engine.isready():
        end

if __name__ == "__main__":

    initchess()

    dgt_board = asyncdgt.Board()
    #oldboard = asyncdgt.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
    loop = asyncio.get_event_loop()
    dgt = asyncdgt.auto_connect(loop, ["/dev/ttyUSB0"])

    @dgt.on("connected")
    def on_connected(port):
        print("Board connected to {0}!".format(port))

    @dgt.on("disconnected")
    def on_disconnected():
        print("Board disconnected!")

    @dgt.on("board")
    def on_board(dgtboard):
        a = dgtboard.board_fen()
        if a == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR":
            newgame = True
            print("--------")
            print("New Game")
            print("--------")
            initchess()
        else:
            newgame = False
        pass

    @dgt.on("update")
    def on_update(sqr, pcs, was):
        global bestmove
        global pieceup
        global piecedown
        global movedpiece
        global realmove
        global fromsq
        global tosq
        global movecomplete
        global movelegal
        global count
        global mydict, mylist
        movecomplete = False
        movelegal = False
        mymove = ""
        print("---------------------------")
        print("COUNT = ", count)

#register events
        mylist.append(sqr)
        mylist.append(pcs)
        mylist.append(was)
        mydict[count] = mylist
        mylist = []

        if (pcs == 0):  # piece up
            fromsq = sqr  # then source square is obvious
            pieceup = was
            if count == 0:
                movedpiece = pieceup
            #print("Lifted = ", PIECESET[pieceup])
            #print("Moved = ", PIECESET[movedpiece])
            realmove.append(getcell(fromsq))
        else:
            tosq = sqr  # otherwise piece down on the target square
            piecedown = pcs
            #print("Placed = ", PIECESET[piecedown])
            realmove.append(getcell(tosq))

        count += 1

        if piecedown == movedpiece and pcs > 0:  # then move is complete
            movecomplete = True
            count = 0
            mydict = {}

        if movecomplete:
            xmove = realmove[0] + realmove[-1]
            mymove = chess.Move.from_uci(xmove.lower())
            print("Move is = ", mymove)
            realmove = []

# is white playing
        if chess_board.turn:
#yes
#is move completed?
            if movecomplete:
#is it legal? check according to the color
                if mymove in chess_board.legal_moves:
                    print("** Move is legal **")
                    chess_board.push_uci(mymove.uci())
                    movelegal = True
                else:
                    print("** Move is illegal **")
                    movelegal = False
#engine play
            if movecomplete and movelegal:
                engine.position(chess_board)
                print("**** Stockfish ****")
                print("**** Thinking ****")
                bestmove, ponder = engine.go(movetime=2000)
                print("Stockfish plays = ", bestmove)
        else:
#no blak's playing
#is move completed?
            if movecomplete:
                print("move complete")
                if mymove in chess_board.legal_moves:
                    print("** legal **")
                    movelegal = True
                    if (mymove == bestmove):
                        chess_board.push_uci(mymove.uci())
                        print("---------")
                        print("YOUR MOVE")
                        print("---------")
                    else:
                        print("This is not my move!")
                else:
                    print("** illegal move **")
                    movelegal = False

        if(chess_board.is_check()):
            print("Check!")

        if(chess_board.is_checkmate()):
            print("Checkmate!")

        #oldboard.state = dgt_board.state.copy()

    # Get some information.
    print("Version:", loop.run_until_complete(dgt.get_version()))
    print("Serial:", loop.run_until_complete(dgt.get_serialnr()))

    # Run the event loop.
    print("Running event loop ...")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        dgt.close()

        pending = asyncio.Task.all_tasks(loop)
        loop.run_until_complete(asyncio.gather(*pending))
        loop.close()
#return 0