# Meta Brainfuck

<!-- TODO decription -->

## Examples

create "Hello World" program:
```
"Hello, World!"{{+}.>}
```

create program that prints the first 10 Fibonacci numbers (as character codes)
```
1a:1b:10{a{+}a.b#b>a:b:}
```

Output the sequence of positive integers as binary numbers encoded in `.` and `+`

```
1n:"n a:2a#{a2%b:b{+}b0=a0=!&{.}a2/a:},n1#n:x?"x:x?
```

## Usage

`python metabf.py` followed by one or more of the following flags:

* `-x` execute the code given by the script
* `-o <output-file>` output the created Brainfuck code to the given file

optional additional flags:

* `-f <source-file>` set the source file (the default is `./test.mbf`)
* `-N <number>`  sets the maximum length (in characters) of the created output file, the default is `65536` 

## Syntax

Each brainfuck command (`+-<>[].,`) will add itself to the output program.
A sequence of characters surrounded by `"` defines a string, each sequence of digits will define a (decimal) number.
Sequences of letters are interpreted as variable names

Meta-Brainfuck is a stack based language, all operations act on a stack.

String and number literals push the corresponding value onto the stack.

### Loops

`{}` takes the top stack value and executes the coded surrounded by the brackets for each element of that value (characters in string, numbers from zero to value if integer),
the iteration variable is pushed onto the stack at the start of each iteration

Examples:

* `3{+}`  expands to `+++`
* `"Hello"{.}` expands to `.....`
* `"Hi!"{{+}.>}` expands to the following program, which will print the string `Hi!`
```
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++.>+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++.>+++++++++++++++++++++++++++++++++.>
```

### Operators

assignment:

`:` pops a variable and a value from the stack and assigns the value to the variable.
The right operand of `:` has to be a variable

`0a:` sets `a` to `0`
 
unary operators:

* `!` boolean negation
* `?` evaluate previous value as code (only works on strings)

binary operators:

* `=` equality check
* `(` `a b (` -> `1` if `a<b` otherwise `0`
* `)` `a b )` -> `1` if `a>b` otherwise `0`
* `&` minimum
* `|` maximum
* `#` addition  `a b #` -> `a+b`
* `~` subtraction `a b ~` -> `a-b`
* `*` multiplication `a b *` -> `a*b`
* `/` division `a b /` -> `a/b` (floor division)
* `%` modulo `a b %` -> `a%b`   (remainder of given division)



