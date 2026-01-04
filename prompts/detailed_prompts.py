"""Detailed prompts for ion transport symposium with Scientific Critic integration."""


# ============================================================================
# TEST AGENDA WITH CRITIC FEEDBACK
# ============================================================================
TEST_AGENDA_WITH_CRITIC = """
Explore the fundamental similarities and differences in ion transport across different fields.

Each expert should:
1. Present the key mechanisms of ion transport in your system
2. State the governing equations or principles (with assumptions clearly noted)
3. Provide ONE concrete, quantitative example from your field
4. Identify what you believe is universal vs. field-specific

After EACH expert speaks, the Scientific Critic will:
- Evaluate the strength of evidence and logic
- Challenge any unsupported claims or unclear assumptions
- Request clarification where needed
- Provide constructive feedback

The goal is to build a rigorous, evidence-based understanding of common principles.
"""


# ============================================================================
# DETAILED SYMPOSIUM AGENDAS
# ============================================================================

ROUND_1_DETAILED_AGENDA = """
ROUND 1: Map the Landscape of Ion Transport Theory

Objective: Create a comprehensive, critical survey of how each field approaches ion transport.

Each expert will present (10-15 minutes worth of content):

A. FUNDAMENTAL EQUATIONS (be explicit about assumptions)
   - What is your field's "master equation" for ion flux?
   - State it mathematically if possible (or describe in words)
   - List the key assumptions (steady-state? dilute? electroneutral? linear response?)
   - When do these assumptions break down in practice?

B. PHYSICAL MECHANISMS (diffusion, migration, convection, etc.)
   - Which transport mechanism typically dominates in your systems?
   - How do you experimentally distinguish between mechanisms?
   - What dimensionless numbers govern the competition between mechanisms?

C. SELECTIVITY (how your system chooses between ions)
   - What property determines selectivity: charge, size, hydration, binding?
   - Where does selectivity occur: at entry, during transit, or at exit?
   - Provide a quantitative example: "Ion A vs Ion B: selectivity = X because..."

D. LIMITING PHENOMENA (what sets maximum transport rate)
   - What causes "saturation" or "limiting current" in your systems?
   - Is the bottleneck in bulk transport, interface kinetics, or a boundary layer?
   - Give a real example with numbers (current density, flux, concentration, etc.)

E. ONE CRITICAL CHALLENGE in your field that relates to ion transport

After each expert finishes, the Scientific Critic will provide feedback before moving to the next expert.

AFTER ALL EXPERTS HAVE SPOKEN:
The Symposium Chair will synthesize and identify:
- Which equations appear in multiple fields (possibly under different names)
- Which mechanisms are universal vs. field-specific
- Where terminology differs but physics is the same
- Outstanding questions that need clarification in Round 2
"""


ROUND_2_DETAILED_AGENDA = """
ROUND 2: Identify Unifying Principles and Test Analogies

Objective: Rigorously test whether apparent similarities are deep or superficial.

Each expert will:

A. RESPOND TO ROUND 1 SYNTHESIS
   - Do you agree with the proposed common equations/principles?
   - Clarify any misunderstandings about your field
   - Refine your position based on what you heard from other experts

B. TEST SPECIFIC ANALOGIES
   The Chair will propose specific analogies. Each expert should evaluate:
   - Is this analogy valid? Where does it hold, where does it break?
   - Provide evidence or counterexamples

   Proposed analogies to test:
   1. Electrode double layer ↔ Donnan layer in membranes ↔ Ion channel selectivity filter
   2. Concentration polarization (electrodes) ↔ Boundary layer (membranes) ↔ Channel mouth depletion
   3. Limiting current (electrodes) ↔ Permselectivity limit (ED) ↔ Channel saturation
   4. Overpotential (electrodes) ↔ Membrane potential ↔ Action potential
   5. SEI layer ↔ Charged membrane ↔ Protein channel wall

C. QUANTITATIVE COMPARISON
   For your favorite system, estimate:
   - Characteristic length scale of the transport region (nm? μm? mm?)
   - Characteristic time scale for ion motion (ns? ms? s?)
   - Typical ion flux or current density
   - Energy barrier for selectivity (kT? 10 kT? 100 kT?)

   This will help us see if we're comparing apples to apples.

D. PROPOSE A UNIFYING EQUATION OR PRINCIPLE
   - What is the simplest statement that captures ion transport across all fields?
   - Example: "Ion flux follows gradients in electrochemical potential"
   - What are the minimal equations needed?

After each expert, the Scientific Critic evaluates the strength of arguments and analogies.

AFTER ALL EXPERTS:
The Chair will attempt to write down a "minimal common model" and ask experts to validate it.
"""


ROUND_3_DETAILED_AGENDA = """
ROUND 3: Build a Unified Framework and Identify Field-Specific Extensions

Objective: Agree on a common theoretical core and clearly define how each field extends it.

The Chair will present a draft "unified framework" based on Rounds 1-2.

Each expert will:

A. VALIDATE OR CHALLENGE THE FRAMEWORK
   - Does it correctly represent your field?
   - Are the equations correct and general enough?
   - What essential features are missing?

B. DEFINE YOUR FIELD'S "BOUNDARY CONDITIONS"
   - Given the common core equations, what makes your field unique?
   - Example: "Electrochemistry adds Butler-Volmer at interfaces"
   - Example: "Membranes add Donnan partitioning at interfaces"
   - Be explicit: these are ADD-ONS to the common core, not contradictions

C. MAP TERMINOLOGY
   Create a translation table:
   - Your field's term → Common framework term
   - Example: "Transference number" (electrochem) = "Transport number" (general)
   - Example: "Permselectivity" (membranes) = "Selectivity" (general)

D. IDENTIFY KNOWLEDGE GAPS
   - What experiments or simulations from other fields could inform yours?
   - What measurements are routinely done in one field but not others?
   - Could techniques from one field solve problems in another?

After each expert, the Critic assesses whether the framework truly unifies or just relabels.

FINAL SYNTHESIS:
The Chair will produce:
1. A concise statement of the unified framework (< 200 words)
2. A table mapping field-specific terms to common concepts
3. A list of 3-5 testable predictions or cross-field experiments
"""


ROUND_4_DETAILED_AGENDA = """
ROUND 4: Applications, Cross-Pollination, and Future Directions

Objective: Make the framework useful and identify high-impact applications.

Each expert will:

A. PROPOSE A CROSS-FIELD APPLICATION
   - How could insights from another field solve a problem in yours?
   - Be specific: "Insight X from field Y could improve Z in my field"
   - Explain the mechanism and estimate the potential impact

B. IDENTIFY A MEASUREMENT OR TECHNIQUE TO BORROW
   - What do other fields measure that you don't (but should)?
   - Example: Impedance spectroscopy, patch-clamp, permselectivity, transport numbers
   - How would this new measurement advance your field?

C. PROPOSE A "CHALLENGE PROBLEM" FOR THE UNIFIED FRAMEWORK
   - Describe one unsolved problem in your field
   - Ask: "Can the unified framework provide new insights here?"
   - Invite other experts to suggest approaches from their perspective

D. ENVISION FUTURE TECHNOLOGIES
   - What new device or material becomes possible with a unified understanding?
   - Example: "Membranes designed like ion channels for ultra-high selectivity"
   - Example: "Batteries with memristor-like adaptive interfaces"

After each expert, the Critic evaluates feasibility and novelty.

FINAL DELIVERABLE:
The Chair will produce:
1. A ranked list of high-impact cross-field opportunities
2. A proposed collaborative experiment or simulation
3. A roadmap for developing the unified framework into a review paper or grant proposal
"""


# ============================================================================
# RULES FOR RIGOROUS DISCUSSION
# ============================================================================
RIGOROUS_DISCUSSION_RULES = (
    "Clearly state assumptions before presenting equations or models",
    "Provide quantitative estimates whenever possible (numbers, not just trends)",
    "Distinguish between established facts, likely hypotheses, and speculation",
    "Define technical jargon when first used or translate to common language",
    "Acknowledge the limits of your expertise and defer to other experts appropriately",
    "Support claims with specific examples, data, or literature references",
    "When making analogies, explicitly state where they hold and where they break down",
)


# ============================================================================
# QUESTIONS FOR EACH ROUND
# ============================================================================
ROUND_1_QUESTIONS = (
    "What is the governing equation for ion flux in your field? State assumptions.",
    "What physical property determines ion selectivity in your system, and how is it measured?",
    "What causes the 'limiting' or saturation behavior in ion transport for your systems?",
)

ROUND_2_QUESTIONS = (
    "Which proposed analogy between fields is most valid, and which is most misleading?",
    "What is the simplest mathematical statement that captures ion transport across ALL fields?",
    "What dimensionless numbers or length/time scales distinguish your field from others?",
)

ROUND_3_QUESTIONS = (
    "Does the proposed unified framework correctly describe your field? If not, what is missing?",
    "What is the key 'boundary condition' or interface physics that makes your field unique?",
    "What terminology from your field should be adopted vs. replaced in the unified framework?",
)

ROUND_4_QUESTIONS = (
    "What is one concrete insight from another field that could advance your field?",
    "What is one unsolved problem in your field where the unified framework might help?",
    "What new technology or material could emerge from this cross-field understanding?",
)
