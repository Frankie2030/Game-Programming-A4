## ✅ **Checklist**#### **1 pt — Random Baseline**

* [x] Implement a **random AI### **IV. Menu & Continue System (1 pt total)**

* [x] Provide a **functional Main Menu** with:

  * [x] "Start Game"
  * [x] "Continue" (Resume last saved session)
  * [x] "Quit" or "Settings"
* [x] Implement **state transitions**:
  `Splash → Menu → Gameplay → Pause → End (Win/Lose/Draw) → Menu`
* [x] **Continue** reliably restores the previous game session (local or online).lects **only legal moves**.
* [x] Ensure it **never crashes** and respects **turn/time limits**.

#### **3 pts — Correct Implementation of Search**

* [x] Implement **Minimax**, **Alpha–Beta Pruning**, or **MCTS** correctly:

  * [x] Proper **terminal evaluation** and **utility propagation**.
  * [x] **Alpha–Beta** actually prunes nodes where expected.
  * [x] **MCTS** uses a documented **UCT/PUCT** formula and valid rollouts.
  * [x] AI expands **no illegal nodes**.
* [x] Validate correctness via debug logs or tests (show state expansions, prunes, etc.).

#### **1 pt — Multiple Difficulty Levels**

* [x] Expose **≥2 difficulty modes** (e.g., by changing depth, time limit, or rollouts).
* [x] Difficulty must **visibly affect AI strength** (e.g., "Easy" plays worse than "Hard").
* [x] Display difficulty selection in menu or before match start.ept & Rules**

* [x] Choose a **non-trivial strategic board game** (e.g., Connect 4+, Othello, Gomoku, Tablut, small TBS).
* [x] Clearly document in **README.md**:

  * [x] Objective of the game.
  * [x] Win/Lose/Draw conditions.
  * [x] Turn order and legal moves.
  * [x] Scoring (if applicable).
  * [x] Edge cases (illegal moves, stalemate, etc.).
* [x] The game must be **playable without crashes** and respect all rules.

---

### **II. Artificial Intelligence (5 pts total)**

#### **1 pt — Random Baseline**

* [ ] Implement a **random AI** that selects **only legal moves**.
* [ ] Ensure it **never crashes** and respects **turn/time limits**.

#### **3 pts — Correct Implementation of Search**

* [ ] Implement **Minimax**, **Alpha–Beta Pruning**, or **MCTS** correctly:

  * [ ] Proper **terminal evaluation** and **utility propagation**.
  * [ ] **Alpha–Beta** actually prunes nodes where expected.
  * [ ] **MCTS** uses a documented **UCT/PUCT** formula and valid rollouts.
  * [ ] AI expands **no illegal nodes**.
* [ ] Validate correctness via debug logs or tests (show state expansions, prunes, etc.).

#### **1 pt — Multiple Difficulty Levels**

* [ ] Expose **≥2 difficulty modes** (e.g., by changing depth, time limit, or rollouts).
* [ ] Difficulty must **visibly affect AI strength** (e.g., “Easy” plays worse than “Hard”).
* [ ] Display difficulty selection in menu or before match start.

---

### **III. Networking (4 pts total)**

#### **Connection & Session**

* [x] Two players can **connect from different machines** over the network.
* [x] Include **Host/Join** or **Matchmaking** screen (basic lobby).

#### **Synchronization & Validation**

* [x] Maintain **authoritative game state** (server or host-based).
* [x] **Validate moves server-side** and **reject illegal moves**.
* [x] Synchronize **turns, scores, and game events** for both clients.

#### **Error Handling & Stability**

* [x] Handle **disconnects gracefully** (timeout messages, no softlocks).
* [x] Optionally support **reconnection**.
* [x] Ignore **malformed messages**, sanitize all inputs (avoid code injection).
* [x] Latency ≤ ~200 ms round-trip should still yield a smooth experience.

---

### **IV. Menu & Continue System (1 pt total)**

* [ ] Provide a **functional Main Menu** with:

  * [ ] “Start Game”
  * [ ] “Continue” (Resume last saved session)
  * [ ] “Quit” or “Settings”
* [ ] Implement **state transitions**:
  `Splash → Menu → Gameplay → Pause → End (Win/Lose/Draw) → Menu`
* [ ] **Continue** reliably restores the previous game session (local or online).

---

## ⭐ **Bonus Points (Optional, up to +2 pts)**

### **Machine Learning Integration**

* [ ] Train a model from **self-play** or **human gameplay data** (policy/value net).
* [ ] Integrate it into AI decision-making (e.g., hybrid Minimax + ML evaluation).
* [ ] Document your ML setup clearly in README.md.

### **Multiple AI Opponents**

* [ ] Support **3-player or more** AI variants with working turn order.
* [ ] Ensure fairness and clear win conditions for multi-AI scenarios.

---

## 🧩 **Deliverables Checklist**

* [ ] Full **source code + assets**.
* [ ] A detailed **README.md** containing:

  * [ ] Game rules & objectives.
  * [ ] How to run (local + network).
  * [ ] AI method & parameters.
  * [ ] How to host/join games (ports, NAT, relay).
  * [ ] Known issues or limitations.
* [ ] All dependencies included or installable easily.

---

## 💯 **Grading Summary**

| Category        | Criteria                                                                        | Points        |
| --------------- | ------------------------------------------------------------------------------- | ------------- |
| AI              | Random baseline (1), Correct Minimax/Alpha–Beta/MCTS (3), Difficulty levels (1) | **5**         |
| Networking      | Online PvP, Lobby, Sync, Validation, Disconnect handling                        | **4**         |
| Menu + Continue | Menu and Resume system                                                          | **1**         |
| **Total**       | **Perfect Implementation**                                                      | **10 / 10**   |
| **Bonus**       | ML integration / Multiple AIs                                                   | **+ up to 2** |

---

Would you like me to make a **scoring checklist template (Markdown or Excel)** so you can self-grade your implementation item by item (e.g., checkboxes, weights, and comments column)?
