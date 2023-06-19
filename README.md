
# SAT solver 

A program for an educational competition of solving SAT problems. 

# Results of a competition

The solution is fully developed by me and it took 2nd place among 51 participants and lost to an existing algorithm implementation only. It is 43,7 times faster than the average result.

[Results](https://docs.google.com/spreadsheets/d/1shJnHj9kq5NloDtytCcwxqw_pTenL7PAPcJ5KMOQtEY/edit)

# Input data
Each test consists of 50 or more lines of disjuncts. Each line of disjuncts consists of conjuncts, where all the conjuncts after the ‘_’ symbol are negated.

Example: 

abc_xwe

…

yui_

_abc

Means (a&b&c&(!x)&(!w)&(!e)) | … | (y&u&i) | ((!a)&(!b)&(!c)), where & is logical AND, | is logical OR.

# Algorithm 
Currently, all the existing algorithms for solving SAT problems are enumerations with some improvements and my one is not an exception. Not implementing any mathematical improvements, the solution is fast due to tehnical optimizations, particularly, using machine word processing.

**The main idea** is having machine words for 3 cases:

- Conjunct literals' signs

- Conjunct literals' presence

- Current solution attempt

**Conjunct literals' signs** machine word indicates whether a literal is positive (0) or negative (1) in a current conjunct. For optimization purposes, the order of literals is reversed. Only last 26 bits of a machine word matter.

*Example*: 0000...00000000000000000000000101 means that in a current conjunct line 'a' and 'c' literals are negated, others are positive or aren't present.

**Conjunct literals' presence** machine word indicates whether a literal is present (1) in a current conjunct.

*Example*: 0000...00000000000000000000000101 means that in a current conjunct only 'a' and 'c' literals are present.

**Current solution attempt** machine word indicates current solution attempt literal's signs (0 for positive, 1 for negative).

*Example*: 0000...00000000000000000000000101 means that current solution attempt is a = 1, b = 0, c = 1, d = 0, e = 0 etc. 

After the initiazation of the first two machine words for each conjunct, a loop over **current solution attempt** is started. Current solution attempt is successfull if for every conjunct the operation ***literalSigns ^ solutionAttempt & literalExists*** is not 0 (*literalSigns* is a conjunct literals' signs machine word, *solutionAttempt* is a current solution attempt machine word, *literalExists* is a conjunct literals' presence machine word).

**The idea** of this set of operations is that in order for a conjunct's disjuncts to be true, its current attempt value and sign must be of the same value (true is a negated 0 or a positive 1) so the **XOR** operation is needed. Moreover, this disjunct must be present in a current line, otherwise it shouldn't affect the result, so **AND** operation takes place.

For optimization purposes, as soon as one conjunct is 0, the current attempt is declared unsuccessful and further tests for the current solution attempt aren't evaluated.

## Implementation

The implementation of the algorithm can be found in ```45 void find(const std::string& filename)```. The surrounding code is a testing environment.
