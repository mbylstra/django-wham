def func(a, b, c, d , e=1, f=2):
    pass

# print func.func_code
func_name = 'func'
print getattr(func, func_name + '_code')
