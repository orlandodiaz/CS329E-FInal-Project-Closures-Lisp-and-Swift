################ Lispy: Scheme Interpreter in Python

## (c) Peter Norvig, 2010-14; See http://norvig.com/lispy.html

################ Types

from __future__ import division

Symbol = str          # A Lisp Symbol is implemented as a Python str
List   = list         # A Lisp List is implemented as a Python list
Number = (int, float) # A Lisp Number is implemented as a Python int or float


################ Environments

def standard_env():
    "An environment with some Scheme standard procedures."
    import math, operator as op
    env = Env()
    env.update(vars(math)) # sin, cos, sqrt, pi, ...
    env.update({
        '+':lambda *x: reduce(lambda y, z: y + z, x) ,
        '-':lambda *x: -x[0] if len(x) == 1 else reduce(lambda y, z: y-z, x), '*':lambda *x: reduce(lambda y, z: z*y, x ),
        '/':lambda *x: x[0] / reduce(lambda y, z: y * z, x[1:])   if reduce(lambda y, z: y * z, x[1:])!= 0 else "ZeroDivisionError: Cannot divide by 0! ",
        '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '==':op.eq,
        'abs':     abs,
        'append':  op.add,
        'apply':   apply,
        'begin':   lambda *x: x[-1],
        'car':     lambda x: x[0],
        'cdr':     lambda x: x[1:],
        'cons':    lambda x, y: [x]+y,
        'concat':   lambda x, y: x + y,
        'eq?':     op.is_,
        'equal?':  op.eq,
        'length':  len,
        'count': lambda x,y:len([i for i in y if i == x]),
        'distinct':lambda x:[j for j in {i for i in x}],
        'positive': lambda x:([i for i in x if x > 0]),
        'positive?':lambda x: x > 0,
        'cond':  lambda *x: x[1] if x[0] else None,
        'list':    lambda *x: list(x),
        'list?':   lambda x: isinstance(x,list),
        'exec':    lambda x: eval(compile(x,'None','single')),
        'map':     map,
        'max':     max,
        'min':     min,
        'not':     op.not_,
        'null?':   lambda x: x == [],
        'number?': lambda x: isinstance(x, Number),
        'procedure?': callable,
        'round':   round,
        'symbol?': lambda x: isinstance(x, Symbol),
        'abs': abs,
    })
    return env

class Env(dict):
    "An environment: a dict of {'var':val} pairs, with an outer Env."
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms, args))
        self.outer = outer
    def find(self, var):
        "Find the innermost Env where var appears."
        return self if (var in self) else self.outer.find(var) if self.outer is not None else None

global_env = standard_env()


################ Procedures

class Procedure(object):
    "A user-defined Scheme procedure."
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env
    def __call__(self, *args): 
        return eval(self.body, Env(self.parms, args, self.env))
######################### CONSTANT CLOUSRE
class Constant(object):
    def f(self):
        data = {
          '$update':lambda x: data.update(x)
        }
        def cf(self, d):
           if d in data:
               return data[d]
           else:
               return None
        return cf
    run = f(1)

################ eval

toReturn = None
global dic
dic = {}
def eval(x, env=global_env):
    "Evaluate an expression in an environment."
    if isinstance(x, Symbol) :# variable reference
        return env.find(x)[x] if env.find(x) is not None else x
    elif not isinstance(x, List):  # constant literal
        return x                
    elif x[0] == 'quote':          # (quote exp)
        (_, exp) = x
        return exp
    elif x[0] == 'if':             # (if test conseq alt)
        (_, test, conseq, alt) = x
        exp = (conseq if eval(test, env) else alt)
        return eval(exp, env)
    elif x[0] == 'var' or x[0] == '=': # (define var exp)
        s1 = Constant()
        if len(x) == 4:
            (_, eq,var,exp) = x
        else:
            (_, var, exp) = x
        if s1.run(var) is None:
            x = eval(exp, env)
            if isinstance(x,List):
              print(x)
              x = [str(i) if not isinstance(i, List) else str(i[0]).replace('"',"") for i in x ]
              x = " ".join(x)
            env[var] = x
        else:
            return "error: cannot assign to value: "+ var + " is a 'let' constant"
    elif x[0] == 'set':           # (set var exp)
        (_, var, exp) = x
        env.find(var)[var] = eval(exp, env)
    elif x[0] == 'lambda':         # (lambda (var...) body)
        (_, parms, body) = x
        return Procedure(parms, body, env)
    elif x[0] == 'exec':
        proc = eval(x[0], env)
        import re
        exec(proc(re.sub(r"^'|'$", '', x[1])))
        return toReturn
    elif x[0] == 'print':
        if len(x) == 1:
            return
        elif len(x) == 2:
            return eval(x[1],env)
        else:
           return eval(x[1:], env)
    elif isinstance(x[0],Symbol) and x[0] not in env and len(x) == 2 and isinstance(x[1], Number):
        dic[x[0]] = x[1]
        return x[1]
    elif x[0] == 'let1':
        num = eval(x[1],env)
        results = [eval(exp,env) for exp in x[2:]]
        dic.clear()
        return results[-1] if len(results) > 0 else num
    elif x[0] == 'let':
        s1 = Constant()
        if len(x) == 4:
            (_, eq,var,exp) = x
        else:
            (_, var, exp) = x
        x = eval(exp, env)
        if isinstance(x,List):
           x = [str(i) if not isinstance(i, List) else str(i[0]).replace('"',"") for i in x ]
           x = " ".join(x)
        a = {var:x}
        env[var] = x
        s1.run('$update')(a)


    elif x[0] == "random":
        exec('from java.lang import Math; toReturn = Math.random()')
        return toReturn

    else:                          # (proc arg...)
        proc = eval(x[0], env)
        s = x[1:]
        for i in range(len(s)):
            if not isinstance(s[i], List):
                if s[i] in dic:
                    s[i] = dic[s[i]]
        args = [eval(exp, env) for exp in s]
        return proc(*args)
