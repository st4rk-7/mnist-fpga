# Getting started (do this once)

## 1. Install the tools
| Tool | What for | How |
|---|---|---|
| Git | share code | git-scm.com |
| Icarus Verilog + GTKWave | fast simulation and waveforms | Windows: bleyer.org/icarus (tick GTKWave). Linux: `sudo apt install iverilog gtkwave`. Mac: `brew install icarus-verilog` |
| Python 3 + NumPy | train the network, golden model | python.org, then `pip install numpy` |
| Vivado (free edition) | synthesis, programming the board | AMD/Xilinx website, or use the lab PCs |
| Claude Code | AI tutor in your repo | claude.ai/code (follow the install steps there) |

Check: `iverilog -V`, `python3 -c "import numpy"`, `git --version`.

## 2. Make the team repo
1. One person creates a **private** GitHub repo, e.g. `mnist-accelerator`, and adds the other 3 as collaborators.
2. Copy this whole starter folder into it, commit, push.
3. Everyone clones it.
4. Download Digilent's `Nexys-A7-100T-Master.xdc` into `constraints/`.

## 3. Open Claude Code in the repo folder
```
cd mnist-accelerator
claude
```
It reads `CLAUDE.md` automatically. Good first prompts:

- **"Read CLAUDE.md and docs/PROJECT_CONTEXT.md. Explain the whole project back to me in simple English with a block diagram, so I know you understood."**
- **"Check my tools: run iverilog -V and python3 with numpy. Then make a tiny AND-gate module and testbench to prove simulation works."**
- **"We are in phase 2. Help me plan the Python script that trains the 784-32-10 network and converts it to 8-bit. Explain each step; don't write it all at once."**
- **"I'm the Compute person. Explain how a signed 8x8 MAC with a 24-bit accumulator works, draw the timing, and give me a skeleton with TODOs for rtl/mac.v."**
- **"Write tb/tb_mac.v that tests my MAC against values computed in the testbench and prints PASS or FAIL."**
- **"Review rtl/mac.v. List bugs, latches and signed/unsigned problems, and tell me what hardware each line becomes."**
- **"Ask me 5 viva questions about the MAC unit and mark my answers."**

## 4. Good habits
- One small task per conversation. Start a new chat for a new module.
- Ask "why?" whenever it does something you don't understand. You must explain it in the viva.
- Run the testbench yourself and look at the waves in GTKWave.
- Commit after every passing testbench.
- When you freeze a format or port list, add it to `docs/PROJECT_CONTEXT.md` section 9 so Claude Code and your team both see it.
