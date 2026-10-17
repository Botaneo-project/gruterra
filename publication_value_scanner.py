"""Value-aware publication checks. No secret values are returned in diagnostics."""
import ast
import json
import re

NAMES = {'accesstoken','refreshtoken','clientsecret','apikey','authorization',
         'password','passwd','managementkey','privatekey','applicationid','accesstokenprotected',
         'token','secret','authtoken','bearertoken','apitoken','secretkey','privatekeyb64'}
def secret_name(name):
    return isinstance(name,str) and re.sub(r'[^a-z0-9]','',name.casefold()) in NAMES

def empty(value):
    return value is None or isinstance(value,str) and not value.strip()

STRONG = [
    re.compile(r'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}'),
    re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'bearer\s+[A-Za-z0-9._\-]{20,}',re.I),
]

def literal(node):
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
        left,right=literal(node.left),literal(node.right)
        if isinstance(left,str) and isinstance(right,str):return left+right
        raise ValueError('not a static string')
    return ast.literal_eval(node)

def scan(content,suffix):
    """Return fixed categories only; never values, lines of code or exceptions."""
    if any(pattern.search(content) for pattern in STRONG):return {'recognizable_secret'}
    found=set()
    def value(name,item):
        if secret_name(name) and not empty(item):found.add('filled_secret_field')
    def data(item):
        if isinstance(item,dict):
            for key,item_value in item.items():value(key,item_value);data(item_value)
        elif isinstance(item,list):
            for child in item:data(child)
    def node_value(name,node):
        try:value(name,literal(node))
        except (ValueError,TypeError,SyntaxError):pass
    if suffix=='.py':
        try:tree=ast.parse(content)
        except SyntaxError:return {'unreadable_python'}
        for node in ast.walk(tree):
            if isinstance(node,ast.Dict):
                for key,item in zip(node.keys,node.values):
                    if isinstance(key,ast.Constant):node_value(key.value,item)
            elif isinstance(node,(ast.Assign,ast.AnnAssign)):
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                if node.value is None:continue
                for target in targets:
                    if isinstance(target,ast.Name):node_value(target.id,node.value)
                    elif isinstance(target,ast.Subscript) and isinstance(target.slice,ast.Constant):node_value(target.slice.value,node.value)
            elif isinstance(node,ast.keyword):node_value(node.arg,node.value)
            elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                positional=node.args.posonlyargs+node.args.args
                for argument,default in zip(positional[-len(node.args.defaults):],node.args.defaults):
                    node_value(argument.arg,default)
                for argument,default in zip(node.args.kwonlyargs,node.args.kw_defaults):
                    if default is not None:node_value(argument.arg,default)
            elif isinstance(node,ast.Constant) and isinstance(node.value,str):
                # Embedded JSON is data too; normal field-name strings are harmless.
                try:data(json.loads(node.value))
                except (ValueError,TypeError):pass
        return found
    if suffix in ('.json','.example'):
        try:data(json.loads(content));return found
        except ValueError:
            if suffix=='.json':return {'unreadable_json'}
    # Documentation, shell examples, YAML/INI and assignments outside Python.
    names=r'access[_-]?token(?:[_-]?protected)?|refresh[_-]?token|client[_-]?secret|api[_-]?key|authorization|password|passwd|management[_-]?key|private[_-]?key(?:[_-]?b64)?|application[_-]?id|token|secret|auth[_-]?token|bearer[_-]?token|api[_-]?token|secret[_-]?key'
    quoted=re.compile(r'''(?i)(?<![\w])(?:["']?)(?:'''+names+r''')(?:["']?)[ \t]*[:=][ \t]*(["'])(.*?)\1''')
    for match in quoted.finditer(content):
        if match.group(2).strip():found.add('filled_secret_field')
    lines=re.compile(r'(?im)^[ \t]*(?:export[ \t]+)?(?:'+names+r')[ \t]*=[ \t]*([^\r\n]*)')
    for match in lines.finditer(content):
        if match.group(1).strip().strip('"\'').strip():found.add('filled_secret_field')
    return found
