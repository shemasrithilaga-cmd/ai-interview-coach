import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import time

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif;
}

.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    border: 1px solid #e94560;
    box-shadow: 0 8px 32px rgba(233,69,96,0.2);
}

.main-header h1 {
    color: #e94560;
    font-size: 2.5rem;
    margin: 0;
}

.main-header p {
    color: #a8b2d8;
    margin: 0.5rem 0 0 0;
}

.card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #0f3460;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.metric-card {
    background: linear-gradient(135deg, #0f3460, #16213e);
    border: 1px solid #e94560;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    box-shadow: 0 4px 16px rgba(233,69,96,0.15);
}

.metric-card h2 {
    color: #e94560;
    font-size: 2rem;
    margin: 0;
}

.metric-card p {
    color: #a8b2d8;
    margin: 0.3rem 0 0 0;
    font-size: 0.9rem;
}

.score-green { color: #00ff88; }
.score-yellow { color: #ffd700; }
.score-red { color: #e94560; }

.company-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #0f3460;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.3s;
}

.company-card:hover {
    border-color: #e94560;
}

.stButton > button {
    background: linear-gradient(135deg, #e94560, #c23152);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    transition: all 0.3s;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #ff5577, #e94560);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(233,69,96,0.4);
}

.sidebar-btn {
    width: 100%;
    margin-bottom: 0.4rem;
}

.timer-green { color: #00ff88; font-size: 1.5rem; font-weight: bold; }
.timer-yellow { color: #ffd700; font-size: 1.5rem; font-weight: bold; }
.timer-red { color: #e94560; font-size: 1.5rem; font-weight: bold; animation: blink 1s step-end infinite; }

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

.leaderboard-row {
    display: flex;
    align-items: center;
    padding: 0.7rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #16213e, #1a1a2e);
    border: 1px solid #0f3460;
}

.badge-gold { color: #ffd700; font-size: 1.3rem; }
.badge-silver { color: #c0c0c0; font-size: 1.3rem; }
.badge-bronze { color: #cd7f32; font-size: 1.3rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "🏠 Home",
        "logged_in": False,
        "user": {},
        "sessions": [],          # list of {date, type, scores[]}
        "interview_active": False,
        "q_index": 0,
        "questions": [],
        "answers": [],
        "scores": [],
        "hints_used": [],
        "interview_type": None,
        "interview_done": False,
        "timer_start": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────
# QUESTION BANK  (50+ questions)
# ─────────────────────────────────────────────
QUESTION_BANK = {
    "HR": [
        {"q": "Tell me about yourself.", "keywords": ["experience","skills","background","graduated","worked","passionate","team","goal"], "sample": "I'm a final-year CS student at Anna University. I've developed strong skills in Python and data structures through projects and internships. I'm passionate about problem-solving and thrive in collaborative environments. My goal is to contribute to innovative products while continuously growing.", "tips": "Keep it under 2 minutes. Follow: Present → Past → Future structure."},
        {"q": "Why do you want to join our company?", "keywords": ["culture","growth","values","product","mission","align","contribute","learn"], "sample": "Your company's commitment to innovation and its collaborative culture align with my values. I'm particularly excited about your AI product roadmap and believe I can contribute meaningfully to that vision.", "tips": "Research the company before. Mention specific products or values."},
        {"q": "What are your strengths?", "keywords": ["analytical","communication","team","problem","adapt","leader","quick","creative"], "sample": "My key strength is analytical thinking—I break complex problems into manageable parts. I'm also a strong communicator and have led team projects in college successfully.", "tips": "Give 2–3 strengths with brief examples."},
        {"q": "What is your greatest weakness?", "keywords": ["improve","working","overcome","learning","awareness","action","steps"], "sample": "I sometimes focus too much on perfecting details. I've been working on this by setting time-boxed goals and using the 80/20 rule to prioritize.", "tips": "Show self-awareness + active improvement. Never say 'I work too hard.'"},
        {"q": "Where do you see yourself in 5 years?", "keywords": ["grow","senior","lead","skill","expertise","team","contribute","long-term"], "sample": "In 5 years I see myself as a senior engineer, leading a small team and contributing to architectural decisions. I want to deepen my expertise in distributed systems.", "tips": "Show ambition, but keep it realistic and company-relevant."},
        {"q": "Why should we hire you?", "keywords": ["skills","experience","contribute","value","unique","fit","team","deliver"], "sample": "I bring a strong technical foundation, hands-on project experience, and the ability to learn fast. My internship at XYZ showed I can deliver under pressure, and I'm confident I'll add value from day one.", "tips": "Connect your skills directly to the role requirements."},
        {"q": "Tell me about a time you failed.", "keywords": ["mistake","learned","improved","handled","recover","action","result","lesson"], "sample": "During a hackathon, I underestimated the time for integration. We missed a feature. I learned to break tasks into smaller chunks and build buffer time. Since then I've delivered all projects on schedule.", "tips": "Use STAR method. Focus on the lesson, not the failure."},
        {"q": "How do you handle pressure?", "keywords": ["prioritize","calm","deadline","manage","organize","breathe","plan","focus"], "sample": "I handle pressure by breaking the problem into steps and prioritizing. During exam season, I used a Kanban board to manage 3 deadlines simultaneously and delivered all on time.", "tips": "Give a concrete example. Mention a technique you use."},
        {"q": "Are you a team player or individual contributor?", "keywords": ["team","collaborate","independent","balance","support","communicate","flexible"], "sample": "I'm adaptable—I can work independently when needed but thrive in teams. In my final-year project, I coordinated a 4-person team while also handling the backend solo during crunch time.", "tips": "Show flexibility. Don't just say 'both'—demonstrate it."},
        {"q": "What motivates you?", "keywords": ["challenge","learn","impact","build","solve","grow","passion","achieve"], "sample": "I'm driven by building things that solve real problems. Seeing a user use something I built—whether it's an app or a script—gives me immense satisfaction.", "tips": "Be genuine. Tie it to the role."},
    ],
    "Python": [
        {"q": "What are Python's key features?", "keywords": ["interpreted","dynamic","typing","readable","oop","functional","library","duck"], "sample": "Python is interpreted, dynamically typed, and supports OOP and functional paradigms. Its readability and rich standard library make it ideal for rapid development.", "tips": "Mention: GIL, duck typing, memory management."},
        {"q": "Explain list vs tuple vs set.", "keywords": ["mutable","immutable","ordered","unordered","duplicate","hashable","tuple","set"], "sample": "Lists are mutable ordered collections. Tuples are immutable ordered. Sets are mutable unordered with no duplicates. Use tuples for fixed data, sets for uniqueness checks.", "tips": "Mention time complexity: set lookup is O(1)."},
        {"q": "What is a decorator in Python?", "keywords": ["wrapper","function","modify","extend","@","higher-order","closure","behaviour"], "sample": "A decorator is a higher-order function that wraps another function to extend its behaviour without modifying it. Used with @syntax. Common examples: @staticmethod, @property, @functools.lru_cache.", "tips": "Be ready to write a simple decorator from scratch."},
        {"q": "Explain generators and yield.", "keywords": ["lazy","iterator","memory","yield","next","iterable","state","efficient"], "sample": "Generators use yield to produce values lazily, pausing execution between calls. They're memory-efficient for large datasets. `range()` in Python 3 is a generator.", "tips": "Contrast with list comprehensions. Mention StopIteration."},
        {"q": "What is the GIL?", "keywords": ["global","interpreter","lock","thread","memory","cpython","performance","multiprocessing"], "sample": "The Global Interpreter Lock prevents multiple native threads from executing Python bytecode simultaneously. It's a CPython limitation. Use multiprocessing for CPU-bound tasks, asyncio/threads for I/O-bound tasks.", "tips": "Know when GIL matters and when it doesn't."},
        {"q": "Explain list comprehension with example.", "keywords": ["comprehension","concise","filter","map","expression","iterable","condition","readable"], "sample": "`[x**2 for x in range(10) if x%2==0]` creates a list of even squares. Comprehensions are more Pythonic and often faster than equivalent for-loops.", "tips": "Don't overuse nested comprehensions—readability matters."},
        {"q": "What are *args and **kwargs?", "keywords": ["positional","keyword","variable","arguments","unpack","flexible","tuple","dict"], "sample": "*args collects extra positional arguments as a tuple. **kwargs collects extra keyword arguments as a dict. They allow flexible function signatures.", "tips": "Demonstrate with a simple example. Mention order: args before kwargs."},
        {"q": "Explain OOP concepts in Python.", "keywords": ["class","object","inheritance","polymorphism","encapsulation","abstraction","method","self"], "sample": "Python supports all OOP pillars: Encapsulation via classes, Inheritance via subclassing, Polymorphism via method overriding, Abstraction via abstract base classes (ABC module).", "tips": "Give a short code example for each pillar."},
        {"q": "What is monkey patching?", "keywords": ["runtime","modify","class","attribute","dynamic","patch","test","mock"], "sample": "Monkey patching is dynamically modifying a class or module at runtime. Often used in testing to replace methods with mocks. Should be used carefully to avoid confusion.", "tips": "Mention unittest.mock as a safer alternative."},
        {"q": "How does Python manage memory?", "keywords": ["garbage","reference","counting","cyclic","gc","heap","del","allocation"], "sample": "Python uses reference counting as its primary GC mechanism. When count hits 0, memory is freed. The `gc` module handles cyclic references. Objects live on the heap.", "tips": "Mention __del__, weak references, and memory profiling tools."},
    ],
    "DBMS": [
        {"q": "What is normalization? Explain 1NF, 2NF, 3NF.", "keywords": ["redundancy","dependency","atomic","partial","transitive","key","relation","form"], "sample": "Normalization reduces redundancy. 1NF: atomic values, no repeating groups. 2NF: 1NF + no partial dependencies on composite key. 3NF: 2NF + no transitive dependencies.", "tips": "Draw small table examples. BCNF is stricter than 3NF."},
        {"q": "Explain ACID properties.", "keywords": ["atomicity","consistency","isolation","durability","transaction","rollback","commit","database"], "sample": "ACID ensures reliable transactions. Atomicity: all-or-nothing. Consistency: DB stays valid. Isolation: transactions don't interfere. Durability: committed data persists after crash.", "tips": "Give real-world examples for each property."},
        {"q": "What is an index and when should you use it?", "keywords": ["b-tree","lookup","read","write","clustered","non-clustered","performance","query"], "sample": "An index speeds up data retrieval using a B-tree or hash structure. Use indexes on frequently queried/joined columns. Avoid over-indexing—it slows writes.", "tips": "Know clustered vs non-clustered. Mention EXPLAIN in MySQL."},
        {"q": "Difference between JOIN types.", "keywords": ["inner","left","right","full","cross","outer","null","match"], "sample": "INNER JOIN: matching rows only. LEFT JOIN: all left rows + matches. RIGHT JOIN: all right + matches. FULL OUTER: all rows from both. CROSS JOIN: cartesian product.", "tips": "Draw Venn diagrams mentally. Practice writing all 4 types."},
        {"q": "What is a transaction? Explain with SQL.", "keywords": ["begin","commit","rollback","savepoint","lock","isolation","concurrent","integrity"], "sample": "A transaction is a unit of work. BEGIN TRANSACTION → SQL statements → COMMIT or ROLLBACK. Savepoints allow partial rollback within a transaction.", "tips": "Know isolation levels: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE."},
        {"q": "Explain SQL vs NoSQL databases.", "keywords": ["relational","schema","scalable","document","key-value","horizontal","consistency","flexible"], "sample": "SQL: structured schema, ACID, vertical scaling (MySQL, PostgreSQL). NoSQL: flexible schema, horizontal scaling, eventual consistency (MongoDB, Cassandra, Redis).", "tips": "Use cases: SQL for transactions, NoSQL for big data/real-time apps."},
        {"q": "What are stored procedures and triggers?", "keywords": ["procedure","trigger","automate","event","reusable","server-side","before","after"], "sample": "Stored procedures: precompiled SQL logic stored in DB, called explicitly. Triggers: automatically fire on INSERT/UPDATE/DELETE events. Both reduce app-DB round trips.", "tips": "Know the difference between BEFORE and AFTER triggers."},
        {"q": "What is denormalization?", "keywords": ["performance","redundancy","read","trade-off","join","cache","reporting","analytics"], "sample": "Denormalization intentionally adds redundancy to improve read performance by reducing joins. Common in data warehouses and reporting systems. Trade-off: more storage, update anomalies.", "tips": "Contrast with normalization. Mention OLAP vs OLTP."},
    ],
    "OS": [
        {"q": "What is a process vs thread?", "keywords": ["process","thread","memory","lightweight","share","context","switch","overhead"], "sample": "A process is an independent program in execution with its own memory space. A thread is a lightweight unit within a process sharing the same memory. Context switching is cheaper for threads.", "tips": "Mention: PCB, TCB, multi-threading advantages."},
        {"q": "Explain deadlock and its conditions.", "keywords": ["mutual","exclusion","hold","wait","circular","preemption","resource","prevent"], "sample": "Deadlock occurs when processes wait for each other's resources forever. Four conditions: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait. Prevention: break any one condition.", "tips": "Know Banker's Algorithm for deadlock avoidance."},
        {"q": "What is virtual memory?", "keywords": ["paging","swap","page","fault","physical","logical","address","mmu"], "sample": "Virtual memory allows processes to use more memory than physically available by using disk as an extension. The OS maps virtual addresses to physical via page tables. Page faults trigger disk reads.", "tips": "Know TLB, page replacement algorithms (LRU, FIFO, Optimal)."},
        {"q": "Explain CPU scheduling algorithms.", "keywords": ["fcfs","sjf","round","robin","priority","preemptive","burst","starvation"], "sample": "FCFS: first come first served, simple but convoy effect. SJF: shortest job first, optimal but needs burst time prediction. Round Robin: time-slice based, fair. Priority: starvation risk.", "tips": "Calculate average waiting time for small examples."},
        {"q": "What is semaphore?", "keywords": ["synchronization","binary","counting","wait","signal","mutex","critical","section"], "sample": "A semaphore is a synchronization primitive. Binary semaphore (0/1) is like a mutex. Counting semaphore tracks available resources. wait() decrements, signal() increments.", "tips": "Know Producer-Consumer problem solution using semaphores."},
        {"q": "Explain memory management techniques.", "keywords": ["paging","segmentation","fragmentation","compaction","buddy","slab","allocation","fit"], "sample": "Techniques include: Paging (fixed-size frames), Segmentation (variable logical units), Buddy System (power-of-2 allocation). External fragmentation handled by compaction or paging.", "tips": "Know internal vs external fragmentation clearly."},
        {"q": "What is a system call?", "keywords": ["kernel","user","mode","interface","trap","api","interrupt","privilege"], "sample": "System calls are interfaces between user space and kernel space. When a program needs OS services (file I/O, process creation), it triggers a software interrupt, switching to kernel mode.", "tips": "Examples: fork(), exec(), read(), write(), open()."},
    ],
    "Data Structures": [
        {"q": "Explain time complexity of common operations in arrays vs linked lists.", "keywords": ["O(1)","O(n)","access","insert","delete","head","tail","random"], "sample": "Arrays: O(1) access, O(n) insert/delete. Linked Lists: O(n) access, O(1) insert/delete at head. Use arrays for random access, linked lists for frequent insertions.", "tips": "Always state best/average/worst cases."},
        {"q": "What is a binary search tree (BST)?", "keywords": ["left","right","smaller","larger","inorder","balanced","search","insert"], "sample": "BST: left subtree contains smaller values, right contains larger. Search/insert/delete: O(log n) average, O(n) worst (skewed). Inorder traversal gives sorted output.", "tips": "Know AVL tree for balanced BST. Mention Red-Black Tree."},
        {"q": "Explain graph traversal: BFS vs DFS.", "keywords": ["queue","stack","level","depth","visited","adjacent","shortest","path"], "sample": "BFS uses a queue, explores level by level—ideal for shortest path in unweighted graphs. DFS uses a stack/recursion, explores depth-first—used for cycle detection, topological sort.", "tips": "Know time complexity: O(V+E) for both."},
        {"q": "What is dynamic programming?", "keywords": ["overlapping","subproblem","memoization","tabulation","optimal","cache","state","recurrence"], "sample": "DP solves problems with overlapping subproblems and optimal substructure. Top-down: memoization (cache recursive results). Bottom-up: tabulation (fill table iteratively). Examples: Fibonacci, Knapsack.", "tips": "Identify: can problem be broken into subproblems? Do they overlap?"},
        {"q": "Explain hashing and collision resolution.", "keywords": ["hash","function","collision","chaining","probing","bucket","load","factor"], "sample": "Hashing maps keys to indices via a hash function. Collisions resolved by: Chaining (linked list at bucket) or Open Addressing (linear/quadratic probing). Load factor affects performance.", "tips": "Average O(1) for insert/search. Know when to resize."},
        {"q": "What is a heap and where is it used?", "keywords": ["min","max","priority","queue","heapify","complete","binary","O(log n)"], "sample": "A heap is a complete binary tree satisfying heap property (min-heap: parent ≤ children). Used in: Priority Queues, Heap Sort, Dijkstra's algorithm. Heapify is O(n), insert/delete O(log n).", "tips": "Know heapify operation. Python's heapq module implements min-heap."},
        {"q": "Explain stack applications.", "keywords": ["undo","browser","expression","balanced","parentheses","call","backtrack","reverse"], "sample": "Stacks (LIFO) are used in: function call stack, expression evaluation (infix→postfix), balanced parentheses checking, undo operations, browser back button, DFS.", "tips": "Be ready to trace through a balanced parentheses algorithm."},
        {"q": "What are tries?", "keywords": ["prefix","string","search","autocomplete","dictionary","node","character","path"], "sample": "A trie (prefix tree) stores strings character by character. Each node represents a character. Enables O(m) search where m is word length. Used in autocomplete, spell-check, IP routing.", "tips": "Space can be large—mention compressed tries (Patricia tree)."},
    ],
    "Behavioral": [
        {"q": "Describe a challenging team project you worked on.", "keywords": ["situation","task","action","result","team","conflict","resolve","delivered"], "sample": "S: Our final-year project had 4 members with conflicting ideas. T: I needed to align the team. A: I organized a structured meeting, listed pros/cons of each approach, and we voted. R: We delivered ahead of schedule and won best project award.", "tips": "Use STAR: Situation, Task, Action, Result."},
        {"q": "Tell me about a time you showed leadership.", "keywords": ["led","initiative","motivated","decision","responsibility","outcome","team","influence"], "sample": "S: Our team lead dropped out a week before submission. T: Someone had to step up. A: I redistributed tasks based on strengths, held daily standups. R: We submitted on time with the best demo in class.", "tips": "Leadership doesn't require a title. Show initiative."},
        {"q": "How did you handle a conflict with a teammate?", "keywords": ["disagreement","communicate","listen","resolve","perspective","compromise","outcome","professional"], "sample": "S: Teammate and I disagreed on tech stack. T: We needed consensus to proceed. A: I listened to their reasoning, shared mine, and we researched both options together. R: We chose a hybrid approach that worked better than either original idea.", "tips": "Show maturity. Never badmouth the other person."},
        {"q": "Describe a time you went above and beyond.", "keywords": ["extra","initiative","unexpected","value","impact","surprise","effort","recognized"], "sample": "S: Internship task was just to fix a bug. T: While fixing it, I noticed a larger performance issue. A: I fixed the bug and documented the performance issue with a proposed solution. R: Manager implemented my suggestion, improving response time by 40%.", "tips": "Quantify the impact when possible."},
        {"q": "How do you prioritize when you have multiple deadlines?", "keywords": ["prioritize","urgent","important","matrix","list","communicate","deadline","manage"], "sample": "I use the Eisenhower Matrix: urgent+important first, then schedule important-not-urgent tasks. I communicate proactively if a deadline is at risk. During finals I managed 3 project deadlines simultaneously using this method.", "tips": "Mention specific tools or frameworks you use."},
        {"q": "Tell me about a time you learned something quickly.", "keywords": ["learn","adapt","fast","new","skill","technology","applied","short","time"], "sample": "S: Internship required Flask, which I hadn't used. T: Had 2 days to build an API. A: I did the official tutorial in day 1, built the API on day 2 referencing docs. R: Delivered on time, mentor said it was production-quality.", "tips": "Shows adaptability—highly valued in startups."},
    ],
    "TCS": [
        {"q": "What is TCS and what are its core values?", "keywords": ["tata","consultancy","services","integrity","respect","excellence","learning","agility"], "sample": "TCS (Tata Consultancy Services) is India's largest IT company. Core values: Integrity, Respect for individuals, Excellence, Learning & Sharing, Customer centricity.", "tips": "Know TCS's revenue, headcount, and key business verticals."},
        {"q": "Explain the difference between agile and waterfall.", "keywords": ["iterative","sprint","flexible","sequential","phase","requirement","change","feedback"], "sample": "Waterfall: sequential phases (requirements→design→code→test→deploy), rigid. Agile: iterative sprints, adaptive to change, continuous feedback. TCS uses both—Agile for product work, Waterfall for fixed-scope contracts.", "tips": "Know Scrum roles: PO, Scrum Master, Dev Team."},
        {"q": "What is cloud computing?", "keywords": ["iaas","paas","saas","aws","azure","gcp","scalable","on-demand","service"], "sample": "Cloud computing delivers on-demand IT resources over the internet. Models: IaaS (infrastructure), PaaS (platform), SaaS (software). Providers: AWS, Azure, GCP. TCS is a major cloud migration partner.", "tips": "Know TCS's cloud partnerships and offerings."},
        {"q": "What do you know about TCS iON and TCS BaNCS?", "keywords": ["ion","bancs","platform","digital","banking","education","product","tcs"], "sample": "TCS iON is a digital learning and assessment platform. TCS BaNCS is a financial services platform used by banks globally. Both are key TCS product offerings.", "tips": "Research at least 2–3 TCS products/platforms."},
    ],
    "Google": [
        {"q": "How does Google Search work at a high level?", "keywords": ["crawl","index","rank","pagerank","algorithm","spider","serp","relevance"], "sample": "Google crawls the web via bots, indexes content in massive data stores, then ranks results using algorithms including PageRank (link authority), content relevance, user signals, and hundreds of other factors.", "tips": "Mention: crawl budget, canonicalization, Core Web Vitals."},
        {"q": "Explain MapReduce.", "keywords": ["map","reduce","distributed","parallel","hadoop","key-value","aggregate","scale"], "sample": "MapReduce is a programming model for processing large datasets in parallel. Map phase: splits data and applies a function. Reduce phase: aggregates map outputs by key. Used in Hadoop, and influenced Google's Bigtable/Spanner.", "tips": "Word count is the classic example. Know its limitations vs Spark."},
        {"q": "What is CAP theorem?", "keywords": ["consistency","availability","partition","tolerance","choose","two","distributed","trade-off"], "sample": "CAP: In a distributed system, you can guarantee only 2 of 3: Consistency (all nodes same data), Availability (always responds), Partition Tolerance (works despite network splits). Most systems sacrifice C (Cassandra) or A (HBase).", "tips": "Google Spanner achieves CA+P with TrueTime—mention this."},
        {"q": "Describe your approach to a system design problem.", "keywords": ["requirements","scale","api","database","cache","load","balancer","trade-off"], "sample": "I start by clarifying functional and non-functional requirements, estimate scale (DAU, QPS), design APIs, choose data stores, add caching layer, design for scalability with load balancers and horizontal scaling, then discuss trade-offs.", "tips": "Use a structured approach: Requirements → High-level → Deep dive → Trade-offs."},
    ],
    "Startup": [
        {"q": "Why do you want to work at a startup?", "keywords": ["ownership","impact","learn","fast","build","iterate","autonomy","growth"], "sample": "I want direct ownership over what I build and to see its real-world impact quickly. Startups offer fast feedback loops, diverse responsibilities, and the chance to learn across the stack—not just one narrow area.", "tips": "Be honest. Mention risk tolerance. Ask about equity culture."},
        {"q": "How do you handle ambiguity?", "keywords": ["clarify","assumption","prototype","iterate","feedback","decision","comfortable","undefined"], "sample": "I first try to clarify with stakeholders. If that's not possible, I make explicit assumptions, prototype quickly, and seek early feedback. I'm comfortable making decisions with incomplete information and correcting course.", "tips": "Startups value bias-to-action. Don't say 'I wait for clarity.'"},
        {"q": "Describe a product you'd build to solve a local problem.", "keywords": ["problem","user","market","solution","build","validate","iterate","impact"], "sample": "I'd build a hyperlocal gig marketplace for Tamil Nadu's unorganized labour sector—connecting skilled workers (plumbers, electricians) with households via WhatsApp-first interface, solving the trust and discovery problem.", "tips": "Show product thinking: problem → solution → market → validation."},
        {"q": "How do you stay up-to-date with technology?", "keywords": ["read","blog","paper","twitter","newsletter","build","side","project","community"], "sample": "I follow Hacker News, specific GitHub repos, and newsletters like TLDR. I build side projects to apply new tech hands-on. I also engage with local developer communities like Chennai's tech meetups.", "tips": "Name specific resources. Build projects to show—not just read."},
    ],
}

# ─────────────────────────────────────────────
# COMPANIES DATA
# ─────────────────────────────────────────────
COMPANIES = [
    {"name": "TCS", "location": "Chennai, Tamil Nadu", "domain": "IT Services / Consulting", "phone": "+91-44-67789999", "website": "www.tcs.com", "employees": "600,000+", "founded": 1968},
    {"name": "Infosys", "location": "Chennai, Tamil Nadu", "domain": "IT Services / BPO", "phone": "+91-44-28524678", "website": "www.infosys.com", "employees": "350,000+", "founded": 1981},
    {"name": "Wipro", "location": "Chennai, Tamil Nadu", "domain": "IT Services / Cloud", "phone": "+91-44-28524500", "website": "www.wipro.com", "employees": "250,000+", "founded": 1945},
    {"name": "Cognizant", "location": "Chennai, Tamil Nadu", "domain": "IT Services / Digital", "phone": "+91-44-43281234", "website": "www.cognizant.com", "employees": "350,000+", "founded": 1994},
    {"name": "HCL Technologies", "location": "Chennai, Tamil Nadu", "domain": "IT Services / Engineering", "phone": "+91-44-23456789", "website": "www.hcltech.com", "employees": "220,000+", "founded": 1976},
    {"name": "Zoho Corporation", "location": "Chennai, Tamil Nadu", "domain": "SaaS / Product", "phone": "+91-44-67447000", "website": "www.zoho.com", "employees": "15,000+", "founded": 1996},
    {"name": "Freshworks", "location": "Chennai, Tamil Nadu", "domain": "SaaS / CRM", "phone": "+91-44-61154500", "website": "www.freshworks.com", "employees": "5,000+", "founded": 2010},
    {"name": "BHEL", "location": "Tiruchirappalli, Tamil Nadu", "domain": "Engineering / Manufacturing", "phone": "+91-431-2570100", "website": "www.bhel.com", "employees": "40,000+", "founded": 1952},
    {"name": "L&T Technology Services", "location": "Chennai, Tamil Nadu", "domain": "Engineering / R&D Services", "phone": "+91-44-67777777", "website": "www.ltts.com", "employees": "23,000+", "founded": 1997},
    {"name": "Hexaware Technologies", "location": "Chennai, Tamil Nadu", "domain": "IT Services / AI/ML", "phone": "+91-44-40521000", "website": "www.hexaware.com", "employees": "30,000+", "founded": 1990},
]

# ─────────────────────────────────────────────
# LEADERBOARD DATA
# ─────────────────────────────────────────────
LEADERBOARD = [
    {"rank": 1, "name": "Priya Ramesh", "college": "IIT Madras", "score": 9.4, "sessions": 28, "badge": "🥇"},
    {"rank": 2, "name": "Arjun Krishnan", "college": "Anna University", "score": 9.1, "sessions": 24, "badge": "🥈"},
    {"rank": 3, "name": "Kavya Subramaniam", "college": "NIT Trichy", "score": 8.9, "sessions": 31, "badge": "🥉"},
    {"rank": 4, "name": "Rahul Murugan", "college": "SSN College", "score": 8.7, "sessions": 19, "badge": "🏅"},
    {"rank": 5, "name": "Deepika Selvam", "college": "CEG Chennai", "score": 8.5, "sessions": 22, "badge": "🏅"},
    {"rank": 6, "name": "Vikram Narayanan", "college": "Amrita University", "score": 8.3, "sessions": 17, "badge": "🏅"},
    {"rank": 7, "name": "Ananya Chandrasekaran", "college": "VIT Vellore", "score": 8.2, "sessions": 20, "badge": "🏅"},
    {"rank": 8, "name": "Siva Karthikeyan", "college": "PSG Tech", "score": 8.0, "sessions": 15, "badge": "🏅"},
    {"rank": 9, "name": "Meena Durai", "college": "Thiagarajar College", "score": 7.8, "sessions": 18, "badge": "🏅"},
    {"rank": 10, "name": "Arun Balasubramanian", "college": "SRM Institute", "score": 7.6, "sessions": 21, "badge": "🏅"},
]

# ─────────────────────────────────────────────
# FILLER WORDS
# ─────────────────────────────────────────────
FILLER_WORDS = ["um", "uh", "basically", "like", "you know", "kind of", "sort of", "actually", "literally", "right"]

# ─────────────────────────────────────────────
# AI SCORING FUNCTION
# ─────────────────────────────────────────────
def score_answer(answer, question_data):
    if not answer or len(answer.strip()) < 10:
        return 1.0, "Answer too short."

    answer_lower = answer.lower()
    words = answer_lower.split()
    word_count = len(words)

    # Keyword score (0-4)
    keywords = question_data.get("keywords", [])
    matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
    keyword_score = min(4.0, (matched / max(len(keywords), 1)) * 4.0)

    # Length score (0-3): 80–200 words is ideal
    if word_count < 20:
        length_score = 0.5
    elif word_count < 50:
        length_score = 1.5
    elif word_count <= 200:
        length_score = 3.0
    elif word_count <= 350:
        length_score = 2.0
    else:
        length_score = 1.0

    # Filler word penalty (0-3)
    filler_count = sum(answer_lower.count(fw) for fw in FILLER_WORDS)
    filler_score = max(0, 3.0 - filler_count * 0.5)

    total = keyword_score + length_score + filler_score
    score = round(min(10.0, max(1.0, total)), 1)

    # Feedback
    feedback_parts = []
    if matched == 0:
        feedback_parts.append("❌ No key terms detected. Try to include relevant technical/domain vocabulary.")
    elif matched < len(keywords) // 2:
        feedback_parts.append(f"⚠️ Only {matched}/{len(keywords)} key terms covered. Expand your answer.")
    else:
        feedback_parts.append(f"✅ Good coverage of {matched}/{len(keywords)} key concepts.")

    if word_count < 50:
        feedback_parts.append("📝 Answer is too brief. Aim for 80–150 words.")
    elif word_count > 300:
        feedback_parts.append("📝 Answer is too long. Be concise—interviewers value clarity.")
    else:
        feedback_parts.append(f"📝 Good length ({word_count} words).")

    if filler_count > 3:
        feedback_parts.append(f"🔇 High filler word usage ({filler_count} found). Practice speaking without them.")
    elif filler_count > 0:
        feedback_parts.append(f"🔇 Minor filler words detected ({filler_count}). Keep improving.")
    else:
        feedback_parts.append("🔇 No filler words detected. Excellent delivery!")

    return score, " | ".join(feedback_parts)

# ─────────────────────────────────────────────
# GET QUESTIONS FOR INTERVIEW TYPE
# ─────────────────────────────────────────────
def get_questions(interview_type, n):
    category_map = {
        "HR": ["HR"],
        "Technical - Python": ["Python"],
        "Technical - DBMS": ["DBMS"],
        "Technical - OS": ["OS"],
        "Technical - Data Structures": ["Data Structures"],
        "Behavioral": ["Behavioral"],
        "Company - TCS": ["TCS", "HR"],
        "Company - Google": ["Google", "Data Structures"],
        "Company - Startup": ["Startup", "Behavioral"],
    }
    cats = category_map.get(interview_type, ["HR"])
    pool = []
    for cat in cats:
        pool.extend(QUESTION_BANK.get(cat, []))
    if not pool:
        pool = QUESTION_BANK["HR"]
    selected = random.sample(pool, min(n, len(pool)))
    if len(selected) < n:
        selected += random.choices(pool, k=n-len(selected))
    return selected

# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding: 1rem 0;'>
            <h2 style='color:#e94560; font-family:Syne,sans-serif; margin:0;'>🎯 AI Interview</h2>
            <h2 style='color:#e94560; font-family:Syne,sans-serif; margin:0;'>Coach</h2>
            <p style='color:#a8b2d8; font-size:0.8rem; margin:0.3rem 0 0 0;'>Tamil Nadu Edition</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        if st.session_state.logged_in:
            user = st.session_state.user
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#0f3460,#16213e);border:1px solid #e94560;border-radius:10px;padding:0.8rem;margin-bottom:1rem;text-align:center;'>
                <p style='color:#e94560;font-weight:700;margin:0;font-size:1rem;'>👤 {user.get("name","User")}</p>
                <p style='color:#a8b2d8;font-size:0.75rem;margin:0;'>{user.get("college","")}</p>
                <p style='color:#a8b2d8;font-size:0.75rem;margin:0;'>{user.get("branch","")} • Year {user.get("year","")}</p>
            </div>
            """, unsafe_allow_html=True)

        pages = [
            ("🏠", "Home"),
            ("📝", "Mock Interview"),
            ("📚", "Question Bank"),
            ("📊", "Progress Tracker"),
            ("🏆", "Leaderboard"),
            ("🤖", "AI Mentor"),
            ("🏢", "Top Companies"),
            ("👤", "My Profile"),
            ("📞", "Contact Us"),
        ]

        for icon, name in pages:
            label = f"{icon} {name}"
            active = st.session_state.page == label
            if st.button(label, key=f"nav_{name}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.page = label
                st.session_state.interview_active = False
                st.rerun()

        st.divider()
        if st.session_state.logged_in:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user = {}
                st.session_state.page = "🏠 Home"
                st.rerun()

sidebar()

# ─────────────────────────────────────────────
# PAGE: HOME
# ─────────────────────────────────────────────
def page_home():
    st.markdown("""
    <div class='main-header'>
        <h1>🎯 AI Interview Coach</h1>
        <p>Your personal interview preparation platform · Tamil Nadu Edition</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📋 Register")
            with st.form("register_form"):
                name = st.text_input("Full Name *")
                email = st.text_input("Email *")
                phone = st.text_input("Phone")
                college = st.text_input("College / University")
                branch = st.selectbox("Branch", ["CS", "IT", "ECE", "Mech", "Civil", "Other"])
                year = st.selectbox("Year", ["1st", "2nd", "3rd", "4th", "Alumni"])
                cgpa = st.number_input("CGPA", 0.0, 10.0, 7.5, 0.1)
                interests = st.multiselect("Areas of Interest",
                    ["Python", "Web Dev", "Data Science", "ML/AI", "DevOps", "Cloud", "DSA", "System Design", "Product Management"])
                submitted = st.form_submit_button("🚀 Register & Start", use_container_width=True)

                if submitted:
                    if not name or not email:
                        st.error("Name and Email are required.")
                    else:
                        st.session_state.user = {
                            "name": name, "email": email, "phone": phone,
                            "college": college, "branch": branch, "year": year,
                            "cgpa": cgpa, "interests": interests,
                        }
                        st.session_state.logged_in = True
                        st.session_state.page = "📝 Mock Interview"
                        st.success(f"Welcome, {name}! 🎉")
                        time.sleep(1)
                        st.rerun()

        with col2:
            st.markdown("### ⚡ Quick Login")
            with st.form("login_form"):
                qname = st.text_input("Your Name")
                qcollege = st.text_input("College")
                qbranch = st.selectbox("Branch ", ["CS", "IT", "ECE", "Mech", "Civil"])
                qlogin = st.form_submit_button("▶ Quick Start", use_container_width=True)
                if qlogin:
                    if not qname:
                        st.error("Please enter your name.")
                    else:
                        st.session_state.user = {
                            "name": qname, "college": qcollege, "branch": qbranch,
                            "email": "", "phone": "", "year": "3rd", "cgpa": 7.5, "interests": []
                        }
                        st.session_state.logged_in = True
                        st.session_state.page = "📝 Mock Interview"
                        st.rerun()

            st.markdown("---")
            st.markdown("""
            <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #0f3460;border-radius:12px;padding:1.5rem;'>
                <h4 style='color:#e94560;margin-top:0;'>✨ What you get</h4>
                <p style='color:#a8b2d8;'>🎤 Mock Interviews with AI Scoring</p>
                <p style='color:#a8b2d8;'>📚 50+ Questions across all domains</p>
                <p style='color:#a8b2d8;'>📊 Progress tracking & Radar charts</p>
                <p style='color:#a8b2d8;'>🏆 Tamil Nadu Leaderboard</p>
                <p style='color:#a8b2d8;'>🤖 AI Mentor with STAR guidance</p>
                <p style='color:#a8b2d8;'>🏢 Top 10 TN Companies info</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        user = st.session_state.user
        sessions = st.session_state.sessions

        st.markdown(f"## Welcome back, {user['name']}! 👋")

        c1, c2, c3, c4 = st.columns(4)
        total_sessions = len(sessions)
        all_scores = [s for sess in sessions for s in sess["scores"]]
        avg_score = round(sum(all_scores)/len(all_scores), 1) if all_scores else 0
        best_score = round(max(all_scores), 1) if all_scores else 0

        with c1:
            st.metric("Total Sessions", total_sessions, "interviews")
        with c2:
            st.metric("Avg Score", avg_score, "/ 10")
        with c3:
            st.metric("Best Score", best_score, "/ 10")
        with c4:
            st.metric("CGPA", user.get("cgpa", "N/A"))

        st.markdown("### 🚀 Quick Actions")
        qa1, qa2, qa3 = st.columns(3)
        with qa1:
            if st.button("🎤 Start Mock Interview", use_container_width=True):
                st.session_state.page = "📝 Mock Interview"
                st.rerun()
        with qa2:
            if st.button("📚 Browse Questions", use_container_width=True):
                st.session_state.page = "📚 Question Bank"
                st.rerun()
        with qa3:
            if st.button("📊 View Progress", use_container_width=True):
                st.session_state.page = "📊 Progress Tracker"
                st.rerun()

# ─────────────────────────────────────────────
# PAGE: MOCK INTERVIEW
# ─────────────────────────────────────────────
def page_interview():
    st.markdown("<div class='main-header'><h1>📝 Mock Interview</h1><p>Practice with AI-powered scoring and real-time feedback</p></div>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please register or login first.")
        return

    if st.session_state.interview_done:
        show_interview_results()
        return

    if not st.session_state.interview_active:
        # Setup
        c1, c2 = st.columns(2)
        with c1:
            itype = st.selectbox("Interview Type", [
                "HR", "Technical - Python", "Technical - DBMS", "Technical - OS",
                "Technical - Data Structures", "Behavioral",
                "Company - TCS", "Company - Google", "Company - Startup"
            ])
        with c2:
            n_qs = st.slider("Number of Questions", 3, 10, 5)

        if st.button("🚀 Start Interview", use_container_width=True):
            qs = get_questions(itype, n_qs)
            st.session_state.questions = qs
            st.session_state.answers = [""] * len(qs)
            st.session_state.scores = [0.0] * len(qs)
            st.session_state.hints_used = [False] * len(qs)
            st.session_state.q_index = 0
            st.session_state.interview_active = True
            st.session_state.interview_done = False
            st.session_state.interview_type = itype
            st.session_state.timer_start = time.time()
            st.rerun()
    else:
        run_interview()

def run_interview():
    idx = st.session_state.q_index
    qs = st.session_state.questions
    total = len(qs)

    if idx >= total:
        finalize_interview()
        return

    q_data = qs[idx]

    # Progress
    st.progress((idx) / total)
    st.markdown(f"**Question {idx+1} of {total}** — *{st.session_state.interview_type}*")

    # Timer
    elapsed = time.time() - st.session_state.timer_start
    remaining = max(0, 60 - int(elapsed))

    if remaining > 30:
        tcol = "timer-green"
        ticon = "🟢"
    elif remaining > 10:
        tcol = "timer-yellow"
        ticon = "🟡"
    else:
        tcol = "timer-red"
        ticon = "🔴"

    st.markdown(f"<p class='{tcol}'>{ticon} Time remaining: {remaining}s</p>", unsafe_allow_html=True)

    # Question
    st.markdown(f"""
    <div class='card'>
        <h3 style='color:#e94560;margin:0;'>Q{idx+1}. {q_data['q']}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Answer
    answer = st.text_area("Your Answer:", height=180, key=f"ans_{idx}",
                           placeholder="Type your answer here... (aim for 80–150 words)")
    word_count = len(answer.split()) if answer.strip() else 0
    st.caption(f"Word count: {word_count}")

    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        if st.button("✅ Submit Answer", key=f"sub_{idx}", use_container_width=True):
            score, feedback = score_answer(answer, q_data)
            st.session_state.answers[idx] = answer
            st.session_state.scores[idx] = score
            st.session_state.q_index = idx + 1
            st.session_state.timer_start = time.time()
            if idx + 1 >= total:
                st.session_state.interview_active = False
                st.session_state.interview_done = True
            st.rerun()

    with c2:
        if st.button("💡 Hint / Sample", key=f"hint_{idx}", use_container_width=True):
            st.session_state.hints_used[idx] = True
            st.info(f"**Sample Answer:** {q_data['sample']}\n\n**Tips:** {q_data['tips']}")

    with c3:
        if st.button("⏭ Skip", key=f"skip_{idx}", use_container_width=True):
            st.session_state.answers[idx] = ""
            st.session_state.scores[idx] = 1.0
            st.session_state.q_index = idx + 1
            st.session_state.timer_start = time.time()
            if idx + 1 >= total:
                st.session_state.interview_active = False
                st.session_state.interview_done = True
            st.rerun()

    # Auto-advance when timer runs out
    if remaining == 0:
        st.warning("⏰ Time's up! Auto-advancing to next question.")
        time.sleep(1)
        st.session_state.q_index = idx + 1
        st.session_state.timer_start = time.time()
        if idx + 1 >= len(qs):
            st.session_state.interview_active = False
            st.session_state.interview_done = True
        st.rerun()

def finalize_interview():
    qs = st.session_state.questions
    scores = st.session_state.scores
    itype = st.session_state.interview_type
    session_record = {
        "date": time.strftime("%Y-%m-%d"),
        "type": itype,
        "scores": list(scores),
        "avg": round(sum(scores)/len(scores), 1) if scores else 0,
    }
    st.session_state.sessions.append(session_record)
    st.session_state.interview_done = True
    st.rerun()

def show_interview_results():
    qs = st.session_state.questions
    scores = st.session_state.scores
    answers = st.session_state.answers

    avg = round(sum(scores)/len(scores), 1) if scores else 0
    st.markdown(f"## 🎉 Interview Complete!")

    c1, c2, c3 = st.columns(3)
    with c1:
        color = "#00ff88" if avg >= 7 else "#ffd700" if avg >= 5 else "#e94560"
        st.markdown(f"<div class='metric-card'><h2 style='color:{color};'>{avg}/10</h2><p>Average Score</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h2>{len(qs)}</h2><p>Questions Answered</p></div>", unsafe_allow_html=True)
    with c3:
        hints = sum(st.session_state.hints_used)
        st.markdown(f"<div class='metric-card'><h2>{hints}</h2><p>Hints Used</p></div>", unsafe_allow_html=True)

    # Bar chart
    labels = [f"Q{i+1}" for i in range(len(scores))]
    colors = ["#00ff88" if s >= 7 else "#ffd700" if s >= 5 else "#e94560" for s in scores]
    fig = go.Figure(go.Bar(x=labels, y=scores, marker_color=colors,
                           text=[f"{s}" for s in scores], textposition="outside"))
    fig.update_layout(
        title="Your Scores Per Question",
        paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
        font=dict(color="#a8b2d8"),
        yaxis=dict(range=[0, 10.5]),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detailed feedback
    st.markdown("### 📋 Detailed Feedback")
    for i, (q_data, answer, score) in enumerate(zip(qs, answers, scores)):
        with st.expander(f"Q{i+1}: {q_data['q']} — Score: {score}/10"):
            if answer:
                st.markdown(f"**Your Answer:** {answer}")
                _, feedback = score_answer(answer, q_data)
                st.info(feedback)
            else:
                st.warning("Question was skipped.")
            st.success(f"**Sample Answer:** {q_data['sample']}")
            st.caption(f"💡 **Tip:** {q_data['tips']}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Interview", use_container_width=True):
            st.session_state.interview_done = False
            st.session_state.interview_active = False
            st.session_state.questions = []
            st.rerun()
    with col2:
        if st.button("📊 View Progress", use_container_width=True):
            st.session_state.page = "📊 Progress Tracker"
            st.session_state.interview_done = False
            st.rerun()

# ─────────────────────────────────────────────
# PAGE: QUESTION BANK
# ─────────────────────────────────────────────
def page_question_bank():
    st.markdown("<div class='main-header'><h1>📚 Question Bank</h1><p>Browse 50+ curated interview questions with sample answers</p></div>", unsafe_allow_html=True)

    all_cats = list(QUESTION_BANK.keys())
    selected_cat = st.selectbox("Filter by Category", ["All"] + all_cats)

    cats_to_show = all_cats if selected_cat == "All" else [selected_cat]
    search = st.text_input("🔍 Search questions", "")

    for cat in cats_to_show:
        questions = QUESTION_BANK[cat]
        filtered = [q for q in questions if search.lower() in q["q"].lower()] if search else questions

        if not filtered:
            continue

        st.markdown(f"### {cat} ({len(filtered)} questions)")
        for i, q_data in enumerate(filtered):
            with st.expander(f"Q: {q_data['q']}"):
                st.markdown(f"**🔑 Key concepts:** `{'` · `'.join(q_data['keywords'][:5])}`")
                st.markdown("---")
                st.success(f"**✅ Sample Answer:** {q_data['sample']}")
                st.info(f"**💡 Tips:** {q_data['tips']}")

# ─────────────────────────────────────────────
# PAGE: PROGRESS TRACKER
# ─────────────────────────────────────────────
def page_progress():
    st.markdown("<div class='main-header'><h1>📊 Progress Tracker</h1><p>Track your improvement over time</p></div>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please login first.")
        return

    sessions = st.session_state.sessions

    if not sessions:
        st.info("No sessions yet. Complete a mock interview to see your progress!")

        # Show demo chart
        st.markdown("### 📈 Sample Progress Chart (Demo)")
        demo_scores = [5.2, 6.1, 5.8, 6.5, 7.0, 7.3, 7.8, 8.1]
        fig = px.line(x=list(range(1, len(demo_scores)+1)), y=demo_scores,
                      title="Sample: Score Improvement Over Sessions",
                      labels={"x": "Session", "y": "Avg Score"})
        fig.update_layout(paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
                          font=dict(color="#a8b2d8"))
        fig.update_traces(line_color="#e94560", line_width=3)
        st.plotly_chart(fig, use_container_width=True)
        return

    # Line chart - session scores
    session_nums = list(range(1, len(sessions)+1))
    avg_scores = [s["avg"] for s in sessions]

    fig_line = px.line(x=session_nums, y=avg_scores,
                       title="📈 Average Score Per Session",
                       labels={"x": "Session", "y": "Avg Score"},
                       markers=True)
    fig_line.update_layout(paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
                            font=dict(color="#a8b2d8"), yaxis=dict(range=[0, 10]))
    fig_line.update_traces(line_color="#e94560", line_width=3, marker_size=8)
    st.plotly_chart(fig_line, use_container_width=True)

    # Skills radar chart
    cat_scores = {
        "HR": [], "Python": [], "DBMS": [], "OS": [],
        "Data Structures": [], "Behavioral": []
    }
    for sess in sessions:
        itype = sess["type"]
        avg = sess["avg"]
        for cat in cat_scores:
            if cat.lower() in itype.lower():
                cat_scores[cat].append(avg)

    radar_vals = []
    for cat in cat_scores:
        vals = cat_scores[cat]
        radar_vals.append(round(sum(vals)/len(vals), 1) if vals else random.uniform(4, 7))

    categories = list(cat_scores.keys())
    fig_radar = go.Figure(go.Scatterpolar(
        r=radar_vals + [radar_vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(233,69,96,0.2)',
        line=dict(color='#e94560', width=2),
        marker=dict(size=8, color='#e94560')
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#16213e",
            radialaxis=dict(visible=True, range=[0, 10], color="#a8b2d8"),
            angularaxis=dict(color="#a8b2d8")
        ),
        paper_bgcolor="#1a1a2e",
        font=dict(color="#a8b2d8"),
        title="🕸️ Skills Radar Chart",
        height=450,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Session table
    st.markdown("### 📋 Session History")
    df = pd.DataFrame([{
        "Session": i+1,
        "Date": s["date"],
        "Type": s["type"],
        "Questions": len(s["scores"]),
        "Avg Score": s["avg"],
        "Best": max(s["scores"]),
        "Worst": min(s["scores"]),
    } for i, s in enumerate(sessions)])
    st.dataframe(df, use_container_width=True)

# ─────────────────────────────────────────────
# PAGE: LEADERBOARD
# ─────────────────────────────────────────────
def page_leaderboard():
    st.markdown("<div class='main-header'><h1>🏆 Leaderboard</h1><p>Top performers in Tamil Nadu</p></div>", unsafe_allow_html=True)

    st.markdown("### 🥇 Top 10 Tamil Nadu Students")
    for entry in LEADERBOARD:
        rank = entry["rank"]
        badge = entry["badge"]
        color = "#ffd700" if rank == 1 else "#c0c0c0" if rank == 2 else "#cd7f32" if rank == 3 else "#a8b2d8"
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#16213e,#1a1a2e);border:1px solid #0f3460;
             border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;
             display:flex;align-items:center;'>
            <span style='font-size:1.3rem;margin-right:1rem;'>{badge}</span>
            <span style='color:{color};font-weight:700;width:2rem;'>#{rank}</span>
            <span style='color:#ffffff;font-weight:600;flex:1;'>{entry["name"]}</span>
            <span style='color:#a8b2d8;margin-right:2rem;'>{entry["college"]}</span>
            <span style='color:#e94560;font-weight:700;'>{entry["score"]}/10</span>
            <span style='color:#a8b2d8;margin-left:1rem;font-size:0.85rem;'>{entry["sessions"]} sessions</span>
        </div>
        """, unsafe_allow_html=True)

    # User stats
    if st.session_state.logged_in:
        st.markdown("---")
        st.markdown("### 📊 Your Stats")
        user = st.session_state.user
        sessions = st.session_state.sessions
        all_scores = [s for sess in sessions for s in sess["scores"]]
        avg = round(sum(all_scores)/len(all_scores), 1) if all_scores else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Name", user["name"])
        with c2:
            st.metric("Sessions", len(sessions))
        with c3:
            st.metric("Avg Score", avg)
        with c4:
            st.metric("College", user.get("college", "—"))

        if avg > 0:
            rank_estimate = sum(1 for e in LEADERBOARD if e["score"] > avg) + 1
            st.info(f"Based on your average score of {avg}, your estimated rank is **#{rank_estimate}** in our leaderboard. Keep practicing!")

# ─────────────────────────────────────────────
# PAGE: AI MENTOR
# ─────────────────────────────────────────────
def page_mentor():
    st.markdown("<div class='main-header'><h1>🤖 AI Mentor</h1><p>Get expert guidance and STAR method tips</p></div>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please login first.")
        return

    topic = st.selectbox("Select Topic", list(QUESTION_BANK.keys()))
    questions_in_topic = QUESTION_BANK[topic]
    q_labels = [q["q"] for q in questions_in_topic]
    selected_q_label = st.selectbox("Select Question", q_labels)
    q_data = next((q for q in questions_in_topic if q["q"] == selected_q_label), None)

    if q_data:
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ✅ Sample Answer")
            st.success(q_data["sample"])

            st.markdown("#### 🔑 Key Concepts to Cover")
            for kw in q_data["keywords"]:
                st.markdown(f"• `{kw}`")

        with col2:
            st.markdown("#### 💡 Pro Tips")
            st.info(q_data["tips"])

            if topic == "Behavioral":
                st.markdown("#### ⭐ STAR Method Guidance")
                st.markdown("""
                <div class='card'>
                    <p style='color:#e94560;font-weight:700;'>S — Situation</p>
                    <p style='color:#a8b2d8;'>Set the scene. What was the context? Be specific but brief.</p>
                    <p style='color:#e94560;font-weight:700;'>T — Task</p>
                    <p style='color:#a8b2d8;'>What was your responsibility? What challenge needed solving?</p>
                    <p style='color:#e94560;font-weight:700;'>A — Action</p>
                    <p style='color:#a8b2d8;'>What did YOU specifically do? Use "I", not "we". Be detailed here.</p>
                    <p style='color:#e94560;font-weight:700;'>R — Result</p>
                    <p style='color:#a8b2d8;'>What was the outcome? Quantify where possible (%, time saved, impact).</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("#### 🎯 Practice Tips by Category")
        category_tips = {
            "HR": "Research the company before every HR interview. Know their mission, recent news, and products. Prepare your 'Tell me about yourself' in advance.",
            "Python": "Practice coding without an IDE. Be ready to explain time/space complexity. Review Python-specific idioms and PEP8.",
            "DBMS": "Bring a pen and draw schema diagrams. Practice SQL queries on HackerRank. Know normalization inside-out.",
            "OS": "Understand the OS concepts with diagrams. The Silberschatz textbook is gold. Focus on process scheduling and memory management.",
            "Data Structures": "LeetCode daily. Focus on patterns: sliding window, two pointers, BFS/DFS, DP. Time yourself.",
            "Behavioral": "Prepare 6–8 STAR stories that can adapt to different questions. Record yourself to catch filler words.",
            "TCS": "TCS interviews are structured. Prepare: NQT exam topics, technical MCQs on C/Java/Python, and HR rounds.",
            "Google": "System design is crucial. Study Designing Data-Intensive Applications. Practice on Pramp.com.",
            "Startup": "Show passion and versatility. Have side projects ready to demo. Know the startup's product deeply.",
        }
        st.info(f"**{topic} Strategy:** {category_tips.get(topic, 'Practice consistently and review sample answers.')}")

# ─────────────────────────────────────────────
# PAGE: TOP COMPANIES
# ─────────────────────────────────────────────
def page_companies():
    st.markdown("<div class='main-header'><h1>🏢 Top Companies in Tamil Nadu</h1><p>Explore leading employers and their details</p></div>", unsafe_allow_html=True)

    search = st.text_input("🔍 Search by name, location, or domain", "")
    filtered = [c for c in COMPANIES if
                search.lower() in c["name"].lower() or
                search.lower() in c["location"].lower() or
                search.lower() in c["domain"].lower()] if search else COMPANIES

    st.caption(f"Showing {len(filtered)} of {len(COMPANIES)} companies")

    for c in filtered:
        with st.expander(f"🏢 {c['name']} — {c['domain']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"📍 **Location:** {c['location']}")
                st.markdown(f"🏭 **Domain:** {c['domain']}")
            with col2:
                st.markdown(f"📞 **Phone:** {c['phone']}")
                st.markdown(f"🌐 **Website:** {c['website']}")
            with col3:
                st.markdown(f"👥 **Employees:** {c['employees']}")
                st.markdown(f"📅 **Founded:** {c['founded']}")

            # Interview tips per company
            company_tips = {
                "TCS": "NQT test + Technical + HR. Focus on aptitude, C/Java basics, and communication.",
                "Infosys": "InfyTQ platform test + HR. Strong focus on logical reasoning and verbal ability.",
                "Wipro": "NLTH test + Technical + HR. Practice data structures and aptitude.",
                "Cognizant": "GenC / GenC Next programs. Coding + aptitude + HR.",
                "HCL Technologies": "Online test + group discussion + interview. Focus on tech fundamentals.",
                "Zoho Corporation": "No-agent direct hiring. Multi-round written tests + technical interviews. Very merit-based.",
                "Freshworks": "Coding round + System design + Culture fit. Startup mindset valued.",
                "BHEL": "GATE score for engineers + departmental interviews. Technical depth required.",
                "L&T Technology Services": "Aptitude + Technical + HR. Focus on engineering fundamentals.",
                "Hexaware Technologies": "Online test + technical interview. AI/ML skills are a plus.",
            }
            st.info(f"🎯 **Interview Tip:** {company_tips.get(c['name'], 'Research the company and prepare for technical + HR rounds.')}")

# ─────────────────────────────────────────────
# PAGE: MY PROFILE
# ─────────────────────────────────────────────
def page_profile():
    st.markdown("<div class='main-header'><h1>👤 My Profile</h1><p>Your account details and performance summary</p></div>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        st.warning("Please login first.")
        return

    user = st.session_state.user
    sessions = st.session_state.sessions
    all_scores = [s for sess in sessions for s in sess["scores"]]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
        <div class='card'>
            <div style='text-align:center;margin-bottom:1rem;'>
                <div style='width:80px;height:80px;background:linear-gradient(135deg,#e94560,#c23152);
                     border-radius:50%;display:flex;align-items:center;justify-content:center;
                     font-size:2rem;margin:0 auto;'>
                    👤
                </div>
            </div>
            <h3 style='color:#e94560;text-align:center;margin:0;'>{user.get("name","—")}</h3>
            <p style='color:#a8b2d8;text-align:center;margin:0.3rem 0;'>{user.get("college","—")}</p>
            <hr style='border-color:#0f3460;'>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>📧</b> {user.get("email","—")}</p>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>📞</b> {user.get("phone","—")}</p>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>🎓</b> {user.get("branch","—")} • Year {user.get("year","—")}</p>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>📊</b> CGPA: {user.get("cgpa","—")}</p>
            <p style='color:#a8b2d8;'><b style='color:#e94560;'>💡</b> {", ".join(user.get("interests",[])) or "Not specified"}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 📊 Session Statistics")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Sessions", len(sessions))
        with c2:
            avg = round(sum(all_scores)/len(all_scores), 1) if all_scores else 0
            st.metric("Avg Score", avg)
        with c3:
            best = round(max(all_scores), 1) if all_scores else 0
            st.metric("Best Score", best)

        if sessions:
            # Score distribution
            fig = px.histogram(x=all_scores, nbins=10, title="Score Distribution",
                               labels={"x": "Score", "y": "Count"},
                               color_discrete_sequence=["#e94560"])
            fig.update_layout(paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
                              font=dict(color="#a8b2d8"))
            st.plotly_chart(fig, use_container_width=True)

            # Recent sessions
            st.markdown("#### 📋 Recent Sessions")
            recent = sessions[-5:][::-1]
            for s in recent:
                col_a, col_b, col_c = st.columns([2, 2, 1])
                with col_a:
                    st.markdown(f"📅 {s['date']} — {s['type']}")
                with col_b:
                    st.progress(s["avg"]/10)
                with col_c:
                    st.markdown(f"**{s['avg']}/10**")
        else:
            st.info("Complete mock interviews to see your stats here!")

# ─────────────────────────────────────────────
# PAGE: CONTACT US
# ─────────────────────────────────────────────
def page_contact():
    st.markdown("<div class='main-header'><h1>📞 Contact Us</h1><p>Reach out to our team in Chennai, Tamil Nadu</p></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class='card'>
            <h3 style='color:#e94560;'>🏢 AI Interview Coach HQ</h3>
            <p style='color:#a8b2d8;'>📍 <b>Address:</b><br>
            Level 5, Tower A, Tidel Park,<br>
            Rajiv Gandhi Salai (OMR),<br>
            Taramani, Chennai – 600 113,<br>
            Tamil Nadu, India</p>
            <hr style='border-color:#0f3460;'>
            <p style='color:#a8b2d8;'>📞 <b>Phone:</b> +91-44-6677-8899</p>
            <p style='color:#a8b2d8;'>📱 <b>WhatsApp:</b> +91-98400-12345</p>
            <p style='color:#a8b2d8;'>📧 <b>Email:</b> support@aiinterviewcoach.in</p>
            <p style='color:#a8b2d8;'>🌐 <b>Website:</b> www.aiinterviewcoach.in</p>
            <hr style='border-color:#0f3460;'>
            <p style='color:#a8b2d8;'>🕐 <b>Working Hours:</b><br>
            Mon–Fri: 9:00 AM – 6:00 PM IST<br>
            Sat: 10:00 AM – 2:00 PM IST<br>
            Sun: Closed</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📍 Our Location")
        location_df = pd.DataFrame({"lat": [13.0105], "lon": [80.2441]})
        st.map(location_df, zoom=13)

    with col2:
        st.markdown("#### 💬 Send Us a Message")
        with st.form("contact_form"):
            fname = st.text_input("Your Name *")
            femail = st.text_input("Your Email *")
            fphone = st.text_input("Phone (optional)")
            fsubject = st.selectbox("Subject", [
                "General Inquiry", "Technical Support", "Feedback",
                "Partnership", "Report a Bug", "Other"
            ])
            fmessage = st.text_area("Message *", height=160,
                                    placeholder="Tell us how we can help...")
            fsend = st.form_submit_button("📨 Send Message", use_container_width=True)

            if fsend:
                if not fname or not femail or not fmessage:
                    st.error("Please fill in all required fields.")
                else:
                    st.success(f"✅ Thank you, {fname}! Your message has been received. We'll respond to {femail} within 24 hours.")
                    st.balloons()

        st.markdown("""
        <div class='card' style='margin-top:1rem;'>
            <h4 style='color:#e94560;margin-top:0;'>🔗 Connect With Us</h4>
            <p style='color:#a8b2d8;'>🔵 LinkedIn: /company/ai-interview-coach-tn</p>
            <p style='color:#a8b2d8;'>🐦 Twitter/X: @AICoachTN</p>
            <p style='color:#a8b2d8;'>📸 Instagram: @ai.interview.coach.tn</p>
            <p style='color:#a8b2d8;'>▶️ YouTube: AI Interview Coach TN</p>
            <p style='color:#a8b2d8;'>💬 Telegram: t.me/AIInterviewCoachTN</p>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
page = st.session_state.page

if page == "🏠 Home":
    page_home()
elif page == "📝 Mock Interview":
    page_interview()
elif page == "📚 Question Bank":
    page_question_bank()
elif page == "📊 Progress Tracker":
    page_progress()
elif page == "🏆 Leaderboard":
    page_leaderboard()
elif page == "🤖 AI Mentor":
    page_mentor()
elif page == "🏢 Top Companies":
    page_companies()
elif page == "👤 My Profile":
    page_profile()
elif page == "📞 Contact Us":
    page_contact()
else:
    page_home()
