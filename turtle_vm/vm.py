import re
import pygame
import time

from math import radians, sin, cos

# ---------------------------------------------------------------------
screen = pygame.display.set_mode((1200,800))

# TODO?: implement a true byte-indexed memory
memory = [0] * (32 * 1024 * 1024)
regs = {}
instr = {}
labels = {}

colors = [
    0xFFFFFF, 0xFFFF00, 0x1CE6FF, 0xFF34FF, 0xFF4A46, 0x008941, 0x006FA6, 0xA30059,
    0xFFDBE5, 0x7A4900, 0x0000A6, 0x63FFAC, 0xB79762, 0x004D43, 0x8FB0FF, 0x997D87,
    0x5A0007, 0x809693, 0xFEFFE6, 0x1B4400, 0x4FC601, 0x3B5DFF, 0x4A3B53, 0xFF2F80,
    0x61615A, 0xBA0900, 0x6B7900, 0x00C2A0, 0xFFAA92, 0xFF90C9, 0xB903AA, 0xD16100,
    0xDDEFFF, 0x000035, 0x7B4F4B, 0xA1C299, 0x300018, 0x0AA6D8, 0x013349, 0x00846F,
    0x372101, 0xFFB500, 0xC2FFED, 0xA079BF, 0xCC0744, 0xC0B9B2, 0xC2FF99, 0x001E09,
    0x00489C, 0x6F0062, 0x0CBD66, 0xEEC3FF, 0x456D75, 0xB77B68, 0x7A87A1, 0x788D66,
    0x885578, 0xFAD09F, 0xFF8A9A, 0xD157A0, 0xBEC459, 0x456648, 0x0086ED, 0x886F4C,
    0x34362D, 0xB4A8BD, 0x00A6AA, 0x452C2C, 0x636375, 0xA3C8C9, 0xFF913F, 0x938A81,
    0x575329, 0x00FECF, 0xB05B6F, 0x8CD0FF, 0x3B9700, 0x04F757, 0xC8A1A1, 0x1E6E00,
    0x7900D7, 0xA77500, 0x6367A9, 0xA05837, 0x6B002C, 0x772600, 0xD790FF, 0x9B9700,
    0x549E79, 0xFFF69F, 0x201625, 0x72418F, 0xBC23FF, 0x99ADC0, 0x3A2465, 0x922329,
    0x5B4534, 0xFDE8DC, 0x404E55, 0x0089A3, 0xCB7E98, 0xA4E804, 0x324E72, 0x6A3A4C,
    0x83AB58, 0x001C1E, 0xD1F7CE, 0x004B28, 0xC8D0F6, 0xA3A489, 0x806C66, 0x222800,
    0xBF5650, 0xE83000, 0x66796D, 0xDA007C, 0xFF1A59, 0x8ADBB4, 0x1E0200, 0x5B4E51,
    0xC895C5, 0x320033, 0xFF6832, 0x66E1D3, 0xCFCDAC, 0xD0AC94, 0x7ED379, 0x012C58
]

# ---------------------------------------------------------------------
def forward(distance):
    curr_x, curr_y, curr_theta = regs['$x'], regs['$y'], regs['$t']
    nx = curr_x + distance * cos(radians(curr_theta))
    ny = curr_y + distance * sin(radians(curr_theta))
    ci = regs['$s7'] % len(colors)

    if regs['$p'] == 1:
        pygame.draw.lines(screen, colors[ci], False, [(curr_x, curr_y), (nx, ny)], 1)
        pygame.display.flip()

    regs['$x'] = nx
    regs['$y'] = ny

def rotate(angle):
    regs['$t'] = (regs['$t'] + angle + 360) % 360

def clearscreen():
    screen.fill((0,0,0))
    pygame.display.flip()

# ---------------------------------------------------------------------
def init_regs():
    regs['$zero'] = 0
    regs['$at'] = 0
    regs['$ra'] = 0
    regs['$gp'] = 0
    regs['$fp'] = 8 * len(memory)
    regs['$sp'] = regs['$fp']
    regs['$ra'] = 0
    regs['$pc'] = 0

    regs['$x'] = 600
    regs['$y'] = 700
    regs['$t'] = 270
    regs['$p'] = 1

    for i in xrange(2):
        regs['$v' + str(i)] = 0
    for i in xrange(8):
        regs['$a' + str(i)] = 0
    for i in xrange(8):
        regs['$s' + str(i)] = 0
    for i in xrange(32):
        regs['$f' + str(i)] = 0.0
    # TODO: Implement a proper register allocation scheme to reduce the need
    #       for so many temporary registers.
    for i in xrange(1000):
        regs['$t' + str(i)] = 0

# ---------------------------------------------------------------------
def _add(r1,r2,r3):
    regs[r1] = regs[r2] + regs[r3]
def _sub(r1,r2,r3):
    regs[r1] = regs[r2] - regs[r3]
def _addi(r1,r2,C):
    regs[r1] = regs[r2] + int(C)
def _mult(r1,r2):
    regs[r1] = regs[r1] * regs[r2]
def _div(r1,r2):
    regs[r1] = float(regs[r1]) / regs[r2]

def _lw(r1,C,r2):
    regs[r1] = memory[(regs[r2] + int(C))/8]
def _sw(r1,C,r2):
    memory[(regs[r2] + int(C))/8] = regs[r1]
def _li(r1,C):  
    regs[r1] = int(C)

def _and(r1,r2,r3):
    regs[r1] = regs[r2] & regs[r3]
def _or(r1,r2,r3):
    regs[r1] = regs[r2] | regs[r3]
def _andi(r1,r2,C): 
    regs[r1] = regs[r2] & int(C)
def _ori(r1,r2,C):
    regs[r1] = regs[r2] | int(C)
def _xor(r1,r2,r3):
    regs[r1] = regs[r2] ^ regs[r3]
def _not(r1,r2):
    regs[r1] = ~ regs[r2]

def _slt(r1,r2,r3):
    regs[r1] = int(regs[r2] < regs[r3])
def _slti(r1,r2,C): 
    regs[r1] = int(regs[r2] < int(C))

def _beql(r1,r2,label):
    regs['$pc'] = labels[label] if regs[r1] == regs[r2] else regs['$pc']
def _bnel(r1,r2,label):
    regs['$pc'] = labels[label] if regs[r1] != regs[r2] else regs['$pc']
def _jr(r1):
    regs['$pc'] = regs[r1]
def _jl(label):
    regs['$pc'] = labels[label]
def _jal(r1):
    regs['$ra'] = regs['$pc']
    regs['$pc'] = regs[r1]
def _jall(label):
    regs['$ra'] = regs['$pc']
    regs['$pc'] = labels[label]

def _fd(r1):
    forward(regs[r1])
def _rt(r1):
    rotate(regs[r1])
def _pu():
    regs['$p'] = 1
def _pd():
    regs['$p'] = 0
def _cs():
    clearscreen()

def _li_s(r1,C):
    regs[r1] = float(C)

# ---------------------------------------------------------------------
instr['add'] = _add
instr['sub'] = _sub
instr['addi'] = _addi
instr['mult'] = _mult
instr['div']  = _div

instr['lw'] = _lw
instr['sw'] = _sw
instr['li'] = _li

instr['and']  = _and
instr['or']   = _or
instr['andi'] = _andi
instr['ori']  = _ori
instr['xor']  = _xor
instr['not']  = _not

instr['slt']  = _slt
instr['slti'] = _slti

instr['beql'] = _beql
instr['bnel'] = _bnel
instr['jr'] = _jr
instr['jl'] = _jl
instr['jal'] = _jal
instr['jall'] = _jall

instr['fd'] = _fd
instr['rt'] = _rt
instr['pu'] = _pu
instr['pd'] = _pd
instr['cs'] = _cs

instr['li.s'] = _li_s

# ---------------------------------------------------------------------
def preprocess(s):
    i = 0
    r = []

    temp = [re.findall(r"[\w|\$|\-|\:|\.]+", line) for line in s.split('\n') if len(line) > 0]

    for line in temp:
        if len(line) == 0:
            continue
        elif line[0][-1] == ':':
            labels[line[0][:-1]] = i
        else:
            r.append(line)
            i += 1

    return r

# ---------------------------------------------------------------------
def start(lines):
    init_regs()
    while regs['$pc'] < len(lines):
        line = lines[regs['$pc']]
        regs['$pc'] += 1
        run(line)

def run(line):
    cmd = line[0]
    instr[cmd](*line[1:])
