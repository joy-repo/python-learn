### Refer : https://realpython.com/python3-object-oriented-programming/

# How Do You Define a Class in Python?



In Python, you define a class by using the class keyword followed by a name and a colon. </br>
Then you use .__init__() to declare which attributes each instance of the class should have:


```python

class Employee:
    def __init__(self, name, age):
        self.name =  name
        self.age = age

```

***Note: Python class names are written in CapitalizedWords notation by convention. For example, a class for a specific breed of dog, like the Jack Russell Terrier, would be written as JackRussellTerrier.***


* **You define the properties that all Dog objects must have in a method called `.__init__()`. Every time you create a new Dog object, .__init__() sets the initial state of the object by assigning the values of the object’s properties. That is, .__init__() initializes each new instance of the class.**

* **You can give `.__init__()` any number of parameters, but the first parameter will always be a variable called self. When you create a new class instance, then Python automatically passes the instance to the self parameter in `.__init__()` so that Python can define the new attributes on the object.**



In the body of `.__init__()`, there are two statements using the self variable:

self.name = name creates an attribute called name and assigns the value of the name parameter to it.
self.age = age creates an attribute called age and assigns the value of the age parameter to it.

***Instance Attributes*** : Attributes created in `.__init__()` are called instance attributes. An instance attribute’s value is specific to a particular instance of the class. All Dog objects have a name and an age, but the values for the name and age attributes will vary depending on the Dog instance.
Example name. age instance varibles.
```python

class Employee:
    def __init__(self, name, age):
        self.name =  name
        self.age = age

```



***Class Attributes*** : are attributes that have the same value for all class instances. You can define a class attribute by assigning a value to a variable name outside of `.__init__()`.

Example : species is class variables.

```python
class Dog:
    species = "Canis familiaris"

    def __init__(self, name, age):
        self.name = name
        self.age = age
```


You define class attributes directly beneath the first line of the class name and indent them by four spaces.
**You always need to assign them an initial value.**
When you create an instance of the class, then Python automatically creates and assigns class attributes to their initial values.

```
>>> class Dog:
...     pass
... 
>>> Dog()
<__main__.Dog object at 0x00000257FAE2DF70>
>>>
```

In the output above, you can see that you now have a new Dog object at `0x00000257FAE2DF70`. </br>
This funny-looking string of letters and numbers is a **memory address** that indicates where Python stores the Dog object in your computer’s memory.


