# How Do You Define a Class in Python?

In Python, you define a class by using the class keyword followed by a name and a colon. </br>
Then you use .__init__() to declare which attributes each instance of the class should have:


```python

class Employee:
    def __init__(self, name, age):
        self.name =  name
        self.age = age

```




