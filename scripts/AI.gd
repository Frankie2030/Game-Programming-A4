extends Node

class EvalMove:
    var x:int
    var y:int
    var z:int
    var score:int

@export var max_depth:int = 2
@export var beam_width:int = 24

var board:Node # set by GameManager

func choose_move(player:int)->Vector3i:
    var candidates := _generate_candidates()
    if candidates.is_empty():
        return Vector3i(board.size/2, board.size/2, board.size/2)
    var best := EvalMove.new(); best.score = -INF
    for mv in candidates:
        var s := _score_after(mv.x,mv.y,mv.z, player, 0, -INF, INF)
        if s > best.score:
            best = EvalMove.new(); best.x = mv.x; best.y = mv.y; best.z = mv.z; best.score = s
    return Vector3i(best.x, best.y, best.z)

func _score_after(x:int,y:int,z:int, p:int, depth:int, alpha:int, beta:int)->int:
    if not board.place_stone(x,y,z,p):
        return -999999
    var win := board.check_win_from(x,y,z,p)
    if win:
        board.grid[z][y][x] = 0
        board.stones.pop_back(); board.stone_colors.pop_back(); board._rebuild_stones()
        return 100000 - depth
    if depth >= max_depth:
        var sc := _heuristic(p)
        board.grid[z][y][x] = 0
        board.stones.pop_back(); board.stone_colors.pop_back(); board._rebuild_stones()
        return sc
    # opponent
    var op := (p==1)?2:1
    var best := 999999
    var moves := _generate_candidates()
    for mv in moves:
        var s := _max_after(mv.x,mv.y,mv.z, op, depth+1, alpha, beta)
        if s < best:
            best = s
        beta = mini(beta, best)
        if beta <= alpha: break
    board.grid[z][y][x] = 0
    board.stones.pop_back(); board.stone_colors.pop_back(); board._rebuild_stones()
    return best

func _max_after(x:int,y:int,z:int, p:int, depth:int, alpha:int, beta:int)->int:
    if not board.place_stone(x,y,z,p):
        return -999999
    var win := board.check_win_from(x,y,z,p)
    if win:
        board.grid[z][y][x] = 0
        board.stones.pop_back(); board.stone_colors.pop_back(); board._rebuild_stones()
        return -100000 + depth
    if depth >= max_depth:
        var sc := -_heuristic((p==1)?2:1)
        board.grid[z][y][x] = 0
        board.stones.pop_back(); board.stone_colors.pop_back(); board._rebuild_stones()
        return sc
    var op := (p==1)?2:1
    var best := -999999
    var moves := _generate_candidates()
    for mv in moves:
        var s := _score_after(mv.x,mv.y,mv.z, op, depth+1, alpha, beta)
        if s > best:
            best = s
        alpha = maxi(alpha, best)
        if beta <= alpha: break
    board.grid[z][y][x] = 0
    board.stones.pop_back(); board.stone_colors.pop_back(); board._rebuild_stones()
    return best

func _heuristic(player:int)->int:
    # Very simple pattern-based count around last stones.
    var score := 0
    var dirs = [Vector3i(1,0,0), Vector3i(0,1,0), Vector3i(0,0,1), Vector3i(1,1,0), Vector3i(1,-1,0), Vector3i(1,0,1), Vector3i(1,0,-1), Vector3i(0,1,1), Vector3i(0,1,-1), Vector3i(1,1,1), Vector3i(1,1,-1), Vector3i(1,-1,1), Vector3i(1,-1,-1)]
    for z in board.size:
        for y in board.size:
            for x in board.size:
                var v := board.grid[z][y][x]
                if v == 0: continue
                for d in dirs:
                    var c := _line_count(x,y,z,d,v)
                    if v==player:
                        score += c*c
                    else:
                        score -= c*c
    return score

func _line_count(x:int,y:int,z:int,d:Vector3i, player:int)->int:
    var c := 0
    var nx := x; var ny := y; var nz := z
    for i in 5:
        if nx<0 or ny<0 or nz<0 or nx>=board.size or ny>=board.size or nz>=board.size: break
        if board.grid[nz][ny][nx]==player: c+=1
        nx+=d.x; ny+=d.y; nz+=d.z
    return c

func _generate_candidates()->Array:
    var around := []
    var used := {}
    for z in board.size:
        for y in board.size:
            for x in board.size:
                if board.grid[z][y][x]!=0:
                    for dz in -1:2:
                        for dy in -1:2:
                            for dx in -1:2:
                                var nx := x+dx; var ny := y+dy; var nz := z+dz
                                if nx<0 or ny<0 or nz<0 or nx>=board.size or ny>=board.size or nz>=board.size: continue
                                if board.grid[nz][ny][nx]==0:
                                    var key := Vector3i(nx,ny,nz)
                                    if not used.has(key):
                                        used[key] = true
                                        around.append({"x":nx,"y":ny,"z":nz})
    around.sort_custom(func(a,b):
        var va := abs(a.x - board.size/2) + abs(a.y - board.size/2) + abs(a.z - board.size/2)
        var vb := abs(b.x - board.size/2) + abs(b.y - board.size/2) + abs(b.z - board.size/2)
        return va < vb)
    if around.size() > beam_width:
        around.resize(beam_width)
    return around