class C:
    def method(self):
        return 1


def f():
    def inner():
        return 2
    return inner()
