# Prompting_Claude_A_Logic_Programmers_Guide

Original file: [Open source document](<../../../../materials/04_Prolog_and_Prompts/PromptProlog/Prompting_Claude_A_Logic_Programmers_Guide.pptx>)

Automatically prepared reading copy preserving the author’s content. Arguments and technical claims have not been validated. Refer to the original for layout.

> Text and embedded images are extracted by slide number. Shape positions, connectors, animations, and some charts are not reconstructed; consult the original PowerPoint for diagrams.

## Slide 1

Prompting Claude:

A Logic Programmer's Guide

Using Prolog as a conceptual lens for writing better prompts

## Slide 2

FOUNDATION

The Core Insight

Both Prolog and prompting are declarative.

You describe what you want — not how to compute it.

The system figures out the how.

Prolog Program

Write facts + rules.

Ask a query.

The inference engine finds the proof.

Prolog Style Prompt

Write context + instructions.

Ask a question.

Claude reasons toward an answer.

≈

## Slide 3

MAPPING

Facts  ↔  Context

Prolog facts are ground truths. Prompt context plays the same role.

% Facts
parent(tom, bob).

parent(bob, ann).

speaks(ann, french).

speaks(bob, english).

Prolog

# Context
Bob is Ann's parent.

Tom is Bob's parent.

Ann speaks French.

Bob speaks English.

Prompt: First Part: Context

≈

Same information. One is formal syntax; the other is natural language.

Key insight: Claude applies an open-world assumption — if a fact isn't stated, it draws on training data rather than returning false. Add "Answer only from the facts given above" to close the world.

## Slide 4

MAPPING

Rules  ↔  Instructions

The :- symbol means if. Prompt instructions are the same conditional logic in natural language.

ancestor(X,Y) :- parent(X,Y).

ancestor(X,Y) :- parent(X,Z),

               ancestor(Z,Y).

bilingual(X) :- parent(X,Y),

  speaks(X,english),

  speaks(Y,french).

Prolog

# Instructions

To find an ancestor, trace parent

relationships step by step.

If a parent and child speak different

languages, note the family is bilingual.

Prompt: Second Part: Instructions

≈

Prolog rules are exact and exhaustive. Prompt instructions are fuzzy — Claude applies them approximately, handling cases you didn't anticipate. This is the power and the risk.

Stop reading Prolog before the cut operator (!) appears — once cut arrives, the clean declarative analogy breaks down.

## Slide 5

MAPPING

Query  ↔  The User's Question

% Facts

parent(tom, bob).

parent(bob, ann).

speaks(ann, french).

speaks(bob, english).

% Rules

ancestor(X,Y) :- parent(X,Y).

ancestor(X,Y) :- parent(X,Z),

  ancestor(Z,Y).

% Query

?- ancestor(tom, ann).

Complete Prolog program

# Context

Tom is Bob's parent.

Bob is Ann's parent.

Ann speaks French.

Bob speaks English.

# Instructions

Trace parent relationships

step by step to find ancestors.

# Question

Is Tom an ancestor of Ann?

Complete prompt: With Question

≈

Facts → Context   |   Rules → Instructions   |   Query → User's Question   |   Inference Engine → Claude's Reasoning

## Slide 6

DEBUGGING

When Things Go Wrong

Prolog makes underspecification visible. Claude conceals it behind fluent prose.

Missing facts → Hallucination

Prolog: false

Claude: invents a confident answer

Fix: "Answer only from the facts given above."

Conflicting rules → Unpredictable output

Prolog: tries rules in order

Claude: follows whichever feels most salient

Fix: resolve conflicts explicitly

Silent disambiguation

Prolog: enumerates all valid answers

Claude: silently picks one interpretation

Fix: make the query more specific

Missing edge cases

Prolog: missing base case → stack error

Claude: missing edge case → unexpected output

Fix: enumerate boundary conditions

## Slide 7

LIMITS OF THE ANALOGY

What Falls Outside the Analogy

Prolog operates entirely within logic. Claude also operates somewhere else.

Tone & Register

A proof cannot be warm, dry, or urgent.

Claude can deliver the same fact in radically different registers.

Style & Voice

Two correct Prolog programs are interchangeable.

Claude can write with a distinctive voice.

Creativity

Prolog is closed under its knowledge base.

Claude can invent — metaphors, plots, novel analogies.

Judgment

Prolog fails cleanly on ambiguity.

Claude exercises practical wisdom where rules run out.

Empathy

Prolog has no model of the asker.

Claude can read intent, infer need, respond to the person.

Prolog tells you what to make explicit. The rest tells you what must be cultivated and trusted.

## Slide 8

REACT LOOP

The ReAct Loop: Prolog Made Visible

Thought

Goal selection

(next subgoal)

→

Action

External predicate

(tool call)

→

Observation

Unification with

result

→

Answer

Proof output

(final response)

Prolog

ReAct

Inference engine

The model (decides, reasons)

External predicate

Agent executes a tool

Result unified into proof state

Observation appended to history

Proof state

Message history

Next resolution step

Next call to the model

The ReAct loop is Prolog's inference engine stretched across time, with tool calls as external predicates.

## Slide 9

ARCHITECTURE

System, User, Assistant

The three roles map onto Prolog — but conversation breaks the analogy in a revealing way.

System

≈  Knowledge base

(facts + rules)

Fixed, loaded once.

Axioms the inference engine consults.

User

≈  Query

(+ assert/1)

Poses questions but also

adds new facts dynamically.

Assistant

≈  Proof output

(+ context shaper)

Not just an answer — each turn

reshapes what follows.

The key difference from Prolog:

Prolog's knowledge base is fixed between queries. In conversation, each assistant turn becomes part of the context — the "knowledge base" grows dynamically. This is assert/retract, but it is not a workaround; it is the whole point.

## Slide 10

REACT ARCHITECTURE

Model Decides · Agent Acts · History Remembers

The Model

Stateless. Receives a payload,

generates a response, stops.

Pure function from input to output.

Like Prolog's inference engine.

The Agent

Holds message history.

Executes tool calls.

Receives observations.

Decides when to loop or stop.

Message History

Explicit, inspectable proof state.

Can be pruned, edited, resumed.

Makes implicit context explicit

and controllable.

Without message history, context accumulates implicitly — harder to inspect, debug, or control.

## Slide 11

Same Shape,

Different Physics.

Prolog's declarative structure is the right mental model for writing precise, reliable prompts.

Thinking like a Prolog programmer — complete facts, scoped rules, unambiguous queries — catches most prompt bugs before they happen.

The ReAct loop is Prolog's inference engine made explicit, with tool calls as external predicates.

The message history is the proof state: make it explicit and it becomes inspectable, debuggable, controllable.

Where the analogy ends — tone, creativity, judgment, empathy — is where prompting becomes an art, not an engineering task.

## Slide 12

"Learn Prolog Now!" by Patrick Blackburn, Johan Bos, and Kristina Striegnitz is the standard recommendation for beginners. 

It's available free online at learnyouprolognow.com and 

walks you through the logic carefully without assuming a logic programming background. 

"Programming in Prolog" by Clocksin and Mellish (the original 1981 textbook). 

The first two chapters — facts, rules, and queries — are extremely clean and short. 

The syntax is minimal, the examples are everyday (family trees, simple classifications), and the declarative logic is front and center before 

any procedural complications creep in. 

It's the most "pure" presentation of the paradigm before you hit cuts, assert/retract, and all the messy pragmatics.

Links on the original slide:<http://www.learnprolognow.org/>

