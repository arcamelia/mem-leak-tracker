# Citation: This program was built off of explore_ast.py in the examples package of the ast builder we used
# Link: https://github.com/eliben/pycparser/blob/master/examples/explore_ast.py

# coding: utf-8
from __future__ import print_function
import sys
import copy
import argparse

# This is not required if you've installed pycparser into
# your site-packages/ with setup.py
sys.path.extend(['.', '..'])

from pycparser import c_parser, c_ast, parse_file
from operator import add
from functools import reduce


testProgram= r"""
    int* coolfunc() {
        int* c = malloc(4);
        return c;
    }

    int main()
    {
        int* q = malloc(4);
        int* b = malloc(4);
        b = malloc(4);
        int* test2 = q;
        int* test;
        test = q;

        if(true) {
            int* f = malloc(4);
            if (true) {
                int * k = malloc(4);
                free(f);
                free(q);
            } else {
                free(q);
                free(f);
            }
            if (true) {
                int * p = malloc(4);
            }
            int * w = malloc(4);
        } else {
            int* g = malloc(4);
            free(q);
            free(b);
        }
    }
"""

# the top level list of statements in the C program
dec = []

# our version of memory locations
memloc = 0


# dictionaries for the state of the program
# < key=loc, value=list of aliases currently pointing to loc >
globalLocationDictionary = {}
# < key=alias (funcName.varName), value=list of locs it has pointed to over its life (current at tail) >
globalAliasDictionary = {}

# list of warnings generated for the program
warnings = []

#List of Pass by reference functions
referenceFuncs = []

# for keeping track of line number information
# < key=location, value=(allocation line num, last used line num) >
linesDictionary = {}

# number to keep track of nesting of controlflow
nest = 0
nestedAlias = {}
nestedLocation = {}
iterationHistoryAlias = {}
iterationHistoryLocation = {}

def findFuncDec(name):
    for funcDec in ast.ext:
        if str(funcDec.decl.name) == name:
            return funcDec

def incrementMemLoc():
    global memloc
    memloc += 1

def incrementNest():
    global nest
    nest += 1

def decrementNest():
    global nest
    nest -= 1

# Case where location is same on both branches may not be needed since memory location is global
# Combine dictionaries such that:
# A1: {a: [1], {b: [2]} ,L1: {1: [‘a’], 2: [‘b’]} and
# A2: {a: [1], {c: [3]} ,L2: {1: [‘a’], 3: [‘c’]}
# Results
# A3: {a: [1], b:[2], c:[3]} ,L4: {1: [‘a’],  2:[‘b’], 3:[‘c’]}
# Returns a tuple
def combineDictionaries(aDict1, aDict2, lDict1, lDict2):
    resultADict = {**aDict1, **aDict2}
    resultLDict = {**lDict1, **lDict2}
    return resultADict, resultLDict


# Given that the list1 is a list of old variables, and list2 is a list of new variables
# Return a list of the variables that were introduced in list2
# Ex. aList1 = [a,b,c]
#     aList2 = [a,b,c,d]
#     Returns [d]
def findIntroducedVars(aList1, aList2):
    introduced = []
    for var in aList2:
        if var not in aList1:
            introduced.append(var)
    return introduced


# Given that the list1 is a list of old variables, and list2 is a list of new variables
# Return a list of the variables that are missing in list2
# Ex. aList1 = [a,b,c]
#     aList2 = [a,b]
#     Returns [c]
def findMissingVars(aList1, aList2):
    missing = []
    for var in aList1:
        if var not in aList2:
            missing.append(var)
    return missing

def formatAliasName(funcName, alias):
    return funcName + "." + alias

def getAliasName(decl):
    if type(decl) == c_ast.Decl:
        return decl.name
    elif type(decl) == c_ast.Assignment and type(decl.lvalue) != c_ast.UnaryOp:
        return decl.lvalue.name
    elif type(decl) == c_ast.Return and type(decl.expr) != c_ast.Constant and type(decl.expr) != c_ast.UnaryOp:
        return decl.expr.name
    elif type(decl) == c_ast.FuncCall and type(decl.args.exprs[0]) != c_ast.Constant:
        return decl.args.exprs[0].name
    # cases above should cover all that we actually need the alias
    # return an empty string so formatAliasName doesn't complain
    return ""

def addNewAllocationLine(loc, decl):
    line = str(decl.coord).split(":")[1]
    # initialize last used line num as allocation line num
    linesDictionary[loc] = (line, line)

def updateLastUsedLine(loc, decl):
    if loc == -1 or loc == None:
        return
    line = str(decl.coord).split(":")[1]
    temp = list(linesDictionary[loc])
    temp[1] = line
    linesDictionary[loc] = tuple(temp)

def getAllocationLine(loc):
    if loc == -1 or loc == None:
        return None
    return linesDictionary[loc][0]

def getLastUsedLine(loc):
    if loc == -1 or loc == None:
        return None
    return linesDictionary[loc][1]

def printFormatAlias(alias):
    return "'" + alias + "'"

def inReferenceFunc(i):
    pbrNames = []
    for f in referenceFuncs:
        pbrNames.append(f.funcName)
    if i in pbrNames:
        return True
    else:
        return False

def returnReferenceFunc(i):
    for f in referenceFuncs:
        if f.funcName == i:
            return f
    return None
        
def evaluatePBR(referenceFunc, funcName, decl, aliasDictionary, locationDictionary):
    c = 0
    if hasattr(decl, "rvalue"):
        specDecl = decl.rvalue
    else:
        specDecl = decl
    for i in referenceFunc.pbrIndex:
        referencedVar = specDecl.args.exprs[i].name
        if referenceFunc.malloc[c]:
            # Malloc
            if funcName + "." + referencedVar in aliasDictionary and aliasDictionary[funcName + "." + referencedVar][-1] != -1:
                prevLocation = aliasDictionary[funcName + "." + referencedVar][-1]
                locationDictionary[prevLocation].remove(funcName + "." + referencedVar)
                locationDictionary[memloc] = [funcName + "." + referencedVar]
                aliasDictionary[funcName + "." + referencedVar].append(memloc)
                addNewAllocationLine(memloc, decl)
                incrementMemLoc()
            else:
                locationDictionary[memloc] = [funcName + "." + referencedVar]
                aliasDictionary[funcName + "." + referencedVar] = [memloc]
                addNewAllocationLine(memloc, decl)
                incrementMemLoc()
        # Free
        if referenceFunc.free[c]:
            if funcName + "." + referencedVar in aliasDictionary and aliasDictionary[funcName + "." + referencedVar][-1] != -1:
                locToFree = aliasDictionary[funcName + "." + referencedVar][-1]
                allAliases = locationDictionary[locToFree]
                for alias in allAliases:
                    aliasDictionary[alias].append(-1)
                locationDictionary.pop(locToFree)
                updateLastUsedLine(locToFree, decl)
        # Reallocate
        if not referenceFunc.morf[c]:
            for x in referenceFunc.reference:
                if referenceFunc.varNames[c] in referenceFunc.reference[x]:
                    locToReference = referenceFunc.pbrIndex[referenceFunc.varNames.index(x)]
                    varToReference = specDecl.args.exprs[locToReference].name
                    aliasedTo = funcName + "." + varToReference
                    if (aliasedTo in aliasDictionary): # check that the right hand side is in the dictionary already
                        aliasedLoc = aliasDictionary[aliasedTo]
                        aliasDictionary[funcName + "." + referencedVar] = [aliasedLoc[-1]]
                        locationDictionary[aliasedLoc[-1]].append(funcName + "." + referencedVar)
                        if aliasedLoc[-1] != -1:
                            updateLastUsedLine(aliasedLoc, decl)
        c += 1

def evaluateProgram(dec, funcName, passByRef, aliasDictionary, locationDictionary):
    global nestedAlias	
    global nestedLocation	
    global iterationHistoryAlias	
    global iterationHistoryLocation

    if dec is not None:
        for decl in dec:

            alias = formatAliasName(funcName, getAliasName(decl))

            if type(decl) == c_ast.Decl and type(decl.type) == c_ast.PtrDecl and hasattr(decl.init, "name") and decl.init.name != "NULL":
                # Adding entries for if the following is detected: int* a = malloc(4);
                if type(decl.init) == c_ast.FuncCall and decl.init.name.name == "malloc":
                    locationDictionary[memloc] = [alias]
                    aliasDictionary[alias] = [memloc]
                    addNewAllocationLine(memloc, decl)
                    incrementMemLoc()
                # Adding entries for if the following is detected: int* d = c; (where c has already been allocated)
                else:
                    aliasedTo = decl.init.name
                    if (aliasedTo in aliasDictionary): # check that the right hand side is in the dictionary already
                        aliasedLoc = aliasDictionary[aliasedTo]
                        aliasDictionary[alias] = [aliasedLoc[-1]]
                        locationDictionary[aliasedLoc[-1]].append(alias)
                        updateLastUsedLine(aliasedLoc, decl)

            # removing entries from dictionaries after a free has been detected
            if type(decl) == c_ast.FuncCall and decl.name.name == "free":
                locToFree = aliasDictionary[alias][-1]
                allAliases = locationDictionary[locToFree]
                for a in allAliases:
                    aliasDictionary[a].append(-1)
                locationDictionary.pop(locToFree)
                # note: instead of removing the entry from linesDictionary when the location is freed, 
                # we update the last used location to be that of the free
                updateLastUsedLine(locToFree, decl)

            # if check for 1a: return c (pointer that needs to be removed from the dictionary)
            if type(decl) == c_ast.Return and alias in aliasDictionary:
                locToFree = aliasDictionary[alias][-1]
                allAliases = locationDictionary[locToFree]
                for a in allAliases:
                    aliasDictionary[a].append(-1)
                locationDictionary.pop(locToFree)
                # note: instead of removing the entry from linesDictionary when the location is freed, 
                # we update the last used location to be that of the free
                updateLastUsedLine(locToFree, decl)

            # if check for case 1b: int* c = foo();
            if type(decl) == c_ast.Decl and type(decl.type) == c_ast.PtrDecl and hasattr(decl.init, 'name'):
                aliasedTo = decl.init.name
                if type(aliasedTo) != str: # Check that the right hand side is not null, which would be saved as a string
                    funcDec = findFuncDec(aliasedTo.name) # Find the user defined function
                    if funcDec is not None:
                        locationDictionary[memloc] = [alias]
                        aliasDictionary[alias] = [memloc]
                        addNewAllocationLine(memloc, decl)
                        incrementMemLoc()

            # if check for case 1c: c = foo();
            if type(decl) == c_ast.Assignment and type(decl.rvalue) != c_ast.UnaryOp and type(decl.rvalue) != c_ast.Constant:
                funcDec = None
                if type(decl.rvalue.name) != str:  # Ensure that the right hand side is not null, which would be saved as a string
                    funcDec = findFuncDec(decl.rvalue.name.name)  # Find the user defined function
                if funcDec is not None:
                    if aliasDictionary.get(alias) == -1 or aliasDictionary.get(alias)[-1] == -1: # c declared null previously
                        aliasDictionary[alias] = [memloc]
                        locationDictionary[memloc] = [alias]
                        addNewAllocationLine(memloc, decl)
                        incrementMemLoc()
                    elif aliasDictionary.get(alias) is not None: # c already points to allocated memory
                        locationDictionary[memloc] = [alias]
                        aliasDictionary[alias].append(memloc)
                        updateLastUsedLine(memloc, decl)
                        incrementMemLoc()

            # if check for case 3: repeat mallocs without freeing in between
            if type(decl) == c_ast.Assignment and alias in aliasDictionary and aliasDictionary.get(alias)[-1] != -1:
                if type(decl.rvalue.name) != str: # check that the right hand side is not null, which would be saved as a string
                    if decl.rvalue.name.name == "malloc":
                        prevLocation = aliasDictionary[alias][-1]
                        locationDictionary[prevLocation].remove(alias)
                        locationDictionary[memloc] = [alias]
                        aliasDictionary[alias].append(memloc)
                        addNewAllocationLine(memloc, decl)
                        incrementMemLoc()

            # if check for case 4: evaluating passByRef
            if type(decl) == c_ast.Assignment and type(decl.rvalue) != c_ast.UnaryOp and type(decl.rvalue) != c_ast.Constant and type(decl.rvalue.name) != str and inReferenceFunc(decl.rvalue.name.name):
                    referenceFunc = returnReferenceFunc(decl.rvalue.name.name)
                    evaluatePBR(referenceFunc, funcName, decl, aliasDictionary, locationDictionary)
            
            if type(decl) == c_ast.FuncCall and inReferenceFunc(decl.name.name):
                    referenceFunc = returnReferenceFunc(decl.name.name)
                    evaluatePBR(referenceFunc, funcName, decl, aliasDictionary, locationDictionary)

            # if check for case 2: assigning malloc to a pointer that has been declared null
            # int* a = NULL; OR int* a;
            if type(decl) == c_ast.Decl and type(decl.type) == c_ast.PtrDecl and ((hasattr(decl.init, "name") and decl.init.name == "NULL") or isinstance(decl.init, type(None))):
                aliasDictionary[alias] = [-1]
            # a = malloc()
            if type(decl) == c_ast.Assignment and type(decl.rvalue) == c_ast.FuncCall and decl.rvalue.name.name == "malloc":
                if aliasDictionary.get(alias) is not None:
                    lastLocation = aliasDictionary.get(alias)[-1]
                    if lastLocation == -1:
                        aliasDictionary[alias] = [memloc]
                        locationDictionary[memloc] = [alias]
                        addNewAllocationLine(memloc, decl)
                        incrementMemLoc()
            
            # if check for case 5: assigning a malloc'd pointer to a variable
            if type(decl) == c_ast.Assignment and type(decl.rvalue) != c_ast.FuncCall and type(decl.rvalue) != c_ast.UnaryOp and type(decl.lvalue) != c_ast.UnaryOp and aliasDictionary.get(alias) != None:
                assignmentAlias = formatAliasName(funcName, decl.rvalue.name)
                newLocation = aliasDictionary[assignmentAlias][-1]
                # if the variable being assigned to already points to allocated memory, remove it from its old location
                # (otherwise the variable is either null, not initialized, or previously freed)
                if not (aliasDictionary.get(alias) == -1 or aliasDictionary[alias][-1] == -1):
                    oldLocation = aliasDictionary[alias][-1]
                    locationDictionary[oldLocation].remove(alias)
                # update its new location
                aliasDictionary[alias].append(newLocation)
                locationDictionary[newLocation].append(alias)
                updateLastUsedLine(newLocation, decl)

            # add nest mallocs and frees here at the end
            if nest > 0:
                nestedAlias = aliasDictionary.copy()
                nestedLocation = locationDictionary.copy()
            else:
                nestedAlias = {}
                nestedLocation = {}

            # if check for loops
            if (type(decl) == c_ast.For or type(decl) == c_ast.While or type(decl) == c_ast.DoWhile) and not isinstance(decl.stmt.block_items, type(None)):
                evaluateLoop(decl, passByRef, funcName)

            # if check for conditionals
            if type(decl) == c_ast.If:
                evaluateConditional(decl, funcName, passByRef, aliasDictionary, locationDictionary)

            if nest == 0:
                iterationHistoryAlias = {}
                iterationHistoryLocation = {}
            
            #PASS BY REFERENCE SECTION
            #MALLOC
            if type(decl) == c_ast.Assignment and type(decl.lvalue) != c_ast.UnaryOp and (decl.lvalue.name) in passByRef.varNames:
                if type(decl.rvalue.name) != str: # check that the right hand s ide is not null, which would be saved as a string
                        if not passByRef.morf[passByRef.varNames.index(decl.lvalue.name)]:
                            passByRef.morf[passByRef.varNames.index(decl.lvalue.name)] = True
                        passByRef.malloc[passByRef.varNames.index(decl.lvalue.name)] = True
                        if passByRef.free[passByRef.varNames.index(decl.lvalue.name)]:
                            passByRef.free[passByRef.varNames.index(decl.lvalue.name)] = False 
                elif decl.rvalue.name in passByRef.varNames:
                    #REFERENCE
                    if passByRef.morf[passByRef.varNames.index(decl.lvalue.name)]:
                        passByRef.morf[passByRef.varNames.index(decl.lvalue.name)] = False
                    for reference in passByRef.reference:
                        if decl.lvalue.name in passByRef.reference[reference]:
                            passByRef.reference[reference].remove(decl.lvalue.name)
                    if decl.lvalue.name in passByRef.refNormVars:
                        passByRef.refNormVars.pop(decl.lvalue.name)
                    if decl.rvalue.name in passByRef.reference:
                        passByRef.reference[decl.rvalue.name].append(decl.lvalue.name)
                    else:
                        passByRef.reference[decl.rvalue.name] = [decl.lvalue.name]
                elif funcName + "." + decl.rvalue.name in aliasDictionary.keys():
                    if passByRef.morf[passByRef.varNames.index(decl.lvalue.name)]:
                        passByRef.morf[passByRef.varNames.index(decl.lvalue.name)] = False
                    for reference in passByRef.reference:
                        if decl.lvalue.name in passByRef.reference[reference]:
                            passByRef.reference[reference].remove(decl.lvalue.name)
                    passByRef.refNormVars[decl.lvalue.name] = decl.rvalue.name
                    
            #FREE
            if type(decl) == c_ast.FuncCall and decl.name.name == "free" and decl.args.exprs[0].name in passByRef.varNames:
                if passByRef.malloc[passByRef.varNames.index(decl.args.exprs[0].name)]:
                    passByRef.malloc[passByRef.varNames.index(decl.args.exprs[0].name)] = False
                else:
                    passByRef.free[passByRef.varNames.index(decl.args.exprs[0].name)] = True

def evaluateConditional(decl, funcName, passByRef, aliasDictionary, locationDictionary):
    global nestedAlias
    global nestedLocation
    global iterationHistoryAlias
    global iterationHistoryLocation

    incrementNest()

    # Record the records of all states
    iterationHistoryAlias[nest] = nestedAlias.copy()
    iterationHistoryLocation[nest] = nestedLocation.copy()
    # make copies of global Dictionaries
    if nest > 1:
        # Case where we are in a nested condtional statement
        ifAliasDictionary = copy.deepcopy(iterationHistoryAlias[nest])
        elseAliasDictionary = copy.deepcopy(iterationHistoryAlias[nest])
        ifLocationDictionary = copy.deepcopy(iterationHistoryLocation[nest])
        elseLocationDictionary = copy.deepcopy(iterationHistoryLocation[nest])
        aliasBefore = copy.deepcopy(iterationHistoryAlias[nest])
        locationBefore = copy.deepcopy(iterationHistoryLocation[nest])
    else:
        # Case where we are in the most outer condtional statement
        ifAliasDictionary = copy.deepcopy(aliasDictionary)
        elseAliasDictionary = copy.deepcopy(aliasDictionary)
        ifLocationDictionary = copy.deepcopy(locationDictionary)
        elseLocationDictionary = copy.deepcopy(locationDictionary)
        aliasBefore = copy.deepcopy(aliasDictionary)
        locationBefore = copy.deepcopy(locationDictionary)
    # Evaluating if branch
    evaluateProgram(decl.iftrue.block_items, funcName, passByRef, ifAliasDictionary, ifLocationDictionary)
    # Check if we just finished evaluated a nested condition
    if nest + 1 in iterationHistoryAlias:
        # Clear iteration history when reaching the outer-most condition
        if nest == 1:
            iterationHistoryAlias = {}
            iterationHistoryLocation = {}

    # Evaluating else branch
    if decl.iffalse is not None:
        evaluateProgram(decl.iffalse.block_items, funcName, passByRef, elseAliasDictionary, elseLocationDictionary)
        # Check if we just finished evaluated a nested condition
        if nest + 1 in iterationHistoryAlias:
            # Clear iteration history when reaching the outer-most condition
            if nest == 1:
                iterationHistoryAlias = {}
                iterationHistoryLocation = {}

    # Check if a declared variable has been initialized in one of the branches, update accordingly
    for key in ifAliasDictionary:
        if key in elseAliasDictionary:
            if ifAliasDictionary[key] == [-1] and elseAliasDictionary[key] != [-1]:
                ifAliasDictionary[key] = elseAliasDictionary[key]
            if ifAliasDictionary[key] != [-1] and elseAliasDictionary[key] == [-1]:
                elseAliasDictionary[key] = ifAliasDictionary[key]

    # Union both conditional block dictionaries
    result = combineDictionaries(ifAliasDictionary, elseAliasDictionary, ifLocationDictionary, elseLocationDictionary)

    # Finding introduced variables
    introducedVars = findIntroducedVars(locationBefore.values(), result[1].values())
    if introducedVars != []:
        introducedVars = reduce(add, introducedVars)

    # Finding variables missing in each branch
    if decl.iffalse is not None:
        missingVars = findMissingVars(ifLocationDictionary.values(), elseLocationDictionary.values()) + findMissingVars(
            elseLocationDictionary.values(), ifLocationDictionary.values())
    else:
        missingVars = findMissingVars(locationDictionary.values(),  ifLocationDictionary.values())
    
    if missingVars != []:
        missingVars = reduce(add, missingVars)

    missingVarsCopy = missingVars.copy()
    for var in missingVars:
        if var in introducedVars:
            missingVarsCopy.remove(var)
    missingVars = missingVarsCopy

    # Update globalDictionaries
    aliasDictionary.clear()
    locationDictionary.clear()
    for key in result[0]:
        aliasDictionary[key] = result[0][key]
    for key in result[1]:
        locationDictionary[key] = result[1][key]

    # Generate warnings
    generateIfWarnings(introducedVars, missingVars, aliasDictionary)
    decrementNest()

def generateIfWarnings(introducedVars, missingVars, aliasDictionary):
    # case MALLOC
    for eachVar in set(introducedVars):
        currLoc = aliasDictionary[eachVar][-1]
        w = "WARNING: variable " + printFormatAlias(eachVar) + " was allocated inside of a condition block but was not freed before the condition block's end"
        w += "\n\t-> Allocation occurred at line " + getAllocationLine(currLoc)
        w += "\n\t-> Last reference occurred at line " + getLastUsedLine(currLoc)
        if w not in warnings:
             warnings.append(w)

    # case FREE
    for eachVar in set(missingVars):
        w = "WARNING: variable " + printFormatAlias(eachVar) + " was freed inside one of the condition blocks but not the other block"
        if w not in warnings:
            warnings.append(w)

# decl is the loop decl
def evaluateLoop(decl, pbr, funcName):
    # Copy the current state of the dictionaries
    aliasBefore = {}
    for key in globalAliasDictionary.keys():
        # note: using tuples to preserve immutability
        aliasBefore[key] = tuple(globalAliasDictionary[key])

    # Run through the loop one time, adding/removing entries as necessary from the global dictionaries
    loop = decl.stmt.block_items
    evaluateProgram(loop, funcName, pbr, globalAliasDictionary, globalLocationDictionary)

    # Generate warnings based on differences in the dictionaries' state before and after the loop
    generateLoopWarnings(aliasBefore)


def generateLoopWarnings(aliasBefore):
    varsBefore = aliasBefore.keys()
    varsAfter = globalAliasDictionary.keys()

    # case MALLOC
    for eachVar in set(varsAfter).difference(varsBefore):
        currLoc = globalAliasDictionary[eachVar][-1]
        if currLoc != -1:
            w = "WARNING: variable " + printFormatAlias(eachVar) + " was allocated inside of a loop but was not freed before the loop's end"
            w += "\n\t-> Allocation occurred at line " + getAllocationLine(currLoc)
            if w not in warnings:
                warnings.append(w)
    
    varsInBoth = set(varsBefore).intersection(varsAfter)
    for eachVar in varsInBoth:
        oldLoc = aliasBefore[eachVar][-1]
        newLoc = globalAliasDictionary[eachVar][-1]
        # case FREE
        if oldLoc != -1 and newLoc == -1:
            w = "WARNING: variable " + printFormatAlias(eachVar) + " was freed inside of a loop it was not declared in"
            w += "\n\t-> Free occurred at line " + getLastUsedLine(oldLoc)
            if w not in warnings:
                warnings.append(w)
        # case REALLOCATE
        elif aliasBefore[eachVar] != tuple(globalAliasDictionary[eachVar]):
            w = "WARNING: variable " + printFormatAlias(eachVar) + " was reallocated inside of a loop it was not declared in"
            if w not in warnings:
                warnings.append(w)

def generateOutput():
    # generate leak info
    leaks = []
    for loc in globalLocationDictionary:
        aliasesPointingToLoc = globalLocationDictionary[loc]
        if aliasesPointingToLoc != []:
            strAliases = ", ".join(map(printFormatAlias, aliasesPointingToLoc))
            l = "LEAK: Memory allocated at line " + getAllocationLine(loc) + " was never freed";
            l += "\n\t-> Variables pointing to this memory location: " + strAliases
            l += "\n\t-> Last reference occurred at line " + getLastUsedLine(loc)
        else:
            l = "LEAK: Memory allocated at line " + getAllocationLine(loc) + " was never freed and has nothing pointing to it"
            l += "\n\t-> Last reference occurred at line " + getLastUsedLine(loc)
        if l not in leaks:
            leaks.append(l)
    
    # print leak info
    if (leaks):
        print("")
        print(*leaks,sep='\n\n')
    
    # print warning info (from conditionals & loops)
    if (warnings):
        print("")
        print(*warnings,sep='\n\n')

    if (leaks or warnings):
        print("")
    else:
        print("\nNo memory leaks detected!\n")
    
    # note: the `print("")` statements are to format the output on the console with spacing for better readability


# create the parser and ask to parse the program
# parse() will throw a ParseError if there's an error in the code
parser = c_parser.CParser()

# build an ast from a C file
argparser = argparse.ArgumentParser('memLeakTracker.py')
argparser.add_argument('c_filename',
                        help='name of file to parse')
args = argparser.parse_args()

ast = parse_file(args.c_filename, use_cpp=False)
# for testing
# ast = parser.parse(testProgram, filename='<none>')

# Pass By Reference object
class PassByReference:
  def __init__(self, funcName, varNames, pbrIndex, free, malloc, reference, morf, retName, refNormVars):
    self.funcName = funcName
    self.varNames = varNames
    self.pbrIndex = pbrIndex
    self.free = free
    self.malloc = malloc
    self.reference  = reference
    self.morf = morf
    self.retName = retName
    self.refNormVars = refNormVars
  def __str__(self):
      string = "Function Name: "
      string += self.funcName
      string += "\nVariable Names: "
      string += str(self.varNames)
      string += "\nVariable Indexes: "
      string += str(self.pbrIndex)
      string += "\nFree: "
      string += str(self.free)
      string += "\nMalloc: "
      string += str(self.malloc)
      string += "\nReferences: "
      string += str(self.reference)
      string += "\nReturn Variable Name: "
      string += str(self.retName)
      string += "\nReturn Referenced Normal vars: "
      string += str(self.refNormVars)
      string += "\nMalloc Last or Reference Last?: "
      string += str(self.morf)
      return string

# evaluate and generate output for the C program
for funcDec in ast.ext:
    pbr = False
    x = PassByReference(funcDec.decl.name, [], [], [], [], {}, [], None, {})
    if funcDec.decl.type.args is not None:
        for param in funcDec.decl.type.args.params:
            if(type(param.type) == c_ast.PtrDecl):
                pbr = True
                x.varNames.append(param.name)
                x.free.append(False)
                x.malloc.append(False)
                x.morf.append(True)
                x.pbrIndex.append(funcDec.decl.type.args.params.index(param))
    if pbr:
        referenceFuncs.append(x)
    evaluateProgram(funcDec.body.block_items, funcDec.decl.name, x,  globalAliasDictionary, globalLocationDictionary)
    alreadyMallocedVars = []
    alreadyMalloced = []
    for key in x.refNormVars:
        aliasedNormVar = funcDec.decl.name + "." + x.refNormVars[key]
        if not isinstance(globalAliasDictionary[aliasedNormVar], type(None)) and not x.morf[x.varNames.index(key)]:
            #MALLOC
            if globalAliasDictionary[aliasedNormVar][-1] != -1:
                if globalAliasDictionary[aliasedNormVar] not in alreadyMalloced:
                    if x.free[x.varNames.index(key)]:
                        x.free[x.varNames.index(key)] = False
                    x.malloc[x.varNames.index(key)] = True
                    alreadyMallocedVars.append(key)
                    alreadyMalloced.append(globalAliasDictionary[aliasedNormVar])
                else:
                    varToRef = alreadyMallocedVars[alreadyMalloced.index(globalAliasDictionary[aliasedNormVar])]
                    if varToRef in pbr.reference:
                        pbr.reference[varToRef].append(key)
                    else:
                        pbr.reference[varToRef] = [key]
            #FREE
            else:
                if x.malloc[x.varNames.index(key)]:
                    x.malloc[x.varNames.index(key)] = False
                else:
                    x.free[x.varNames.index(key)] = True

generateOutput()

# Old prints, leaving in for testing.
# ast.show(showcoord=True)
# print("LOCATION DICT (an unempty dict implies mem leak): " + str(globalLocationDictionary))
# print("ALIAS DICT: " + str(globalAliasDictionary))