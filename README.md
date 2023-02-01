# MemLeakTracker
## A static program analysis tool that tracks memory leaks in C
<br/>

**Please read `UserGuide.md` for installation instructions and an intro to our program analysis tool.**
<br/>
<br/>
**1st User Study Form**: https://docs.google.com/document/d/1txMv69-mI2WU-nxEgvHxWzY4vy3AfbSRb5npLBSY8pc/edit
<br/>
**User Study Results 1**: https://docs.google.com/document/d/1_EECoQBn1I4D_vwY6r-HnKdxj98vVHL8ny4CkCTuDWs/edit
<br/>
**User Study Results 2**: https://docs.google.com/document/d/1jhrLHdPVjvXwe0uk7JZEyi48nRl8blFtMzuX4mBPNNg/edit#
<br/>
Feedback:
- User 2 suggested that we add additional information for where the memory was last used which we have implemented
  - ex. "Memory allocated at line x was not freed. Last use of this memory occurred at line y."

**2nd User Study Form**: https://docs.google.com/document/d/1OIjZH4D9-4xR-ph3SIRnHSt-c7qRQylVOen0FbcsN5I/edit
<br/>
**User Study Results**: https://docs.google.com/document/d/1H0AzffNygRTP4wqc6nSedRoO3SAuJ5goQxlZW3kQ0iE/edit#
<br/>
Feedback:
- User found the tool helpful and said it would be a useful tool for a compiler
- Liked calling out which variable was not freed + line numbers
- One piece of feedback we will try to implement was that it might be nice to add spacing between each leak/warning

---
## Milestone 1
- We will be meeting Friday, October 28th to brainstorm some ideas for the project
- Candidate Idea (to be discussed with TA): C memory allocation tracker
    - keep track of memory leaks
    - In every control flow, do we free the memory?
    - timeline of memory usage (visual component)
    - static or dynamic (whichever is more doable within time constraints)
 
### TA Feedback
- TA discussed project requirements: 
  - 2 of 3 criteria on Slide Deck 9, Slide 3
  - program analysis, NOT meta-property analysis
  - concerned with program behaviour and is flow sensitive
- TA provided example ideas from previous projects

---

## Milestone 2
- Discussed advantages and tradeoffs of static vs dynamic analysis with TA, as well as how each might look in the
  context of our project idea
  - For static, we would need to decide what the abstract states, analysis functions, concretization function, and
    output will be
  - For dynamic, we would collect data regarding memory usage during the program, and then output that data visually
    after the program finishes running
- We think our project idea might need a few tweaks still, plan to go to Alex's OH tomorrow to discuss possibilities
  a bit further and make a final decision about static vs dynamic
- We need to decide which C language features to support in our tool (e.g., for loops, conditionals, gotos, 
  recursion, method calls etc.)

**Milestone Goals**

(these will likely need to be edited and made more specific after we decide on static / dynamic)

| Milestone |                               Goal                                |    Assignee(s)     |
|:---------:|:-----------------------------------------------------------------:|:------------------:|
|     3     |               Decide on static vs dynamic analysis                | Amelia, Coby, Matt |
|     3     |                Find C AST converter & familiarize                 |     Owen, Matt     |
|     3     | Nail down what analysis does NOT support (write example programs) |     Mary, Coby     |
|     4     |            Implement simple programs early in the week            |    Amelia, Coby    |
|     4     |           Implement advanced features late in the week            |     Owen, Mary     |
|     4     |      User study 1 (weekend before implementation gets going)      |     Matt, Owen     |
|     5     |                           User study 2                            |     Mary, Owen     |
|     5     |                           Project video                           |    Amelia, Matt    |
|     5     |                     Bug fixing and polishing                      |     Owen, Coby     |

---

## Milestone 3
- Mockup of example output outlined in the first user study: https://docs.google.com/document/d/1txMv69-mI2WU-nxEgvHxWzY4vy3AfbSRb5npLBSY8pc/edit
- First user study has been performed on one participant and the other remains to be done today
  - First study: https://docs.google.com/document/d/1_EECoQBn1I4D_vwY6r-HnKdxj98vVHL8ny4CkCTuDWs/edit?usp=sharing
- Completed goals for milestone 3:
  - Decided on static analysis
  - Chose the following AST parser and began writing simple malloc checking https://github.com/eliben/pycparser
  - Decided that mallocs within structs and double pointers are beyond scope for now (as discussed with Alex)
- Revised goals for milestone 4:
  - Hash out list of basic use cases and assign out to people to implement throughout the week (will discuss tonight)
  - Implement control flow and loop handling possibly on the weekend or next week when there is more availability
- TA has not yet responded to milestone 3 summary email


---

## Milestone 4
### Status of implementation & plan for remaining days.
 - So far, most basic cases are implemented.
 - Passing by reference is the only non-control flow issue that hasn’t  been solved, but may just be out of scope for the project.
 - If/then/else statements and loops will be implemented over the weekend.
 - Nice to haves and bug fixes are planned for week 5.
 - So far, we are theoretically still in line with our Milestone 2 plan.
### Plans for final user study.
 - User study 2 is planned to be executed at the end of week 5.
### TA Feedback
 - Project sounds in scope.
 - Make sure to check with Alex about passing by reference being an acceptable exclusion.


 ---

## Milestone 5
### Status of implementation & plan for remaining days.
- Implementation is largely complete and merging will be done Friday afternoon
- 2nd user study format has been created: https://docs.google.com/document/d/1OIjZH4D9-4xR-ph3SIRnHSt-c7qRQylVOen0FbcsN5I/edit
- User studies will be completed on the weekend
- Video will be completed after weekend
- To be addressed:
  - Line numbers
  - Changing c text input into a file input
  - Pass by reference
### TA Feedback
 - Project still sounds in scope
 - Went over rubric and other deliverables
