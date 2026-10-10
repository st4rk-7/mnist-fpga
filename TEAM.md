# TEAM.md — how we work together

## 1. Roles (fill in names at the kickoff meeting)
| Role | Name | Branch | Owns |
|---|---|---|---|
| Python and testing | _____ | `python` | training, 8-bit conversion, golden model, `.hex` export, compare testbenches |
| Compute | _____ | `compute` | MAC unit, ReLU + shift + clip, argmax |
| Control and memories | _____ | `control` | controller FSM, counters, all memories, top module |
| Board and display | _____ | `board` | `.xdc` constraints, debounce, seven-segment, LEDs, VGA |

Everyone must be able to explain **every** block (individual viva).

## 2. Kickoff meeting (90 min)
| Time | What | Output |
|---|---|---|
| 15 min | Pick roles | names in the table above |
| 30 min | Draw the block diagram together. Compute one neuron by hand (below). | everyone can draw it from memory |
| 20 min | Freeze: argmax tie rule, `.hex` file names and formats | written in `docs/PROJECT_CONTEXT.md` §9 |
| 10 min | Read the rules in section 4 together | everyone agrees |
| 15 min | Each person opens one GitHub issue: their first task | 4 issues |

**Hand example (3 inputs instead of 784):**
pixels `100, 50, 127`, weights `20, -10, 5`, bias `1000`
→ acc = 1000 + 2000 − 500 + 635 = **3135** → ReLU 3135 → `>> 11` = **1** → clip → **1**.
Then discuss: what if acc is negative? What if acc is 400,000?

## 3. First task for each role (week 1)
| Role | Task | Done means |
|---|---|---|
| Python | Train 784-32-10, convert to 8-bit | accuracy > 95% printed |
| Compute | `rtl/mac.v` skeleton + `tb/tb_mac.v` | testbench prints PASS |
| Control | `rtl/top.v` with empty stub modules for every block | `iverilog` compiles with no errors |
| Board | `.xdc` file + LED blink on the board | LED blinks |

## 4. Rules
- **Branches:** work on your role branch. Merge to `main` at least once a week, only when your testbench prints PASS.
- **`main` always passes:** before merging, run *all* testbenches, not only yours.
- **Review:** every merge is reviewed by someone from another role. The reviewer must be able to explain the code before approving.
- **Decisions:** any change to ports, formats or addresses is written in `docs/PROJECT_CONTEXT.md` §9 **before** anyone codes it.
- **Tasks:** one GitHub issue per task, with an owner and a "done means..." line.
- **Blocked?** Post it in the group chat the same day. Don't wait for Friday.
- **Commits:** small, clear messages. Never commit `build/` or Vivado project folders.

## 5. Friday meeting (15 min)
1. Each person: what I did, what is next, what is blocking me (1 min each).
2. One block is explained by someone who did **not** write it (5 min).
3. Update the issues.

## 6. Reviewer rotation
| Week | Compute → | Control → | Board → | Python → |
|---|---|---|---|---|
| 1, 4 | Control | Board | Python | Compute |
| 2, 5 | Board | Python | Compute | Control |
| 3, 6 | Python | Compute | Control | Board |

(Read: in week 1, Control reviews Compute's code.)

## 7. Who waits for whom
```
python ──► .hex files ──► control (ROMs need them)
compute ─► independent (testbench with hand-made numbers first)
board ───► independent (LED blink, VGA test pattern)
```
Python is on the critical path early, Control is on it late. If someone is stuck, help those two first.
