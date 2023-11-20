import sys
import argparse

BF_CHARS="+-<>[].,"
SPECIAL_CHARS="(){}:=&|!~*/%^?#$@\\';`"
DIGITS="0123456789"

TOKEN_BF="bf"
TOKEN_NUMBER="number"
TOKEN_STRING="string"
TOKEN_OPERATOR="operator"
TOKEN_IDENTIFIER="identifer"

class Token:
  def __init__(self,type,value):
    self.type=type
    self.value=value
  def __repr__(self):
    return f"{self.type}: {repr(self.value)}"

def tokenize(code):
  buff=""
  stringMode=False
  for c in code:
    if stringMode:
      if c=='"':
        yield Token(TOKEN_STRING,buff)
        stringMode=False
        buff=""
        continue
      if c=='\\':
        raise NotImplementedError("String escaping")
      buff+=c
      continue
    if c=='"':
      if len(buff)>0:
        yield Token(TOKEN_NUMBER,int(buff))if buff[0] in DIGITS else Token(TOKEN_IDENTIFIER,buff)
        buff=""
      stringMode=True
      continue
    if c in BF_CHARS or c in SPECIAL_CHARS:
      if len(buff)>0:
        yield Token(TOKEN_NUMBER,int(buff))if buff[0] in DIGITS else Token(TOKEN_IDENTIFIER,buff)
        buff=""
      yield Token(TOKEN_BF if c in BF_CHARS else TOKEN_OPERATOR,c)
      continue
    if c in DIGITS:
      if len(buff)>0 and buff[0] not in DIGITS:
        yield Token(TOKEN_IDENTIFIER,buff)
        buff=""
      buff+=c
      continue
    if len(buff)>0 and buff[0]  in DIGITS:
      yield Token(TOKEN_NUMBER,int(buff))
      buff=""
    if c.isspace():
      if len(buff)>0:
        yield Token(TOKEN_NUMBER,int(buff))if buff[0] in DIGITS else Token(TOKEN_IDENTIFIER,buff)
        buff=""
      continue
    buff+=c

def getValue(token,variables):
  if token.type==TOKEN_IDENTIFIER:
    return getValue(variables[token.value],variables)
  if token.type==TOKEN_STRING or token.type==TOKEN_NUMBER:
    return token
  raise Exception(f"tokens of {token.type} do not hold a value")

def getItems(token,variables):
  if token.type==TOKEN_IDENTIFIER:
    return getItems(variables[token.value],variables)
  if token.type==TOKEN_STRING:
    return map(lambda c:Token(TOKEN_NUMBER,ord(c)),token.value)
  if token.type==TOKEN_NUMBER:
    return map(lambda i:Token(TOKEN_NUMBER,i),range(token.value))

def compileTokens(tokens,variables={},stack=None):
  tokens=iter(tokens) ## ensure tokes is a generator
  valueStack=[] if stack is None else stack
  tokenBuffer=[]
  codeStack=[]
  depth=0
  try:
   while 1:
    token=codeStack.pop() if len(codeStack)>0 else next(tokens)
    if depth>0:
      if token.type!=TOKEN_OPERATOR:
        tokenBuffer.append(token)
        continue
      if token.value == "{":
        depth+=1
      if token.value == "}":
        depth-=1
      if depth>0:
        tokenBuffer.append(token)
        continue
      loopSrc=valueStack.pop()
      for e in getItems(loopSrc,variables): ## XXX? use code stack instead of recursion
        valueStack.append(e)
        yield from compileTokens(tokenBuffer,variables,valueStack)
      tokenBuffer=[]
      continue
    if token.type==TOKEN_BF:
      yield token.value
      continue
    if token.type!=TOKEN_OPERATOR:
      valueStack.append(token)
      continue
    if token.value=="{":
      depth=1
      continue
    if token.value==":":
      variable=valueStack.pop()
      if variable.type!=TOKEN_IDENTIFIER:
        raise Exception(f"cannot assign value to tokens of type {variable.type}");
      value=getValue(valueStack.pop(),variables)
      variables[variable.value]=value
      continue
    if token.value=="=":
      r=getValue(valueStack.pop(),variables)
      l=getValue(valueStack.pop(),variables)
      valueStack.append(Token(TOKEN_NUMBER,int(l.type==r.type and l.value==r.value)))
      continue
    if token.value=="(": ## XXX? use different operator for comparison
      r=getValue(valueStack.pop(),variables)
      l=getValue(valueStack.pop(),variables)
      valueStack.append(Token(TOKEN_NUMBER,int(l.type==r.type and l.value<r.value)))
      continue
    if token.value==")":
      r=getValue(valueStack.pop(),variables)
      l=getValue(valueStack.pop(),variables)
      valueStack.append(Token(TOKEN_NUMBER,int(l.type==r.type and l.value>r.value)))
      continue
    if token.value=="&":
      r=getValue(valueStack.pop(),variables)
      l=getValue(valueStack.pop(),variables)
      if (l.type == TOKEN_STRING and r.type == TOKEN_STRING) or (l.type == TOKEN_NUMBER and r.type == TOKEN_NUMBER):
        valueStack.append(Token(l.type,min(l.value,r.value)))
        continue
      raise Exception(f"incompatible types for logical and/minimum {l.type} and {r.type}")
    if token.value=="|":
      r=getValue(valueStack.pop(),variables)
      l=getValue(valueStack.pop(),variables)
      if (l.type == TOKEN_STRING and r.type == TOKEN_STRING) or (l.type == TOKEN_NUMBER and r.type == TOKEN_NUMBER):
        valueStack.append(Token(l.type,max(l.value,r.value)))
        continue
      raise Exception(f"incompatible types for logical or/maximum {l.type} and {r.type}")
    if token.value=="!":
      v=getValue(valueStack.pop(),variables)
      if v.type == TOKEN_NUMBER:
        valueStack.append(Token(l.type,int(v.value==0)))
        continue
      raise Exception(f"invalid type for logical not {v.type}")
    if token.value=="#":
      r=getValue(valueStack.pop(),variables)
      l=getValue(valueStack.pop(),variables)
      if (l.type == TOKEN_STRING and r.type == TOKEN_STRING) or (l.type == TOKEN_NUMBER and r.type == TOKEN_NUMBER):
        valueStack.append(Token(l.type,l.value+r.value))
        continue
      if l.type == TOKEN_STRING and r.type == TOKEN_NUMBER:
        valueStack.append(Token(TOKEN_STRING,l.value+chr(r.value)))
        continue
      if l.type == TOKEN_NUMBER and r.type == TOKEN_STRING:
        valueStack.append(Token(TOKEN_STRING,chr(l.value)+r.value))
        continue
      raise Exception(f"incompatible types for addtion {l.type} and {r.type}")
    if token.value=="~":
      r=getValue(valueStack.pop(),variables)
      l=getValue(valueStack.pop(),variables)
      if l.type == TOKEN_NUMBER and r.type == TOKEN_NUMBER:
        valueStack.append(Token(l.type,l.value-r.value))
        continue
      ## XXX string string ~ -> remove chars in second string from first
      raise Exception(f"incompatible types for subtraction {l.type} and {r.type}")
    if token.value=="*":
      r=getValue(valueStack.pop(),variables)
      l=getValue(valueStack.pop(),variables)
      if l.type == TOKEN_NUMBER and r.type == TOKEN_NUMBER:
        valueStack.append(Token(l.type,l.value*r.value))
        continue
      if (l.type == TOKEN_STRING and r.type == TOKEN_NUMBER) or (l.type == TOKEN_NUMBER and r.type == TOKEN_STRING):
        valueStack.append(Token(TOKEN_STRING,l.value*r.value))
        continue
      raise Exception(f"incompatible types for multiplication {l.type} and {r.type}")
    if token.value=="/":
      r=getValue(valueStack.pop(),variables)
      l=getValue(valueStack.pop(),variables)
      if l.type == TOKEN_NUMBER and r.type == TOKEN_NUMBER:
        valueStack.append(Token(l.type,l.value//r.value))
        continue
      raise Exception(f"incompatible types for division {l.type} and {r.type}")
    if token.value=="%":
      r=getValue(valueStack.pop(),variables)
      l=getValue(valueStack.pop(),variables)
      if l.type == TOKEN_NUMBER and r.type == TOKEN_NUMBER:
        valueStack.append(Token(l.type,l.value%r.value))
        continue
      raise Exception(f"incompatible types for remainder {l.type} and {r.type}")
    if token.value=="?": ## evaluate string as code
      v=getValue(valueStack.pop(),variables)
      if v.type == TOKEN_STRING:
        if not hasattr(v, 'tokens'): ## parse tokens on first call, reuse tokens for subsequent calls
          v.tokens = [*tokenize(v.value)]
        codeStack.extend(reversed(v.tokens))
        continue
      raise Exception(f"invalid type for code evaluation {v.type}")
    # unused operators ^$@\';`
    raise Exception(f"unknown operator: '{token.value}'")
  except StopIteration:pass

def compile(code,stack=None):
  yield from compileTokens(tokenize(code),{},stack)


## execute code from generate
def interpretBF(code):
  memory=dict()
  mp=0
  codeBuffer=[] ## code since the first currently open bracket
  codeStack=[]
  ip=0
  skipDepth=0
  try:
    while 1:
      if ip<len(codeBuffer):
        op=codeBuffer[ip]
      else:
        op=next(code)
        codeBuffer.append(op)
      if skipDepth>0:
        if op=="[":
          skipDepth+=1
        elif op=="]":
          skipDepth-=1
      else:
        if op==">":
          mp+=1
        elif op=="<":
          mp-=1
        elif op=="+":
          prev=memory[mp] if mp in memory else 0
          memory[mp]=(prev+1)&255
        elif op=="-":
          prev=memory[mp] if mp in memory else 0
          memory[mp]=(prev-1)&255
        elif op==".":
          prev=memory[mp] if mp in memory else 0
          sys.stdout.buffer.write(bytes([prev&255])) ## write cell value modulo 256 to stdout
        elif op==",":
          ## TODO read from stdin
          memory[mp]=0
        elif op in "[":
          prev=memory[mp] if mp in memory else 0
          if prev!=0:
            codeStack.append(len(codeStack))
          else:
            skipDepth=1
        elif op in "]":
          prev=memory[mp] if mp in memory else 0
          if prev!=0:
            ip=codeStack[-1]
          else:
            codeStack.pop()
      if len(codeStack)==0:
        codeBuffer.clear()
      ip+=1
  except StopIteration:pass

def main():
  parser=argparse.ArgumentParser()
  parser.add_argument('-f', '--src')
  parser.add_argument('-o', '--out')
  parser.add_argument('-N', '--maxCount', type=int)
  parser.add_argument('-x', dest='execute',action='store_true')
  parser.add_argument('params', nargs='*')
  args=parser.parse_args()
  params=[Token(TOKEN_STRING,p) for p in reversed(args.params)]
  src=args.src
  if src is None:
    src="./test.mbf"
  with open(src, encoding="utf-8") as f:
    code = f.read()
  compiled=compile(code,[*params])
  if args.out is not None:
    N=args.maxCount
    if N is None:
      N=65536
    with open(args.out, encoding="utf-8", mode="w") as f:
      N0=N
      for c in compiled:
        if N<=0:
          print(f"Exceeded maximum allowed program length ({N0} characters) use the -N flag to increase the limit")
          break
        f.write(c)
        N-=1
    if args.execute: ## reset iterator if in execute mode
      compiled=compile(code,params)
  if args.execute:
    interpretBF(compiled)

if __name__ == "__main__":
  main()
