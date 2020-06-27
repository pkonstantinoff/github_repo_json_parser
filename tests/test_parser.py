import pytest
import ast
import json
from functools import reduce
from github_repo_json_parser.json_parser import parser


@pytest.mark.parametrize('properties,param_types', [
    ('pro.array[0].inner', [ast.Name, ast.Attribute, ast.Subscript, ast.Attribute]),
    ('prop[2][0]', [ast.Name, ast.Subscript, ast.Subscript]),
])
def test_parse(properties, param_types):
    nodes = parser._parse(properties)
    for node, type_ in zip(nodes, param_types):
        assert isinstance(node, type_)


def test_parse_error():
    properties = "@@@"
    with pytest.raises(SyntaxError) as err:
        parser._parse(properties)
    assert "Properties must comply JSON's key rules" in str(err)

    properties = ""
    with pytest.raises(ValueError) as err:
        parser._parse(properties)
    assert f"Invalid expression: {properties}" in str(err)

    properties = 1
    with pytest.raises(TypeError) as err:
        parser._parse(properties)
    assert "Properties must be a string" in str(err)


@pytest.mark.parametrize('properties,obj,result', [
    ("prop.array[0].inner", '{"prop": {"array": [{"inner": "value"}, 2]}}', "value"),
    ("prop.inner.array[2]", '{"prop": {"inner": {"array": [1,2,3,4]}}}', 3),
])
def test_lookup(properties, obj, result):
    props = parser._parse(properties)
    object_ = json.loads(obj)
    for prop in props:
        object_ = parser._lookup(object_, prop)
    assert result == object_


def test_lookup_node_not_supported_error():
    prop = "prop.inner.array[2]"
    obj = '{"prop": {"inner": {"array": [1,2,3,4]}}}'
    object_ = json.loads(obj)
    with pytest.raises(NotImplementedError) as err:
        object_ = parser._lookup(object_, prop)
    assert "Node is not supported" in str(err)


def test_lookup_property_error():
    obj = '{"prop": {"inner": {"array": [1,2,3,4]}}}'
    object_ = json.loads(obj)

    prop = "prop.inner.array[8]"
    with pytest.raises(IndexError) as err:
        reduce(parser._lookup, parser._parse(prop), object_)
    assert "list index out of range" in str(err)

    prop = "prop_inner.array"
    with pytest.raises(AttributeError) as err:
        reduce(parser._lookup, parser._parse(prop), object_)
    assert "object has no attribute" in str(err)


@pytest.mark.parametrize('properties,obj,result', [
    ('prop["array"]', '{"prop": {"array": [{"inner": "value"}, 2]}}', [{"inner": "value"}, 2]),
    ("prop.inner.array[2]", '{"prop": {"inner": {"array": [1,2,3,4]}}}', 3),
    ("prop.inner.array[-1]", '{"prop": {"inner": {"array": [1,2,3,4]}}}', 4),
])
def test_lookup_subscript(properties, obj, result):
    object_ = json.loads(obj)
    result_ = reduce(parser._lookup, parser._parse(properties), object_)
    assert result_ == result


def test_lookup_subscript_error():
    obj = '{"prop": {"inner": {"array": [1,2,3,4]}}}'
    object_ = json.loads(obj)

    prop = 'prop[+1]'
    with pytest.raises(NotImplementedError) as err:
        object_ = reduce(parser._lookup, parser._parse(prop), object_)
    assert "Node is not supported" in str(err)


@pytest.mark.parametrize('properties,obj,result', [
    ('', '{"prop": {"array": [{"inner": "value"}, 2]}}', None),
    ("prop.inner.array[8]", '{"prop": {"inner": {"array": [1,2,3,4]}}}', None),
    ("prop.inner2.array[-1]", '{"prop": {"inner": {"array": [1,2,3,4]}}}', None),
    ("prop.inner.array[-1]", '{"prop": {"inner": {"array": [1,2,3,4]}}}', 4),
])
def test_get(properties, obj, result):
    obj = '{"prop": {"inner": {"array": [1,2,3,4]}}}'
    object_ = json.loads(obj)

    result_ = parser.get(object_, properties)
    assert result_ == result
