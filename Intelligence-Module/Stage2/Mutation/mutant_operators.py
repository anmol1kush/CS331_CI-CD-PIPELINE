"""
Mutant Operators for Stage-2 Mutation Testing (Layer 3)

Defines AST-level mutation operators that create single-point
mutations in Python source code.

Each operator is an ast.NodeTransformer subclass that:
    - Targets a specific node type
    - Applies one semantic change
    - Records what it changed and where

Current increment operators (LC/CP focused):
    - Relational swap:     <, <=, >, >=, ==, !=
    - Arithmetic swap:     +, -, *, /
    - Conditional negate:  if x → if not x
    - Boundary mutate:     constant ± 1
    - Return value mutate: return x → return None

Future increment placeholders (general feature commits):
    - Boolean logic swap:      and → or
    - Method call mutation:    list.append → list.remove
    - Argument swap:           func(a, b) → func(b, a)
    - Exception handler mutation: change/remove try-except
    - Assignment deletion:     remove assignment statements
    - Loop boundary mutation:  range(n) → range(n-1)
    - String/collection mutation: value → empty

Design:
    Each operator produces MULTIPLE possible mutations
    (one per applicable node in the AST).
    mutation_engine.py selects which ones to apply.

NOTE:
    Current increment supports Python only.
    C/CPP/Java operators deferred to future increment
    (requires language-specific parsers).
"""
import ast
import copy


class Base_Mutant_Operator:
    """
    Base class for all mutation operators.

    Subclasses must implement:
        - name: str
        - description: str
        - find_targets(tree): returns list of target dicts
        - apply(tree, target): returns mutated AST copy
        - describe_mutation(target): returns human-readable string
    """

    name = "base"
    description = "base operator"

    def find_targets(self, tree):
        raise NotImplementedError

    def apply(self, tree, target):
        raise NotImplementedError

    def describe_mutation(self, target):
        raise NotImplementedError


# Readable names for AST operator types
OP_NAMES = {
    ast.Lt: "<", ast.LtE: "<=",
    ast.Gt: ">", ast.GtE: ">=",
    ast.Eq: "==", ast.NotEq: "!=",
    ast.Add: "+", ast.Sub: "-",
    ast.Mult: "*", ast.Div: "/",
    ast.FloorDiv: "//", ast.Mod: "%",
}


# ──────────────────────────────────────────────
# Operator: Relational Swap
# ──────────────────────────────────────────────

RELATIONAL_SWAPS = {
    ast.Lt:    [ast.LtE, ast.Gt, ast.GtE],
    ast.LtE:   [ast.Lt, ast.Gt, ast.GtE],
    ast.Gt:    [ast.GtE, ast.Lt, ast.LtE],
    ast.GtE:   [ast.Gt, ast.Lt, ast.LtE],
    ast.Eq:    [ast.NotEq],
    ast.NotEq: [ast.Eq],
}


class Relational_Swap(Base_Mutant_Operator):

    name = "relational_swap"
    description = "Swaps relational comparison operators"

    def find_targets(self, tree):
        targets = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for i, op in enumerate(node.ops):
                    if type(op) in RELATIONAL_SWAPS:
                        for swap_to in RELATIONAL_SWAPS[type(op)]:
                            targets.append({
                                "node": node,
                                "op_index": i,
                                "original_op": type(op),
                                "mutated_op": swap_to,
                                "line": node.lineno
                            })

        return targets

    def apply(self, tree, target):
        mutant_tree = copy.deepcopy(tree)

        for node in ast.walk(mutant_tree):
            if isinstance(node, ast.Compare) and node.lineno == target["line"]:
                if target["op_index"] < len(node.ops):
                    if type(node.ops[target["op_index"]]) == target["original_op"]:
                        node.ops[target["op_index"]] = target["mutated_op"]()
                        return mutant_tree

        return None

    def describe_mutation(self, target):
        orig = OP_NAMES.get(target["original_op"], "?")
        mutated = OP_NAMES.get(target["mutated_op"], "?")
        return f"Line {target['line']}: Changed {orig} to {mutated}"


# ──────────────────────────────────────────────
# Operator: Arithmetic Swap
# ──────────────────────────────────────────────

ARITHMETIC_SWAPS = {
    ast.Add:      [ast.Sub],
    ast.Sub:      [ast.Add],
    ast.Mult:     [ast.Div],
    ast.Div:      [ast.Mult],
    ast.FloorDiv: [ast.Mod],
    ast.Mod:      [ast.FloorDiv],
}


class Arithmetic_Swap(Base_Mutant_Operator):

    name = "arithmetic_swap"
    description = "Swaps arithmetic operators in expressions"

    def find_targets(self, tree):
        targets = []

        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp):
                if type(node.op) in ARITHMETIC_SWAPS:
                    for swap_to in ARITHMETIC_SWAPS[type(node.op)]:
                        targets.append({
                            "node": node,
                            "original_op": type(node.op),
                            "mutated_op": swap_to,
                            "line": node.lineno
                        })

        return targets

    def apply(self, tree, target):
        mutant_tree = copy.deepcopy(tree)

        for node in ast.walk(mutant_tree):
            if isinstance(node, ast.BinOp) and node.lineno == target["line"]:
                if type(node.op) == target["original_op"]:
                    node.op = target["mutated_op"]()
                    return mutant_tree

        return None

    def describe_mutation(self, target):
        orig = OP_NAMES.get(target["original_op"], "?")
        mutated = OP_NAMES.get(target["mutated_op"], "?")
        return f"Line {target['line']}: Changed {orig} to {mutated}"


# ──────────────────────────────────────────────
# Operator: Conditional Negation
# ──────────────────────────────────────────────

class Conditional_Negate(Base_Mutant_Operator):

    name = "conditional_negate"
    description = "Negates if-statement conditions"

    def find_targets(self, tree):
        targets = []

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                targets.append({
                    "node": node,
                    "line": node.lineno
                })

        return targets

    def apply(self, tree, target):
        mutant_tree = copy.deepcopy(tree)

        for node in ast.walk(mutant_tree):
            if isinstance(node, ast.If) and node.lineno == target["line"]:
                node.test = ast.UnaryOp(
                    op=ast.Not(),
                    operand=node.test
                )
                ast.fix_missing_locations(mutant_tree)
                return mutant_tree

        return None

    def describe_mutation(self, target):
        return f"Line {target['line']}: Negated if-condition"


# ──────────────────────────────────────────────
# Operator: Boundary Mutation
# ──────────────────────────────────────────────

class Boundary_Mutate(Base_Mutant_Operator):

    name = "boundary_mutate"
    description = "Shifts integer constants by ±1"

    def find_targets(self, tree):
        targets = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, int):
                targets.append({
                    "node": node,
                    "original_value": node.value,
                    "mutated_value": node.value + 1,
                    "line": node.lineno
                })
                targets.append({
                    "node": node,
                    "original_value": node.value,
                    "mutated_value": node.value - 1,
                    "line": node.lineno
                })

        return targets

    def apply(self, tree, target):
        mutant_tree = copy.deepcopy(tree)

        for node in ast.walk(mutant_tree):
            if (isinstance(node, ast.Constant)
                    and isinstance(node.value, int)
                    and node.lineno == target["line"]
                    and node.value == target["original_value"]):
                node.value = target["mutated_value"]
                return mutant_tree

        return None

    def describe_mutation(self, target):
        return (
            f"Line {target['line']}: "
            f"Changed {target['original_value']} to {target['mutated_value']}"
        )


# ──────────────────────────────────────────────
# Operator: Return Value Mutation
# ──────────────────────────────────────────────

class Return_Mutate(Base_Mutant_Operator):

    name = "return_mutate"
    description = "Replaces return values with None"

    def find_targets(self, tree):
        targets = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Return) and node.value is not None:
                targets.append({
                    "node": node,
                    "line": node.lineno
                })

        return targets

    def apply(self, tree, target):
        mutant_tree = copy.deepcopy(tree)

        for node in ast.walk(mutant_tree):
            if isinstance(node, ast.Return) and node.lineno == target["line"]:
                if node.value is not None:
                    node.value = ast.Constant(value=None)
                    ast.fix_missing_locations(mutant_tree)
                    return mutant_tree

        return None

    def describe_mutation(self, target):
        return f"Line {target['line']}: Changed return value to None"


# ──────────────────────────────────────────────
# Placeholders: Future Increment Operators
# ──────────────────────────────────────────────

class Boolean_Logic_Swap(Base_Mutant_Operator):
    """and → or, or → and"""
    name = "boolean_logic_swap"
    description = "Swaps boolean operators (and ↔ or)"

    def find_targets(self, tree):
        # TODO: target ast.BoolOp nodes
        return []

    def apply(self, tree, target):
        raise NotImplementedError

    def describe_mutation(self, target):
        raise NotImplementedError


class Method_Call_Mutate(Base_Mutant_Operator):
    """list.append → list.remove, dict.get → dict.pop, etc."""
    name = "method_call_mutate"
    description = "Swaps method calls to semantically different alternatives"

    def find_targets(self, tree):
        # TODO: target ast.Call nodes with ast.Attribute func
        return []

    def apply(self, tree, target):
        raise NotImplementedError

    def describe_mutation(self, target):
        raise NotImplementedError


class Argument_Swap(Base_Mutant_Operator):
    """func(a, b) → func(b, a)"""
    name = "argument_swap"
    description = "Swaps argument order in function calls"

    def find_targets(self, tree):
        # TODO: target ast.Call nodes with 2+ args
        return []

    def apply(self, tree, target):
        raise NotImplementedError

    def describe_mutation(self, target):
        raise NotImplementedError


class Exception_Handler_Mutate(Base_Mutant_Operator):
    """Remove or change exception handlers"""
    name = "exception_handler_mutate"
    description = "Modifies or removes try-except blocks"

    def find_targets(self, tree):
        # TODO: target ast.ExceptHandler nodes
        return []

    def apply(self, tree, target):
        raise NotImplementedError

    def describe_mutation(self, target):
        raise NotImplementedError


class Assignment_Delete(Base_Mutant_Operator):
    """Remove assignment statements"""
    name = "assignment_delete"
    description = "Deletes assignment statements"

    def find_targets(self, tree):
        # TODO: target ast.Assign nodes
        return []

    def apply(self, tree, target):
        raise NotImplementedError

    def describe_mutation(self, target):
        raise NotImplementedError


class Loop_Boundary_Mutate(Base_Mutant_Operator):
    """range(n) → range(n-1), change loop termination"""
    name = "loop_boundary_mutate"
    description = "Modifies loop boundary conditions"

    def find_targets(self, tree):
        # TODO: target range() calls within ast.For nodes
        return []

    def apply(self, tree, target):
        raise NotImplementedError

    def describe_mutation(self, target):
        raise NotImplementedError


class Collection_Mutate(Base_Mutant_Operator):
    """Replace value with empty string/list/dict"""
    name = "collection_mutate"
    description = "Replaces values with empty collections"

    def find_targets(self, tree):
        # TODO: target ast.List, ast.Dict, ast.Constant(str) nodes
        return []

    def apply(self, tree, target):
        raise NotImplementedError

    def describe_mutation(self, target):
        raise NotImplementedError


# ──────────────────────────────────────────────
# Operator Registry
# ──────────────────────────────────────────────

# Active operators — used by mutation_engine in current increment
ACTIVE_OPERATORS = [
    Relational_Swap(),
    Arithmetic_Swap(),
    Conditional_Negate(),
    Boundary_Mutate(),
    Return_Mutate(),
]

# All operators including placeholders — for future increments
# Placeholder operators return empty target lists so they are safe
# to include but produce no mutations until implemented
ALL_OPERATORS = ACTIVE_OPERATORS + [
    Boolean_Logic_Swap(),
    Method_Call_Mutate(),
    Argument_Swap(),
    Exception_Handler_Mutate(),
    Assignment_Delete(),
    Loop_Boundary_Mutate(),
    Collection_Mutate(),
]