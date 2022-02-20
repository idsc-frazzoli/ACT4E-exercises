import traceback
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from io import StringIO
from typing import Any, Dict, Generic, List, Protocol, TypeVar

import ruamel.yaml as yaml
import zuper_html as zh
from ruamel.yaml import RoundTripLoader, YAML
from zuper_commons.types import add_context, ZValueError
from zuper_testint import ImplementationFail, TestContext

import act4e_interfaces as I
from . import logger

X = TypeVar("X")


@dataclass
class TestData(Generic[X]):
    tags: Dict[str, bool]
    requires: Dict[str, bool]
    data: X
    properties: Dict[str, Any]


ALLOWED_TAGS = {
    "poset",
    "set",
    "semigroup",
    "monoid",
    "group",
    "relation",
    "map",
    "dp",
    "category",
    "natural_transform",
}
ALLOWED_PROPERTIES = {
    "powerset",
    "some_antichains",
    "some_not_antichains",
    "some_chains",
    "some_not_chains",
    "surjective",
    "defined_everywhere",
    "single_valued",
    "injective",
    "reflexive",
    "irreflexive",
    "transitive",
    "asymmetric",
    "symmetric",
    "antisymmetric",
    "has_top",
    "height",
    "width",
    "has_bottom",
    "top",
    "opposite",
    "bottom",
    "lattice",
    "some_not_uppersets",
    "some_lowersets",
    "some_uppersets",
    "some_not_lowersets",
}
ALLOWED_REQUIRES = {
    "set_product",
    "poset_product",
    "set_union",
    "poset_sum",
}

import os

ENV_VAR = "ACT4E_DATA"


def find_yamls(dirnames: List[str]) -> List[str]:
    res = []
    for dirname in dirnames:
        for f in os.listdir(dirname):
            if f.endswith(".yaml"):
                res.append(os.path.join(dirname, f))
    return res


@lru_cache()
def get_all_test_data() -> Dict[str, TestData[Any]]:
    from_env = os.environ.get(ENV_VAR, None)
    if from_env:
        dirname = from_env
        logger.info(f"loading data from environment variable {ENV_VAR} = {dirname}")

    else:
        msg = (
            f"Using embedded data. You can use the environment variable {ENV_VAR} to give a different "
            f"directory. "
        )
        logger.info(msg)
        dirname = os.path.join(os.path.dirname(__file__), "thedata")

    yamls = find_yamls([dirname])

    res: Dict[str, TestData[Any]] = {}

    for fn in yamls:
        with open(fn) as f:
            data = f.read()

        d = yaml.load(data, Loader=RoundTripLoader)
        for k, v in d.items():

            if k in res:
                msg = f"Found duplicate key {k} in {fn}"
                raise ZValueError(msg)

            vv = dict(v)
            tags = vv.pop("tags", {})

            try:
                data = vv.pop("data")
            except KeyError:
                raise ZValueError(k=k, v=v)

            requires = vv.pop("requires", {})
            properties = vv.pop("properties", {})

            if vv:
                msg = "Unknown properties"
                raise ZValueError(msg=msg, v=v, vv=vv)

            extra_requires = set(requires) - set(ALLOWED_REQUIRES)
            if extra_requires:
                msg = f'Extra "requires" for entry {k!r}'
                raise ZValueError(msg, extra_requires=extra_requires, allowed=ALLOWED_REQUIRES)

            extra_properties = set(properties) - set(ALLOWED_PROPERTIES)
            if extra_properties:
                msg = "Extra properties"
                raise ZValueError(msg, extra_properties=extra_properties)

            extra_tags = set(tags) - set(ALLOWED_TAGS)
            if extra_tags:
                msg = "Extra tags"
                raise ZValueError(msg, extra_tags=extra_tags)

            res[k] = TestData(tags=tags, requires=requires, data=data, properties=properties)

    entries = {k: v.data for k, v in res.items()}
    for k, v in res.items():
        with add_context(k=k):
            res[k].data = substitute(entries, res[k].data)

    return res


def substitute(entries: Dict[str, object], a: object) -> object:
    if isinstance(a, dict):
        if "load" in a:
            loadit = a["load"]
            if loadit not in entries:
                msg = "Cannot find entry to load"
                raise ZValueError(msg, a=a)
            else:
                return entries[loadit]
        else:
            return {k: substitute(entries, v) for k, v in a.items()}

    elif isinstance(a, list):
        return [substitute(entries, x) for x in a]
    else:
        return a


def purify_data(a: X) -> X:
    """Strip comments etc."""
    loader = YAML()
    loader.indent(mapping=4, sequence=4, offset=2)
    loader.preserve_quotes = True  # type: ignore
    loader.default_flow_style = False
    i = StringIO()
    loader.dump(a, i)
    s = i.getvalue()
    res = yaml.load(s, Loader=yaml.Loader)
    return res


def get_test_relations() -> Dict[str, TestData[I.FiniteRelation_desc]]:
    return get_test_data("relation")


def get_test_posets() -> Dict[str, TestData[I.FinitePoset_desc]]:
    return get_test_data("poset")


def get_test_sets() -> Dict[str, TestData[I.FiniteSet_desc]]:
    return get_test_data("set")


def get_test_data(tagname: str) -> Dict[str, TestData[Any]]:
    alldata = get_all_test_data()
    res = {}
    for k, v in alldata.items():

        if v.tags.get(tagname, False):
            res[k] = v
    return res


class IOHelperImp(I.IOHelper):
    def loadfile(self, name: str) -> Dict[str, Any]:
        raise NotImplementedError(name)


Rcov = TypeVar("Rcov", covariant=True)
Rcon = TypeVar("Rcon", contravariant=True)

Xcov = TypeVar("Xcov", covariant=True)
Xcon = TypeVar("Xcon", contravariant=True)


class Loader(Protocol[Xcov, Rcon]):
    def load(self, h: I.IOHelper, data: Rcon) -> Xcov:
        ...


class Saver(Protocol[Xcon, Rcov]):
    def save(self, h: I.IOHelper, ob: Xcon) -> Rcov:
        ...


def dumpit_(tc: TestContext, fsr: Saver[Xcon, Rcov], h: I.IOHelper, ob: Xcon) -> Rcov:
    KN = type(fsr).__name__

    try:
        res = fsr.save(h, ob)
    except Exception as e:
        tc.fail(zh.span(f"{KN}:save() raised an exception"), tb=traceback.format_exc(), ob=ob)
        raise ImplementationFail() from e

    if res is None:
        tc.fail(zh.span(f"{KN}:save() returned None"), ob=ob)
        raise ImplementationFail()
    check_good_output(tc, res)
    tc.raise_if_failures()
    return res


def loadit_(tc: TestContext, loader: Loader[Xcov, Rcon], h: I.IOHelper, data: Rcon, K: type) -> Xcov:
    LN = type(loader).__name__
    try:
        res = loader.load(h, data)
    except NotImplementedError:
        raise
    except I.InvalidFormat as e:
        msg = f"Implementation of {LN}.load() threw InvalidFormat but the format is valid."
        tc.fail(zh.span(msg), data=yaml.dump(data), tb=traceback.format_exc())
        raise ImplementationFail() from e
    except BaseException as e:
        msg = f"Implementation of {LN}.load() threw {type(e).__name__} but the format is valid."
        tc.fail(zh.span(msg), data=yaml.dump(data), tb=traceback.format_exc())
        raise ImplementationFail() from e
    tc.expect_type2(res, K, zh.span(f"Expected that {LN}.load() returns a {K.__name__}"))
    tc.raise_if_failures()
    return res


def check_good_output(tc: TestContext, x: object) -> None:
    OK = (int, float, bool, datetime, dict, list, str)
    if isinstance(x, tuple):
        msg = (
            "You cannot use tuples for the concrete representation because they cannot be serialized in "
            "YAML. Try using lists. (You can use tuples for the internal representation.)"
        )
        tc.fail(zh.span(msg), x=x)
        return
    # noinspection PyTypeChecker
    if not isinstance(x, OK):
        msg = (
            f"In the concrete representation you can use only one of the usable datatypes; you used "
            f"an object of type {type(x).__name__}"
        )
        tc.fail(zh.span(msg), x=x)
        return  # raise ZValueError(msg)
    if isinstance(x, list):
        for _ in x:
            check_good_output(tc, _)
    if isinstance(x, dict):
        for k, v in x.items():
            check_good_output(tc, v)


def filter_reqs(d: Dict[str, TestData[X]], req: str) -> Dict[str, TestData[X]]:
    res = {}
    for k, v in d.items():
        requires = set(v.requires)
        if requires == {req}:
            res[k] = v

    return res
