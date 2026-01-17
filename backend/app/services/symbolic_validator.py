"""
Symbolic math validator using SymPy (no AI needed).
Validates algebraic steps by checking if expressions are mathematically equivalent.
"""

from sympy import sympify, simplify, Eq, solve, symbols
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from typing import List, Dict, Optional


class SymbolicValidator:
    """Validates math steps using symbolic computation (SymPy)."""
    
    def __init__(self):
        self.transformations = (standard_transformations + (implicit_multiplication_application,))
    
    def parse_expression(self, expr_str: str):
        """
        Parse a math expression string into SymPy format.
        Handles equations like "2x+5=13" and expressions like "2x+5".
        """
        try:
            # Clean up the string
            expr_str = expr_str.strip().replace(' ', '')
            
            # Convert ^ to ** for exponentiation
            expr_str = expr_str.replace('^', '**')
            
            # Check if it's an equation (contains =)
            if '=' in expr_str:
                left, right = expr_str.split('=', 1)
                left_expr = parse_expr(left, transformations=self.transformations)
                right_expr = parse_expr(right, transformations=self.transformations)
                return Eq(left_expr, right_expr)
            else:
                # Just an expression
                return parse_expr(expr_str, transformations=self.transformations)
        except Exception as e:
            raise ValueError(f"Could not parse '{expr_str}': {str(e)}")
    
    def detect_operation(self, prev: Eq, curr: Eq) -> Optional[str]:
        """
        Detect what algebraic operation was applied between two equations.
        Returns a string describing the operation or None if unclear.
        """
        try:
            # Check for addition/subtraction on both sides
            diff_left = simplify(curr.lhs - prev.lhs)
            diff_right = simplify(curr.rhs - prev.rhs)
            
            if simplify(diff_left - diff_right) == 0 and diff_left != 0:
                if diff_left > 0:
                    return f"added {diff_left} to both sides"
                else:
                    return f"subtracted {abs(diff_left)} from both sides"
            
            # Check for multiplication/division on both sides
            if prev.lhs != 0 and curr.lhs != 0:
                ratio_left = simplify(curr.lhs / prev.lhs)
                ratio_right = simplify(curr.rhs / prev.rhs)
                
                if simplify(ratio_left - ratio_right) == 0 and ratio_left != 1:
                    if ratio_left > 1:
                        return f"multiplied both sides by {ratio_left}"
                    else:
                        return f"divided both sides by {simplify(1/ratio_left)}"
            
            # Check if it's just simplification (same solution, different form)
            return "simplified"
            
        except:
            return None
    
    def is_simpler(self, prev: Eq, curr: Eq) -> bool:
        """Check if curr is simpler/more progressed than prev."""
        try:
            # Count terms and complexity
            prev_terms = len(str(prev.lhs)) + len(str(prev.rhs))
            curr_terms = len(str(curr.lhs)) + len(str(curr.rhs))
            
            # Simpler if fewer characters (rough heuristic)
            return curr_terms < prev_terms
        except:
            return False
    
    def validate_step(self, prev_expr: str, curr_expr: str) -> Dict:
        """
        Check if curr_expr is a valid algebraic step from prev_expr.
        
        Returns:
            {
                "is_valid": bool,
                "error": str or None,
                "explanation": str,
                "warning": str or None
            }
        """
        try:
            prev = self.parse_expression(prev_expr)
            curr = self.parse_expression(curr_expr)
            
            # If both are equations, check if they have the same solution set
            if isinstance(prev, Eq) and isinstance(curr, Eq):
                # Try to solve both equations and compare solutions
                try:
                    prev_solutions = solve(prev, dict=True)
                    curr_solutions = solve(curr, dict=True)
                    
                    # Check if solution sets are equal
                    if prev_solutions == curr_solutions or \
                       (len(prev_solutions) == 1 and len(curr_solutions) == 1 and 
                        all(simplify(prev_solutions[0][k] - curr_solutions[0][k]) == 0 
                            for k in prev_solutions[0].keys() if k in curr_solutions[0])):
                        
                        # Valid step - detect what operation was used
                        operation = self.detect_operation(prev, curr)
                        is_progress = self.is_simpler(prev, curr)
                        
                        warning = None
                        if not is_progress:
                            # Show warning for any step that doesn't make progress
                            if operation and operation != "simplified":
                                warning = f"Valid, but this makes the equation more complex ({operation})"
                            else:
                                warning = "Valid, but you could simplify further"
                        
                        explanation = "Valid algebraic step"
                        if operation:
                            explanation += f" ({operation})"
                        
                        return {
                            "is_valid": True,
                            "error": None,
                            "explanation": explanation,
                            "warning": warning
                        }
                    else:
                        # Get the actual solutions for better error message
                        prev_sol_str = ", ".join([f"{k}={v}" for sol in prev_solutions for k, v in sol.items()]) if prev_solutions else "no solution"
                        curr_sol_str = ", ".join([f"{k}={v}" for sol in curr_solutions for k, v in sol.items()]) if curr_solutions else "no solution"
                        
                        operation = self.detect_operation(prev, curr)
                        error_msg = "Incorrect transformation"
                        if operation:
                            error_msg += f" (attempted: {operation})"
                        error_msg += f": gives {curr_sol_str}, but should give {prev_sol_str}"
                        
                        return {
                            "is_valid": False,
                            "error": error_msg,
                            "explanation": "Double-check your arithmetic",
                            "warning": None
                        }
                except:
                    # If solve fails, fall back to checking equivalence
                    prev_diff = simplify(prev.lhs - prev.rhs)
                    curr_diff = simplify(curr.lhs - curr.rhs)
                    
                    if simplify(prev_diff - curr_diff) == 0:
                        return {
                            "is_valid": True,
                            "error": None,
                            "explanation": "Valid algebraic step",
                            "warning": None
                        }
                
                return {
                    "is_valid": False,
                    "error": "This step doesn't follow from the previous equation",
                    "explanation": "Check if you applied operations to both sides correctly",
                    "warning": None
                }
            else:
                # For non-equation expressions, check if they simplify to the same thing
                if simplify(prev - curr) == 0:
                    return {
                        "is_valid": True,
                        "error": None,
                        "explanation": "Expressions are equivalent",
                        "warning": None
                    }
                else:
                    return {
                        "is_valid": False,
                        "error": "These expressions don't have the same value",
                        "explanation": "Verify your simplification",
                        "warning": None
                    }
                    
        except ValueError as e:
            return {
                "is_valid": False,
                "error": str(e),
                "explanation": "Could not parse expression"
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Validation error: {str(e)}",
                "explanation": "Unexpected error during validation"
            }
    
    def validate_sequence(self, expressions: List[str]) -> List[Dict]:
        """
        Validate a sequence of math steps.
        
        Returns list of validation results, one for each step transition.
        Result at index i validates the step from expressions[i] to expressions[i+1].
        """
        if len(expressions) < 2:
            return []
        
        results = []
        for i in range(len(expressions) - 1):
            result = self.validate_step(expressions[i], expressions[i + 1])
            result["step_number"] = i + 1
            result["from_expr"] = expressions[i]
            result["to_expr"] = expressions[i + 1]
            results.append(result)
        
        return results


# Singleton instance
_validator_instance = None

def get_validator() -> SymbolicValidator:
    """Get the singleton validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = SymbolicValidator()
    return _validator_instance
