# C Memory Leak Program Analysis Tool 

1. [ Project Description ](#desc)
2. [ Installation ](#install)
3. [ Usage ](#usage)
4. [ Notes about implementation ](#impl)
5. [ Test Cases ](#tests)

<a name="desc"></a>
## 1. Project Description

<br/>

Our program analysis statically analyzes C source code for memory leaks. It tracks memory leaks in the following scenarios in our analysis function:

- Basic memory allocation within a function that is not freed
- Forgetting to free between allocations
- Reassignment of pointers to other allocations without freeing first
- Caller forgetting to free a pointer that the callee has both declared and allocated
- Caller forgetting to free a pointer that the callee has allocated via pass by reference

And we concretize our program states when considering the following control flows:
- If/Else conditions
- While/For/Do-While loops

<br/>

<a name="install"></a>
## 2. Installation Guide

Please ensure that you have python 3.x installed. Follow the instructions to install `pycparser` (our chosen framework) here: https://github.com/eliben/pycparser

Note that if you have trouble importing pycparser when running our tool, you can also clone the pycparser repo and put the directory named `pycparser` in the root directory of our project.

<br/>

<a name="usage"></a>
## 3. Usage

You can call our tool in the command line like so:
```
python3 memLeakTracker.py <c_filename>
```

And the output will look something like this in the terminal:
```
LEAK: Memory allocated at line 7 was never freed
        -> Variables pointing to this memory location: 'main.ptr'
        -> Last reference occurred at line 7
```
We have provided examples c files in the `Examples` directory of our project. If you would like to run our tool in the root directory of our project using such an example, you would call `python3 memLeakTracker.py ./Examples/ex1.c`

<br/>

<a name="impl"></a>
## 4. Notes about implementation
Our program states are saved into three dictionaries:
- (A) maps Aliases to a list of memory locations 
- (L) maps Locations to a list of Aliases 
- (N) maps Locations to Line numbers

### If-Conditions
At two branching conditions, we recursively call our analysis function on both condition blocks. We then save two different sets of the above states and union them. We compare this unioned set of states with the prior set to see whether memory has been possibly lost at the end of either block.

### Loops
At a loop, we recursively call our analysis function on the loop and keep another set of states for after the while loop has completed once. We then compare this with the prior set to see whether memory has been potentially lost.

### Pass by Reference
Pointers in the parameters of functions are tracked, and information on how variables passed in would be affected is stored and updated as the analysis runs. Pointers in the parameters of a function are assumed to be freed by their caller, and thus cannot produce memory leaks on their own. Functions must be declared before calling (this is standard to C regardless). Recursive calls only information on passed pointers up to the line of the call.

<br/>

<a name="tests"></a>
## 5. Test Cases

For the following test cases, you can run mentioned files in the `Examples` directory with our tool to see the output.

### Basic Memory Leak
```
int main() {
    int* c = malloc(16);
}
```
The function has declared and allocated a pointer but has not freed it before the function's end. Test with: `ex1.c`

OUTPUT:
```
LEAK: Memory allocated at line 2 was never freed
        -> Variables pointing to this memory location: 'main.c'
        -> Last reference occurred at line 2
```

---

### No Memory Leaks

```
int main() {
    int c = 1;
}
```
The function has no memory leaks. Test with: `ex2.c` (nothing allocated) and `ex3.c` (all allocations freed)

OUTPUT:
(nothing)

---

### Forgetting to Free Between Allocations

```
int main() {
    int* c = malloc(16);
    c = malloc(8);
    free(c)
}
```
The initial allocation of c has not been freed before allocating it a new block. Test with: `ex4.c`

OUTPUT:
```
LEAK: Memory allocated at line 2 was never freed and has nothing pointing to it
        -> Last reference occurred at line 2
```
---


### Caller Forgetting to Free Pointer That Callee Declared and Returned
```
int foo() {
    int* c = malloc(4);
    return c;
}

int main() {
    int* a = foo();
    return 0;
}
```
The pointer to the allocated memory is not freed by the end of the caller's function. Test with: `ex5.c`

OUTPUT:
```
LEAK: Memory allocated at line 7 was never freed
        -> Variables pointing to this memory location: 'main.a'
        -> Last reference occurred at line 7
```
---

### Forgetting to Free Between Reassigning Aliases
```
int main() {
    int* a = malloc(4);
    int* b = malloc(4);
    b = a;
    free(b);
}
```
The initial allocation of b is not freed before reassigning it to the pointer of another allocation. Test with: `ex6.c`

OUTPUT:
```
LEAK: Memory allocated at line 3 was never freed and has nothing pointing to it
        -> Last reference occurred at line 3
```

---

### Memory Leak Via Pass by Reference
```
void func(int* r) {
    r = malloc (4);
}

int main()  
{
    int* c;
    func(c);
    return 0;
}
```

c is malloc'd when passed by reference, but is never freed. Test with: `basicPBR.c`

OUTPUT:
```
LEAK: Memory allocated at line 8 was never freed
        -> Variables pointing to this memory location: 'main.c'
        -> Last reference occurred at line 8
```

---

### Allocation Within One Condition Block but Not the Other (Concretization)
```
int main(int argc, char *argv[]) {
    int x = argv[1];
    if (x > 0) {
      int* mem = malloc(4);
    }
    return 0;
}
```
In the case that we enter the if-condition block, memory gets allocated but not freed. Test with: `ex7.c`

OUTPUT:
```
LEAK: Memory allocated at line 4 was never freed
        -> Variables pointing to this memory location: 'main.mem'
        -> Last reference occurred at line 4
WARNING: variable 'main.mem' was allocated inside of a condition block but was not freed before the condition block's end
        -> Allocation occurred at line 4
        -> Last reference occurred at line 4
```

---

### Freeing Within One Condition Block but Not the Other (Concretization)
```
int main(int argc, char *argv[]) {
    int x = argv[1];
    int* mem = malloc(4);
    if (x > 0) {
      free(mem);
    }
    return 0;
}
```
In the case that we enter the if-condition block, memory gets freed. Test with: `ex8.c`

OUTPUT:
```
LEAK: Memory allocated at line 3 was never freed
        -> Variables pointing to this memory location: 'main.mem'
        -> Last reference occurred at line 5
WARNING: variable 'main.mem' was freed inside one of the condition blocks but not the other block
```
---

### Allocation, Reallocation, and Freeing in a Loop (Concretization)
```
int main() {
    while (true) {
        int * c = malloc(4);
    }

    int * d;
    while(true) {
        d = malloc(4);
    }

    int * e = malloc(4);
    while(true) {
        free(e);
    }
}
```
The above code snippet declares/allocates c within a loop, allocates d when it has been declared outside the loop, and frees e inside of a loop it was not declared in. Test with: `ex9.c`

OUTPUT:
```
LEAK: Memory allocated at line 3 was never freed
        -> Variables pointing to this memory location: 'main.c'
        -> Last reference occurred at line 3
LEAK: Memory allocated at line 8 was never freed
        -> Variables pointing to this memory location: 'main.d'
        -> Last reference occurred at line 8
WARNING: variable 'main.c' was allocated inside of a loop but was not freed before the loop's end
        -> Allocation occurred at line 3
WARNING: variable 'main.d' was reallocated inside of a loop it was not declared in
WARNING: variable 'main.e' was freed inside of a loop it was not declared in
        -> Free occurred at line 13
```

---

### If-Condition Recursive Concretization
```
int main() {
  if (false) {
  } else {
      if (true) {
        int* d = malloc(16);
     }
  }
  return 0;
}
```
The above code snippet covers concretization within a deeper-nested conditional. Test with `ex10.c`

OUTPUT:
```
LEAK: Memory allocated at line 5 was never freed
        -> Variables pointing to this memory location: 'main.d'
        -> Last reference occurred at line 5
WARNING: variable 'main.d' was allocated inside of a condition block but was not freed before the condition block's end
        -> Allocation occurred at line 5
        -> Last reference occurred at line 5
```
---

### Loop Recursive Concretization
```
int main() {
    int * d;
    while(true) {
        while(true) {
            d = malloc(4);
        }
    }
}
```
The above code snippet covers concretization with a deeper-nested loop. Test with `ex11.c`

OUTPUT:
```
LEAK: Memory allocated at line 5 was never freed
        -> Variables pointing to this memory location: 'main.d'
        -> Last reference occurred at line 5
WARNING: variable 'main.d' was reallocated inside of a loop it was not declared in
```
