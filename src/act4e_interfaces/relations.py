from abc import ABC, abstractmethod
from typing import Generic

from .sets import E, E1, E2, E3, FiniteSet, Setoid

__all__ = [
    "Relation",
    "FiniteRelation",
    "FiniteRelationOperations",
    "FiniteRelationCompose",
    "FiniteRelationProperties",
    "FiniteEndorelationProperties",
    "FiniteEndorelationOperations",
]


class Relation(Generic[E1, E2], ABC):
    @abstractmethod
    def source(self) -> Setoid[E1]:
        """Returns a setoid"""

    @abstractmethod
    def target(self) -> Setoid[E2]:
        """Returns a setoid"""

    @abstractmethod
    def holds(self, e1: E1, e2: E2) -> bool:
        ...


class FiniteRelation(Generic[E1, E2], Relation[E1, E2], ABC):
    @abstractmethod
    def source(self) -> FiniteSet[E1]:
        """Returns a finite set"""

    @abstractmethod
    def target(self) -> FiniteSet[E2]:
        """Returns a finite set"""


class FiniteRelationProperties(ABC):
    @abstractmethod
    def is_surjective(self, fr: FiniteRelation[E1, E2]) -> bool:
        """Return True if the relation is surjective."""

    @abstractmethod
    def is_injective(self, fr: FiniteRelation[E1, E2]) -> bool:
        """Return True if the relation is injective."""

    @abstractmethod
    def is_defined_everywhere(self, fr: FiniteRelation[E1, E2]) -> bool:
        """Return True if the relation is defined everywhere."""

    @abstractmethod
    def is_single_valued(self, fr: FiniteRelation[E1, E2]) -> bool:
        """Return True if the relation is single-valued"""


class FiniteRelationCompose(ABC):
    @abstractmethod
    def compose(self, fr: FiniteRelation[E1, E2], fr2: FiniteRelation[E2, E3]) -> FiniteRelation[E1, E3]:
        """Compose two relations"""


class FiniteRelationOperations(ABC):
    @abstractmethod
    def transpose(self, fr: FiniteRelation[E1, E2]) -> FiniteRelation[E2, E1]:
        """Create the transposed of a relation"""


class FiniteEndorelationProperties(ABC):
    @abstractmethod
    def is_reflexive(self, fr: FiniteRelation[E, E]) -> bool:
        """Return True if the relation is reflexive."""

    @abstractmethod
    def is_irreflexive(self, fr: FiniteRelation[E, E]) -> bool:
        """Return True if the relation is irreflexive."""

    @abstractmethod
    def is_transitive(self, fr: FiniteRelation[E, E]) -> bool:
        """Return True if the relation is transitive."""

    @abstractmethod
    def is_symmetric(self, fr: FiniteRelation[E, E]) -> bool:
        """Return True if the relation is symmetric"""

    @abstractmethod
    def is_antisymmetric(self, fr: FiniteRelation[E, E]) -> bool:
        """Return True if the relation is antisymmetric"""

    @abstractmethod
    def is_asymmetric(self, fr: FiniteRelation[E, E]) -> bool:
        """Return True if the relation is asymmetric"""


class FiniteEndorelationOperations(ABC):
    @abstractmethod
    def transitive_closure(self, fr: FiniteRelation[E, E]) -> FiniteRelation[E, E]:
        """Returns the transitive closure of a relation"""
