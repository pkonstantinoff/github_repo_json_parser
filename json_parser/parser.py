import ast
from functools import reduce

VALID_NODE_TYPES = (
    ast.Name,
    ast.Attribute,
    ast.Subscript,
)


def _parse(properties):
    """ Parse and validate a property string
    Parameters
        properties (string): string containing properties to parse
    Returns
        nodes(List): returns a list of ast nodes
    """
    if type(properties) != str:
        raise TypeError("Properties must be a string")
    try:
        nodes = ast.parse(properties).body
    except SyntaxError:
        raise SyntaxError("Properties must comply JSON's key rules")
    if not nodes or not isinstance(nodes[0], ast.Expr):
        raise ValueError(f"Invalid expression: {properties}")
    return reversed([node for node in ast.walk(nodes[0])
                    if isinstance(node, VALID_NODE_TYPES)])


def _lookup(obj, prop):
    """ Lookup a given property on the object.
    Parameters
        obj (Dict): A dict to lookup for properties or index
        prop (ast Node): An ast.Attribute, ast.Name, or ast.Subscript node to lookup
    Returns
        An object result of the lookup
    """
    if isinstance(prop, ast.Attribute):
        return obj.get(prop.attr)
    elif isinstance(prop, ast.Name):
        return obj.get(prop.id)
    elif isinstance(prop, ast.Subscript):
        return obj[_lookup_subscript(prop.slice.value)]

    raise NotImplementedError(f"Node is not supported: {prop}")


def _lookup_subscript(node):
    """ Lookup the subscript value of an ast node.
    Parameters
        node (ast node): An ast Node correspondingn object to lookup the attribute, index, or key
    Returns
        subscript index
    """
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Str):
        return node.s
    elif (isinstance(node, ast.UnaryOp)
          and isinstance(node.op, ast.USub)
          and isinstance(node.operand, ast.Num)):
        return -node.operand.n

    raise NotImplementedError("Node is not supported")


def get(obj, properties):
    """ A property getter that supports nested lookups in dicts, lists, and any combination in between.
    Parameters
        obj (Json): An object to lookup the attribute on
        properties (String): A property string to lookup
    Returns
        (string): The property retrieved
    """
    if not isinstance(obj, dict):
        return
    try:
        result = reduce(_lookup, _parse(properties), obj)
        if result == obj:
            return
    except Exception:
        return
    return result
