
BF_CHARS="+-<>[].,"
SPECIAL_CHARS="(){}:=&|!~*/%^?#$@\\',;"
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

def compileTokens(tokens,variables={},stack=[]):
  valueStack=[*stack]
  tokenBuffer=[]
  depth=0
  for token in tokens:
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
      for e in getItems(loopSrc,variables):
        yield from compileTokens(tokenBuffer,variables,[e])
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
    if token.value=="(":
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
      ## XXX string*int int*string -> string repetition
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
    
    # unused operators ^?$@\\',;
    ## XXX other operators: arithmetic operations, eval, join values to array
    raise Exception(f"unknown operator: '{token.value}'")

def compile(code):
  yield from compileTokens(tokenize(code),{})

## TODO execute code from generator, (only store reachable part of previous code)


