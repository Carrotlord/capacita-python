# Capacita Programming Language

Capacita is a general purpose programming language, with the current implementation written in Python. At its core, it is a dynamically-typed language, but can be made to behave like a statically-typed language using type restrictions.

This language is imperative and object-oriented. You can expect features such as variables, operators, control flow, compound data structures, functions, classes, and a variety of value types. You can also utilize first-class functions and closures. Capacita does offer multiple inheritance as well.

Declaring types is optional in Capacita. This makes the language differ from many others. Instead of being forced to use types or leave them out, you can make the choice for each individual variable and function. It is possible to mix-and-match static typing and dynamic typing within a single program.

To start the REPL, use `python capacita.py` (you will need Python 2, not Python 3)
To run a Capacita program, use `python capacita.py NAME_OF_PROGRAM.cap`

## Example Programs

Here are some example programs. A full tutorial will be available in the future.

### Functions and Classes

```
import math

func square(x) = x * x
func hypotenuse(x, y) = sqrt(square(x) + square(y))

sub makeAdder(value)
    func addVal(x) = x + value
    return addVal
end

class Rectangle(x, y, width, height)
    func getArea() = width * height
    func getCenter() = {#x, (x + width / 2) | #y, (y + height / 2)}
end

print square(10.3)
print hypotenuse(3, 4)
add5 = makeAdder(5)
print add5(100)
r = Rectangle(20, 30, 50, 100)
print r.getArea()
print r.getCenter()
```

### Quicksort

```
sub performQuickSort(list, a, b)
    if a < b
        pivotIndex = partition(list, a, b)
        performQuickSort(list, a, pivotIndex - 1)
        performQuickSort(list, pivotIndex + 1, b)
    end
end

sub partition(list, a, b)
    pivot = list[b]
    i = a - 1
    for j = a; j < b; j += 1
        if list[j] < pivot
            i += 1
            temp = list[i]
            list[i] = list[j]
            list[j] = temp
        end
    end
    if list[b] < list[i + 1]
        temp = list[i + 1]
        list[i + 1] = list[b]
        list[b] = temp
    end
    return i + 1
end

sub quickSort(list)
    performQuickSort(list, 0, list.length() - 1)
end

list = [10, 9, 8, 2:5, 1:3, -500, -2400, 16, 65535]
quickSort(list)
print list
```

### Typed Variables

```
List w = [[100], [200, 300], [400, 500, 600], [700, 800]]
for Int j = 0; j < 4; j = j + 1
    List row = w[j]
    for Int i = 0; i < row.length(); i = i + 1
        show w[j][i]
        when i != row.length() - 1
            show ", "
    end
    print ""
end
```

### Multiple Inheritance

```
class Human(name)
    sub speak()
        print "Hello, I am " + name
    end
end

class Man(name) inherits Human
    super Human(name)
    
    sub speak()
        print "Hello, my name is " + name + ", and I am male."
    end
end

class Woman(name) inherits Human
    super Human(name)
    
    sub speak()
        print "Hello, my name is " + name + ", and I am female."
    end
end

class Bat()
    sub speak()
        print "*bat noises*"
    end
end

class Cat()
    sub speak()
        print "meow"
    end
end

class Batman(name) inherits Bat, Man
    super Bat()
    super Man(name)
end

class Catwoman(name) inherits Cat, Woman
    super Cat()
    super Woman(name)
end

Human bob = Batman("Bob")
Human alice = Catwoman("Alice")
Bat().speak()
Cat().speak()
bob.speak()
alice.speak()
Man("Chris").speak()
Woman("Daisy").speak()
```
