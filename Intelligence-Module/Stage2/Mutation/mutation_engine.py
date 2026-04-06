"""
Mutation Engine for Stage-2 (Layer 3)

Takes source code and generates N mutated versions using
operators from mutant_operators.py.

Each mutant has exactly ONE change from the original code.
This ensures that if a test detects the mutant (kills it),
we know exactly which code behavior that test validates.

Flow:
    1. Parse source code into AST
    2. Iterate ACTIVE_OPERATORS, collect all possible targets
    3. Sample up to MAX_MUTANTS if too many targets exist
    4. For each selected target, apply operator to get mutated AST
    5. Unparse mutated AST back to source code
    6. Validate mutant compiles
    7. Return list of valid mutant dicts

Output per mutant:
    {
        "id": int,
        "operator": str,
        "line": int,
        "description": str,
        "source_code": str (the mutated source)
    }

Current increment:
    - Python only (uses ast.parse / ast.unparse)
    - ast.unparse requires Python 3.9+

Future increment placeholders:
    - Multi-language support via external parsers
    - Equivalent mutant detection (skip mutants that don't change behavior)
    - Higher-order mutants (multiple mutations per mutant)
"""

import ast
import random

from Stage2.Mutation.mutant_operators import ACTIVE_OPERATORS


# Config — to be added to Stage2_Validation/config.py
# Maximum number of mutants to generate
# Caps cost: each mutant is executed against the full test suite
MAX_MUTANTS = 15

# If True, skip mutants that fail to compile
# Should always be True — invalid mutants waste execution time
VALIDATE_MUTANTS = True


class Mutation_Engine:
    def __init__(self, operators=None):
        """
        Args:
            operators: list of operator instances to use.
                       Defaults to ACTIVE_OPERATORS.
        """
        self.operators = operators or ACTIVE_OPERATORS

    def generate_mutants(self, source_code):
        """
        Generates mutated versions of the source code.

        Args:
            source_code: the original Python source code string

        Returns:
            list of mutant dicts, each with:
                id, operator, line, description, source_code
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            print(f"    [Mutation Engine] Failed to parse source: {e}")
            return []

        # collect all possible mutation targets across all operators
        all_targets = []

        for operator in self.operators:
            targets = operator.find_targets(tree)
            for target in targets:
                all_targets.append({
                    "operator": operator,
                    "target": target
                })

        if not all_targets:
            print("    [Mutation Engine] No mutation targets found")
            return []

        print(f"    [Mutation Engine] Found {len(all_targets)} possible mutations")

        # sample if too many targets
        if len(all_targets) > MAX_MUTANTS:
            selected = self.select_targets(all_targets)
        else:
            selected = all_targets

        # generate mutants
        mutants = []
        mutant_id = 0

        for entry in selected:
            operator = entry["operator"]
            target = entry["target"]

            mutant_tree = operator.apply(tree, target)

            if mutant_tree is None:
                continue

            # convert back to source code
            try:
                mutant_code = ast.unparse(mutant_tree)
            except Exception as e:
                print(f"    [Mutation Engine] Unparse failed: {e}")
                continue

            # validate compilation
            if VALIDATE_MUTANTS:
                if not self.validate_compiles(mutant_code):
                    continue

            description = operator.describe_mutation(target)

            mutants.append({
                "id": mutant_id,
                "operator": operator.name,
                "line": target.get("line"),
                "description": description,
                "source_code": mutant_code
            })

            mutant_id += 1

        print(f"    [Mutation Engine] Generated {len(mutants)} valid mutants")
        return mutants

    def select_targets(self, all_targets):
        """
        Selects up to MAX_MUTANTS targets from all possibilities.

        Strategy: proportional sampling across operators.
        Each operator gets a fair share of the budget so that
        mutants aren't dominated by one operator type
        (e.g., boundary_mutate on a file with many constants).

        If an operator has fewer targets than its share,
        the remaining budget redistributes to others.
        """
        # group by operator
        by_operator = {}
        for entry in all_targets:
            name = entry["operator"].name
            if name not in by_operator:
                by_operator[name] = []
            by_operator[name].append(entry)

        num_operators = len(by_operator)
        per_operator = MAX_MUTANTS // num_operators
        remainder = MAX_MUTANTS % num_operators

        selected = []
        leftover_budget = 0

        for name, targets in by_operator.items():
            budget = per_operator + (1 if remainder > 0 else 0)
            remainder = max(0, remainder - 1)
            budget += leftover_budget
            leftover_budget = 0

            if len(targets) <= budget:
                selected.extend(targets)
                leftover_budget = budget - len(targets)
            else:
                selected.extend(random.sample(targets, budget))

        return selected[:MAX_MUTANTS]

    def validate_compiles(self, source_code):
        """
        Checks that the mutated source code is valid Python.
        Uses compile() — same approach as Stage0_Compile.py for Python.
        """
        try:
            compile(source_code, "<mutant>", "exec")
            return True
        except SyntaxError:
            return False

    # ──────────────────────────────────────────────
    # Placeholders: Future Increment
    # ──────────────────────────────────────────────

    def detect_equivalent_mutants(self, original_code, mutant_code):
        """
        Future: Detect mutants that don't change observable behavior.
        Equivalent mutants waste execution time and inflate
        survival counts, making tests look weaker than they are.

        Approaches:
            - Constraint-based equivalence checking
            - Heuristic pattern matching (e.g., dead code mutations)
            - LLM-assisted equivalence judgment
        """
        # TODO: implement equivalence detection
        raise NotImplementedError

    def generate_higher_order_mutants(self, source_code, order=2):
        """
        Future: Combine multiple single mutations into one mutant.
        Higher-order mutants test whether the test suite detects
        subtle compound faults that single mutations miss.
        """
        # TODO: select N targets, apply all to same tree
        raise NotImplementedError

    def generate_mutants_multilang(self, source_code, language):
        """
        Future: Support C/CPP/Java mutation via external parsers.
            - C/CPP: pycparser or tree-sitter
            - Java: javalang or tree-sitter
        """
        # TODO: language-specific parser + unparser
        raise NotImplementedError