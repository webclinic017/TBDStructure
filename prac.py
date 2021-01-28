class A:
    F = 10

# class C:


class B(A):
    a = 10
    print(A.F)
    A.F = 199
    print(A.F)

class C(A):
    print(A.F)
