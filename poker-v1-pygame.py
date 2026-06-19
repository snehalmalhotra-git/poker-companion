from enum import Enum
import pygame

pygame.init()

clock = pygame.time.Clock()

WIDTH = 1280
HEIGHT = 720

screen = pygame.display.set_mode((WIDTH, HEIGHT))

font = pygame.font.SysFont(None, 36)

pot = 0
current_bet = 20
last_raise_size = 20
pending_raise_amount = 20
selected_winner = None
hand_complete = False
selected_winners = []
dealer_position = 0
small_blind = 10
big_blind = 20
action_log = []
current_player = 0
action_count = 0

last_raiser = None

class GameState(Enum):
    PREFLOP = 1
    FLOP = 2
    TURN = 3
    RIVER = 4
    SHOWDOWN = 5

current_state = GameState.PREFLOP


running = True

players = [
    {"name":"Player 1","chips":1000,"folded":False,"bet":0,"all_in":False,"eliminated": False},
    {"name":"Player 2","chips":1000,"folded":False,"bet":0,"all_in":False,"eliminated": False},
    {"name":"Player 3","chips":1000,"folded":False,"bet":0,"all_in":False,"eliminated": False},
    {"name":"Player 4","chips":1000,"folded":False,"bet":0,"all_in":False,"eliminated": False},
    {"name":"Player 5","chips":1000,"folded":False,"bet":0,"all_in":False,"eliminated": False},
    {"name":"Player 6","chips":1000,"folded":False,"bet":0,"all_in":False,"eliminated": False},
]

def first_to_act_preflop():
    return (dealer_position + 3) % len(players)

def award_pot(winner_index):
    global pot
    global hand_complete

    players[winner_index]["chips"] += pot

    print(
        f"{players[winner_index]['name']} wins {pot}"
    )

    pot = 0
    check_eliminations()

    hand_complete = True

def reset_betting_round():
    global current_bet

    current_bet = 0
    global last_raise_size
    last_raise_size = 20

    global last_raiser
    global pending_raise_amount

    last_raiser = None
    print("Last raiser after reset =", last_raiser)
    pending_raise_amount = 20
    print("Pending raise =", pending_raise_amount)

    print("Resetting betting round")
    print("Last raiser =", last_raiser)

    for player in players:
        player["bet"] = 0

def advance_state():
    global current_state
    global current_player

    if current_state == GameState.PREFLOP:
        current_state = GameState.FLOP
        reset_betting_round()
        current_player = first_postflop_player()

    elif current_state == GameState.FLOP:
        current_state = GameState.TURN
        reset_betting_round()
        current_player = first_postflop_player()

    elif current_state == GameState.TURN:
        current_state = GameState.RIVER
        reset_betting_round()
        current_player = first_postflop_player()

    elif current_state == GameState.RIVER:
        current_state = GameState.SHOWDOWN
        reset_betting_round()

    elif current_state == GameState.SHOWDOWN:
        reset_hand()

    print(current_state)

def reset_hand():
    global pot
    global current_bet
    global action_count
    global current_player
    global current_state

    pot = 0
    current_bet = 20
    action_count = 0
    current_player = 0
    current_state = GameState.PREFLOP

    for player in players:
        player["folded"] = False
        player["all_in"] = False
        player["bet"] = 0

    action_log.clear()

def next_player():
    global current_player
    global action_count

    
    action_count += 1
    
    active_player_count = sum(
        1 for p in players
        if not p["folded"]
    )
    if active_player_count <= 1:
        print("Hand over")
        reset_hand()
        return

    current_player = (current_player + 1) % len(players)
    
    while (players[current_player]["folded"] 
        or players[current_player]["eliminated"]):
        current_player = (current_player + 1) % len(players)
        
    # if action_count >= active_player_count:
    #     action_count = 0
    #     advance_state()

    if betting_round_complete():
        action_count = 0
        advance_state()

    print(players[current_player]["name"])
    print("Last raiser:", last_raiser)
    
def betting_round_complete():

    if last_raiser is None:
        active_player_count = sum(
            1 for p in players
            if not p["folded"]
        )

        return action_count >= active_player_count

    all_matched = all(
        p["folded"] or p["bet"] == current_bet
        for p in players
    )

    return current_player == last_raiser and all_matched

def call_action():
    global pot

    diff = current_bet - players[current_player]["bet"]

    player = players[current_player]

    if diff >= player["chips"]:

        pot += player["chips"]
        player["bet"] += player["chips"]

        player["chips"] = 0
        player["all_in"] = True

    else:

        player["chips"] -= diff
        player["bet"] += diff

        pot += diff

    action_log.append(
        f"{players[current_player]['name']}: call"
    )

    next_player()

def raise_action():
    global current_bet
    global pot
    global last_raiser
    global last_raise_size

    raise_amount = pending_raise_amount
    if raise_amount < last_raise_size:
        print("Raise too small")
        return

    new_bet = current_bet + raise_amount

    diff = new_bet - players[current_player]["bet"]

    players[current_player]["chips"] -= diff
    players[current_player]["bet"] = new_bet

    current_bet = new_bet
    last_raise_size = raise_amount
    pot += diff

    last_raiser = current_player
    print("RAISER SET TO:", last_raiser)
    print("Last raise size:", last_raise_size)
    

    action_log.append(
        f"{players[current_player]['name']}: raise to {current_bet}"
    )
    

    next_player()

def all_in_action():
    global pot
    global current_bet

    player = players[current_player]

    amount = player["chips"]

    player["bet"] += amount
    pot += amount

    player["chips"] = 0
    player["all_in"] = True

    if player["bet"] > current_bet:
        current_bet = player["bet"]

    action_log.append(
        f"{player['name']}: ALL IN"
    )

    next_player()

def check_eliminations():
    for player in players:

        if (
            player["chips"] == 0
            and not player["all_in"]
        ):
            player["eliminated"] = True

def fold_action():
    players[current_player]["folded"] = True
    action_log.append(f"{players[current_player]['name']}: fold")
    next_player()

def check_eliminations():
    for player in players:

        if player["chips"] <= 0:
            player["eliminated"] = True

            print(
                f"{player['name']} eliminated"
            )

def next_hand():
    global hand_complete

    hand_complete = False

    rotate_dealer()
    reset_hand()
    post_blinds()

def rotate_dealer():
    global dealer_position

    dealer_position = (
        dealer_position + 1
    ) % len(players)

    while players[dealer_position]["eliminated"]:
        dealer_position = (
            dealer_position + 1
        ) % len(players)

def small_blind_position():
    return (dealer_position + 1) % len(players)

def big_blind_position():
    return (dealer_position + 2) % len(players)

def post_blinds():
   
    global pot
    global current_bet
    global current_player
    print("POSTING BLINDS")
    print("Current player before:", current_player)
    sb = small_blind_position()
    bb = big_blind_position()

    players[sb]["chips"] -= small_blind
    players[sb]["bet"] = small_blind

    players[bb]["chips"] -= big_blind
    players[bb]["bet"] = big_blind

    pot += small_blind + big_blind

    current_bet = big_blind
    current_player = first_to_act_preflop()
    print("Current player after:", current_player)
    print("Dealer:", dealer_position)
    print("SB:", small_blind_position())
    print("BB:", big_blind_position())
    print("First:", first_to_act_preflop())

def start_first_hand():
    post_blinds()

def first_postflop_player():
    player = (dealer_position + 1) % len(players)

    while (
        players[player]["folded"]
        or players[player]["eliminated"]
    ):
        player = (player + 1) % len(players)

    return player

def check_action():
    if players[current_player]["bet"] != current_bet:
        print("Connot check")
        return
    
    action_log.append(f"{players[current_player]['name']}: check")
    next_player()

def toggle_winner(index):
    if index in selected_winners:
        selected_winners.remove(index)
    else:
        selected_winners.append(index)
    
def split_pot():
    global pot
    global hand_complete

    if len(selected_winners) == 0:
        print("No winners selected")
        return

    share = pot // len(selected_winners)

    for winner in selected_winners:
        players[winner]["chips"] += share

    pot = 0

    hand_complete = True

    selected_winners.clear()
    check_eliminations()

start_first_hand()

seat_positions = [
        (1070, 360),  # P1 right
        (850, 620),   # P2 bottom-right
        (430, 620),   # P3 bottom-left
        (210, 360),   # P4 left
        (430, 100),   # P5 top-left
        (850, 100)    # P6 top-right
    ]

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_SPACE:
                advance_state()
            if event.key == pygame.K_k:
                check_action()
            if event.key == pygame.K_f:
                fold_action()
            if event.key == pygame.K_c:
                call_action()
            if event.key == pygame.K_r:
                raise_action()
            if event.key == pygame.K_UP:
                pending_raise_amount += 20

            if event.key == pygame.K_DOWN:
                pending_raise_amount = max(20, pending_raise_amount - 20)
            if event.key == pygame.K_a:
                all_in_action()

            if current_state == GameState.SHOWDOWN:
                if event.key == pygame.K_1:
                    toggle_winner(0)

                if event.key == pygame.K_2:
                    toggle_winner(1)

                if event.key == pygame.K_3:
                    toggle_winner(2)

                if event.key == pygame.K_4:
                    toggle_winner(3)

                if event.key == pygame.K_5:
                    toggle_winner(4)

                if event.key == pygame.K_6:
                    toggle_winner(5)

                if event.key == pygame.K_RETURN:
                    split_pot()

            if event.key == pygame.K_n:
                if hand_complete:
                    next_hand()
    screen.fill((0, 0, 0))

    pygame.draw.ellipse(
    screen,
    (20, 100, 20),
    (250, 120, 780, 450)
)
    for i, entry in enumerate(action_log[-3:]):
        log_text = font.render(entry, True, (255, 255, 255))
        screen.blit(log_text, (20, 500 + i * 30))

    for i, (x, y) in enumerate(seat_positions):

        if players[i]["eliminated"]:
            color = (20,20,20)

        elif players[i]["folded"]:
            color = (120, 40, 40)
       
        elif i == current_player:
            color = (255, 255, 0)
        
        elif players[i]["all_in"]:
             color = (255, 0, 0)
        
        else:
            color = (100, 100, 100)


        pygame.draw.circle(
            screen,
            color,
            (int(x), int(y)),
            35
        )

        name_text = font.render(
            players[i]["name"],
            True,
            (255,255,255)
        )

        screen.blit(
            name_text,
            (x - 30, y - 10)
        )
       
        chip_text = font.render(
            str(players[i]["chips"]),
            True,
            (255,255,255)
        )

        screen.blit(chip_text, (x - 20, y + 40))

        if i == small_blind_position():
            sb_text = font.render(
                "SB",
                True,
                (255,255,255)
            )

            screen.blit(
                sb_text,
                (x - 50, y - 50)
            )

        if i == big_blind_position():
            bb_text = font.render(
                "BB",
                True,
                (255,255,255)
            )

            screen.blit(
                bb_text,
                (x + 30, y - 50)
            )

        if i == dealer_position:
            dealer_text = font.render(
                "D",
                True,
                (255,255,255)
            )

            screen.blit(
                dealer_text,
                (x + 40, y - 10)
            )


    state_text = font.render(
        f"State: {current_state.name}",
        True,
        (255,255,255)
    )
    screen.blit(state_text, (20,20))

    player_text = font.render(
        f"Current Turn: {players[current_player]['name']}",
        True,
        (255,255,255)
    )
    screen.blit(player_text, (20,60))

    action_text = font.render(
        f"Actions: {action_count}",
        True,
        (255,255,255)
    )
    screen.blit(action_text, (20,220))

    pot_text = font.render(f"Pot: {pot}", True, (255, 255, 255))
    bet_text = font.render(f"Current Bet: {current_bet}", True, (255, 255, 255))

    screen.blit(pot_text, (20, 140))
    screen.blit(bet_text, (20, 180))

    raise_text = font.render(
    f"Raise Amount: {pending_raise_amount}",
    True,
    (255,255,255)
    )

    screen.blit(raise_text, (20, 260))

    last_raise_text = font.render(
        f"Min Raise: {last_raise_size}",
        True,
        (255,255,255)
)

    screen.blit(last_raise_text, (20, 300))

    selected_text = font.render(
        f"Winners: {selected_winners}",
        True,
        (255,255,255)
    )

    screen.blit(selected_text, (20, 420))

    if current_state == GameState.SHOWDOWN:
        winner_text = font.render(
        "Press 1-6 to select winner",
        True,
        (255,255,255)
        )

        screen.blit(winner_text, (20, 340))

    if hand_complete:
        next_hand_text = font.render(
            "Press N for Next Hand",
            True,
            (255,255,255)
        )

        screen.blit(next_hand_text, (20, 380))

    pygame.display.flip()

    clock.tick(60)
    
pygame.quit()
